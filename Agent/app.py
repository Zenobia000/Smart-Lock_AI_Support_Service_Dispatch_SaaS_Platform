import os
import time
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException

# 引入 Line Bot SDK v3 相關套件
from linebot.v3 import WebhookParser
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    AsyncApiClient,
    AsyncMessagingApi,
    Configuration,
    ReplyMessageRequest,
    PushMessageRequest,
    TextMessage,
    ShowLoadingAnimationRequest,
    ApiException
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from core.config import LINE_BOT_CONFIG, TEMPLATES_CONFIG, DEBOUNCE_CONFIG, SYSTEM_CONFIG, STORAGE_CONFIG

from graph.builder import build_graph
from storage import get_storage, close_storage
from memory import close_checkpointer

# 載入環境變數 (.env)
load_dotenv()
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

app = FastAPI()

# 設定 Line 的 Parser 與非同步 API 客戶端
parser = WebhookParser(LINE_CHANNEL_SECRET)
configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)

# 訊息緩衝池：用來記錄每個使用者的狀態
user_buffers = {}

# 從 config 讀取設定（去硬編碼）
LANGGRAPH_TIMEOUT = SYSTEM_CONFIG.get("request_timeout", 60)
BUFFER_TTL_SECONDS = DEBOUNCE_CONFIG.get("buffer_ttl", 300)
BUFFER_CLEANUP_INTERVAL = DEBOUNCE_CONFIG.get("cleanup_interval", 60)

# LangGraph app 與審計日誌（在 startup 事件中非同步初始化）
langgraph_app = None
audit_storage = None

async def run_langgraph(user_id: str, user_text: str) -> tuple[str, list]:
    """將使用者訊息送入 LangGraph，並利用 user_id 維持對話記憶"""
    try:
        # 1. 設定對話的 Thread ID（固定格式，SQLite 持久化）
        thread_prefix = SYSTEM_CONFIG.get("thread_prefix", "smart_lock_")
        thread_id = f"{thread_prefix}{user_id}"
        config = {
            "configurable": {
                "thread_id": thread_id,
                "user_id": user_id       # profile 用原始 user_id
            }
        }

        # 2. 建立輸入狀態
        inputs = {
            "question": user_text
        }

        # 3. 記錄執行前的 history 長度，用於區分本次 run 新增的 history items
        prev_state = await langgraph_app.aget_state(config)
        prev_history_len = len(prev_state.values.get("history", [])) if prev_state.values else 0

        # 4. 使用非同步呼叫 (ainvoke) 執行圖表，加上 timeout 防止永遠 hang
        print(f"[LangGraph] 開始思考 user_id: {user_id} 的問題...")
        try:
            result_state = await asyncio.wait_for(
                langgraph_app.ainvoke(inputs, config=config),
                timeout=LANGGRAPH_TIMEOUT
            )
        except asyncio.TimeoutError:
            print(f"[LangGraph 超時] {user_id} 的問題處理超過 {LANGGRAPH_TIMEOUT} 秒")
            return TEMPLATES_CONFIG.get("error_timeout", "不好意思，系統處理時間過長，請稍後再試一次。如果問題持續，建議轉接真人客服。"), []

        # 5. 取出 answer，並只回傳本次 run 新增的 history items
        final_answer = result_state.get("answer", TEMPLATES_CONFIG.get("error_no_reply", "抱歉，系統沒有產生回覆。"))
        full_history = result_state.get("history", [])
        current_history = full_history[prev_history_len:]
        return final_answer, current_history

    except Exception as e:
        print(f"[LangGraph 執行錯誤] {e}")
        return TEMPLATES_CONFIG.get("error_system", "不好意思，系統大腦剛剛稍微當機了一下，請稍後再試一次！"), []

async def send_line_message(user_id: str, reply_token: str, message_text: str):
    """嘗試 Reply API，失敗則降級 Push API"""
    async with AsyncApiClient(configuration) as api_client:
        line_bot_api = AsyncMessagingApi(api_client)
        try:
            print("[Reply] 嘗試使用 Reply API 回覆...")
            await line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=[TextMessage(text=message_text)]
                )
            )
            print("[Reply] 成功！(免費)")
        except ApiException as e:
            print(f"[Reply] 失敗 (Token可能已失效): {e.status} - 準備降級使用 Push API")
            fallback_prefix = TEMPLATES_CONFIG.get("push_fallback_prefix", "【系統通知】讓您久等了，以下是您的回覆：\n")
            print("[Push] 嘗試使用 Push API 推播...")
            await line_bot_api.push_message(
                PushMessageRequest(
                    to=user_id,
                    messages=[TextMessage(text=fallback_prefix + message_text)]
                )
            )
            print("[Push] 成功！(花費額度)")


