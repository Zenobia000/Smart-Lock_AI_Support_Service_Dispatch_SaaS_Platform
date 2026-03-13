import asyncio
from langchain_core.tools import StructuredTool
from core.config import DB_CONFIG, SYSTEM_CONFIG, USER_PROFILE_CONFIG, PROMPTS_CONFIG
from core.constants import PHONE_REGEX, ADDRESS_REGEX
from retrievers import get_retriever
from profiles import ProfileManager
from agents import load_prompt_template

profile_manager = ProfileManager(USER_PROFILE_CONFIG)


def _build_retriever_tool(db_config: dict) -> StructuredTool:
    """將單一 retriever 包裝為 LangChain StructuredTool"""
    name = db_config["name"]
    description = db_config.get("description", name)
    retriever_instance = get_retriever(db_config)

    async def _aretrieve(query: str) -> str:
        """根據使用者問題檢索相關資料。參數 query: 使用者的問題或關鍵字"""
        print(f"  [Tool 呼叫] {name}: 正在檢索 '{query}'...")
        result = await retriever_instance.aretrieve(query)
        print(f"  [Tool 結果] {name}: 回傳 {len(result)} 字元")
        return result

    def _retrieve_sync(query: str) -> str:
        return asyncio.run(_aretrieve(query))

    return StructuredTool.from_function(
        func=_retrieve_sync,
        coroutine=_aretrieve,
        name=name,
        description=f"搜尋「{description}」資料庫。當使用者的問題與「{description}」相關時使用此工具。",
    )


def _build_transfer_to_human_tool() -> StructuredTool:
    """建立轉接真人客服的工具"""

    async def _transfer(user_id: str = "anonymous") -> str:
        """當使用者明確堅持要求轉接真人客服，或涉及安全風險時，呼叫此工具。參數 user_id: 使用者 ID"""
        print(f"  [Tool 呼叫] transfer_to_human: user_id={user_id}")

        user_profile = await profile_manager.load_profile(user_id)

        phone = ""
        address = ""
        brand_model = ""
        if user_profile:
            phone_match = PHONE_REGEX.search(user_profile)
            if phone_match:
                phone = phone_match.group()
            addr_match = ADDRESS_REGEX.search(user_profile)
            if addr_match:
                address = addr_match.group().strip()

        has_info = any([brand_model, phone, address])
        header = "您好\n麻煩您確認並補充以下資訊" if has_info else "您好\n麻煩您留下以下資訊"

        transfer_form_path = PROMPTS_CONFIG.get("transfer_form", "agents/prompts/transfer_human_form.md")
        answer = load_prompt_template(
            transfer_form_path,
            header=header, address=address, phone=phone, brand_model=brand_model,
        )
        return answer

    def _transfer_sync(user_id: str = "anonymous") -> str:
        return asyncio.run(_transfer(user_id))

    return StructuredTool.from_function(
        func=_transfer_sync,
        coroutine=_transfer,
        name="transfer_to_human",
        description="轉接真人客服。僅在以下情況使用：(1) 使用者明確堅持要求轉接真人客服 (2) 涉及安全風險（門鎖無法上鎖、疑似被破壞）。不要因為資料不足就轉接，應先嘗試提供通用建議。",
    )


def build_tools() -> dict[str, StructuredTool]:
    """根據 config.toml 建立所有工具，回傳 dict 方便 agent 按名稱取用"""
    tools = {}

    for db_config in DB_CONFIG:
        tool = _build_retriever_tool(db_config)
        tools[tool.name] = tool
        print(f"[*] 已註冊工具: {tool.name} — {db_config.get('description', '')}")

    transfer_tool = _build_transfer_to_human_tool()
    tools[transfer_tool.name] = transfer_tool
    print(f"[*] 已註冊工具: transfer_to_human — 轉接真人客服")

    return tools
