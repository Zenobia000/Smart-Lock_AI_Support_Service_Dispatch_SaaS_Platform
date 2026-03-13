import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, Query, Header
from typing import Optional

app = FastAPI(title="Mock Order API")

# 模擬訂單資料庫
MOCK_ORDERS = {
    "SN-20240501": {
        "order_id": "SN-20240501",
        "customer": "王先生",
        "product": "Philips Alpha 指紋電子鎖",
        "status": "已出貨",
        "logistics": "黑貓宅急便",
        "tracking_no": "TC-88776655",
        "estimated_delivery": "2024 年 5 月 3 日下午",
        "note": "商品已於 5/1 從台北倉庫出貨"
    },
    "SN-20240412": {
        "order_id": "SN-20240412",
        "customer": "李小姐",
        "product": "Samsung SHP-DP609 推拉式電子鎖",
        "status": "處理中",
        "logistics": "",
        "tracking_no": "",
        "estimated_delivery": "預計 3~5 個工作天內出貨",
        "note": "訂單已確認付款，等待倉庫揀貨"
    },
    "SN-20240320": {
        "order_id": "SN-20240320",
        "customer": "張先生",
        "product": "Yale YDM-7116A 觸控指紋鎖",
        "status": "已完成",
        "logistics": "新竹物流",
        "tracking_no": "HCT-12345678",
        "estimated_delivery": "已送達",
        "note": "已於 3/22 簽收完成"
    },
    "ORD-20260301": {
        "order_id": "ORD-20260301",
        "customer": "測試用戶",
        "product": "Philips Alpha 指紋電子鎖",
        "status": "已出貨",
        "logistics": "黑貓宅急便",
        "tracking_no": "TC-20260302-001",
        "estimated_delivery": "2026 年 3 月 4 日下午",
        "note": "商品已於 3/2 從台北倉庫出貨"
    },
    "ORD-20260215": {
        "order_id": "ORD-20260215",
        "customer": "測試用戶",
        "product": "Samsung SHP-DP609 推拉式電子鎖 x2",
        "status": "部分出貨",
        "logistics": "新竹物流",
        "tracking_no": "HCT-20260220-088",
        "estimated_delivery": "第一台已送達；第二台預計 3~5 個工作天內出貨",
        "note": "第一台已於 2/20 簽收完成，第二台備貨中預計近日出貨"
    },
}

# 模擬維修單資料庫
MOCK_REPAIRS = {
    "R-9988": {
        "repair_id": "R-9988",
        "customer": "陳先生",
        "product": "Philips Alpha 指紋電子鎖",
        "issue": "馬達異常，無法正常開鎖",
        "status": "已派工",
        "technician": "林工程師",
        "scheduled_time": "今日下午 14:00 電話聯繫",
        "note": "工程師將先電話確認狀況，再安排到府時間"
    },
    "R-10023": {
        "repair_id": "R-10023",
        "customer": "黃小姐",
        "product": "Samsung SHP-DP609",
        "issue": "指紋感應器故障",
        "status": "維修中",
        "technician": "王工程師",
        "scheduled_time": "",
        "note": "商品已寄回原廠，預計 7~10 個工作天修復完成並寄回"
    },
    "R-10050": {
        "repair_id": "R-10050",
        "customer": "劉先生",
        "product": "Yale YDM-7116A",
        "issue": "觸控面板無反應",
        "status": "維修完成",
        "technician": "林工程師",
        "scheduled_time": "",
        "note": "已更換觸控模組，商品已於昨日寄出，預計後天到貨"
    },
}


def search_orders(keyword: str) -> str:
    """搜尋訂單"""
    results = []
    for order_id, order in MOCK_ORDERS.items():
        if (keyword in order_id or order_id in keyword
                or keyword in order["customer"] or order["customer"] in keyword
                or keyword in order["product"] or order["product"] in keyword):
            if order["status"] == "已出貨":
                results.append(
                    f"訂單編號：{order['order_id']}\n"
                    f"商品：{order['product']}\n"
                    f"狀態：{order['status']}\n"
                    f"物流：{order['logistics']}（追蹤碼：{order['tracking_no']}）\n"
                    f"預計到貨：{order['estimated_delivery']}\n"
                    f"備註：{order['note']}"
                )
            elif order["status"] in ("處理中", "部分出貨"):
                results.append(
                    f"訂單編號：{order['order_id']}\n"
                    f"商品：{order['product']}\n"
                    f"狀態：{order['status']}\n"
                    f"物流：{order['logistics']}（追蹤碼：{order['tracking_no']}）\n"
                    f"預計出貨時間：{order['estimated_delivery']}\n"
                    f"備註：{order['note']}"
                )
            else:
                results.append(
                    f"訂單編號：{order['order_id']}\n"
                    f"商品：{order['product']}\n"
                    f"狀態：{order['status']}\n"
                    f"備註：{order['note']}"
                )
    return "\n---\n".join(results) if results else ""


def search_repairs(keyword: str) -> str:
    """搜尋維修單"""
    results = []
    for repair_id, repair in MOCK_REPAIRS.items():
        if (keyword in repair_id or repair_id in keyword
                or keyword in repair["customer"] or repair["customer"] in keyword
                or keyword in repair["product"] or repair["product"] in keyword
                or keyword in repair["issue"] or repair["issue"] in keyword):
            results.append(
                f"維修單號：{repair['repair_id']}\n"
                f"商品：{repair['product']}\n"
                f"問題描述：{repair['issue']}\n"
                f"狀態：{repair['status']}\n"
                f"負責人：{repair['technician']}\n"
                f"{'預約時間：' + repair['scheduled_time'] if repair['scheduled_time'] else ''}\n"
                f"備註：{repair['note']}"
            )
    return "\n---\n".join(results) if results else ""


@app.get("/v1/status")
async def get_status(
    keyword: str = Query(..., description="使用者的查詢關鍵字"),
    authorization: Optional[str] = Header(None)
):
    print(f"\n[Mock API 收到請求] 關鍵字: {keyword}")
    if authorization:
        print(f"  └ 收到驗證碼: {authorization}")
    else:
        print("  └ (沒有收到驗證碼)")

    # 搜尋訂單與維修單
    order_result = search_orders(keyword)
    repair_result = search_repairs(keyword)

    parts = []
    if order_result:
        parts.append(f"【訂單查詢結果】\n{order_result}")
    if repair_result:
        parts.append(f"【維修進度查詢結果】\n{repair_result}")

    if parts:
        fake_result = "\n\n".join(parts)
    elif "訂單" in keyword:
        fake_result = "在訂單系統中查無相關資訊。請提供您的訂單編號（格式如 ORD-XXXXXXXX 或 SN-XXXXXXXX）以便查詢。"
    elif "維修" in keyword:
        fake_result = "在維修系統中查無相關資訊。請提供您的維修單號（格式如 R-XXXX）以便查詢。"
    else:
        fake_result = "查無相關資訊。請提供訂單編號（ORD-XXXXXXXX 或 SN-XXXXXXXX）或維修單號（R-XXXX）以便查詢。"

    return {
        "status": "success",
        "message": fake_result
    }