async def langgraph_and_reply(user_id: str, reply_token: str, text: str):
    """執行 LangGraph 並回覆使用者"""
    print(f"\n[開始處理] 準備將 '{text}' 送入 LangGraph...")

    # 審計日誌：記錄使用者原始訊息
    if audit_storage:
        try:
            await audit_storage.log_message(user_id, "user", text)
        except Exception as e:
            print(f"[Audit] 記錄使用者訊息失敗: {e}")

    ai_response, history = await run_langgraph(user_id, text)
    print(f"[LangGraph] 思考完畢！準備回傳...")

    # 審計日誌：記錄 AI 回覆
    if audit_storage:
        try:
            await audit_storage.log_message(user_id, "ai", ai_response)
        except Exception as e:
            print(f"[Audit] 記錄 AI 回覆失敗: {e}")

    await send_line_message(user_id, reply_token, ai_response)


async def process_and_reply(user_id: str, reply_token: str):
    """背景執行：等待緩衝 -> 執行 LangGraph -> 嘗試 Reply -> 失敗則 Push"""
    try:
        await asyncio.sleep(DEBOUNCE_CONFIG.get("buffer_wait", 1.5))
        combined_text = "\n".join(user_buffers[user_id]["text"])
        await langgraph_and_reply(user_id, reply_token, combined_text)

    except asyncio.CancelledError:
        print(f" ⏳ [任務取消] {user_id} 仍在輸入，更新計時器...")
        raise

    finally:
        if user_id in user_buffers and user_buffers[user_id].get("task") == asyncio.current_task():
            del user_buffers[user_id]


async def cleanup_stale_buffers():
    """定期清理過期的使用者緩衝區"""
    while True:
        await asyncio.sleep(BUFFER_CLEANUP_INTERVAL)
        now = time.monotonic()
        stale_users = [
            uid for uid, buf in user_buffers.items()
            if now - buf.get("created_at", 0) > BUFFER_TTL_SECONDS
        ]
        for uid in stale_users:
            buf = user_buffers.pop(uid, None)
            if buf:
                task = buf.get("task")
                if task and not task.done():
                    task.cancel()
                print(f"  [Buffer 清理] 移除 {uid} 的過期緩衝")

@app.on_event("startup")
async def startup_event():
    global langgraph_app, audit_storage
    audit_storage = await get_storage(STORAGE_CONFIG)
    langgraph_app = await build_graph()
    asyncio.create_task(cleanup_stale_buffers())

@app.on_event("shutdown")
async def shutdown_event():
    await close_storage()
    await close_checkpointer()

@app.post("/webhook")
async def line_webhook(request: Request):
    """接收 Line 官方傳來的 Webhook"""
    signature = request.headers.get('X-Line-Signature', '')
    body = await request.body()
    body_str = body.decode('utf-8')

    try:
        events = parser.parse(body_str, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature. Check your channel secret.")

    for event in events:
        # 我們目前只處理文字訊息
        if not isinstance(event, MessageEvent) or not isinstance(event.message, TextMessageContent):
            continue

        user_id = event.source.user_id
        new_text = event.message.text
        new_token = event.reply_token

        print(f"[收到訊息] '{new_text}' (Token: {new_token})")

        # 審計日誌：即時記錄使用者原始訊息（debounce 之前）
        if audit_storage:
            try:
                await audit_storage.log_message(user_id, "user_raw", new_text)
            except Exception as e:
                print(f"[Audit] 記錄原始訊息失敗: {e}")

        loading_time = LINE_BOT_CONFIG.get("loading_animation_time", 5)
        async with AsyncApiClient(configuration) as api_client:
            line_bot_api = AsyncMessagingApi(api_client)
            try:
                await line_bot_api.show_loading_animation(
                    ShowLoadingAnimationRequest(chatId=user_id, loadingSeconds=loading_time)
                )
            except Exception as e:
                print(f"[Warning] 顯示 Loading 動畫失敗: {e}")

        # 緩衝邏輯：新訊息重設計時器
        if user_id in user_buffers:
            user_buffers[user_id]["task"].cancel()
            user_buffers[user_id]["text"].append(new_text)
            user_buffers[user_id]["reply_token"] = new_token
            user_buffers[user_id]["created_at"] = time.monotonic()
        else:
            user_buffers[user_id] = {
                "text": [new_text],
                "reply_token": new_token,
                "created_at": time.monotonic()
            }

        new_task = asyncio.create_task(
            process_and_reply(user_id, user_buffers[user_id]["reply_token"])
        )
        user_buffers[user_id]["task"] = new_task

    return "OK"
