import operator
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages


def _keep_last(left, right):
    """Reducer：平行分支合併時保留最後寫入的值（同值時無影響）"""
    return right if right is not None else left


class GraphState(TypedDict):
    messages: Annotated[list, add_messages]   # Agent 對話歷史（LLM + Tool messages）
    question: Annotated[str, _keep_last]      # 原始使用者輸入
    user_profile: Annotated[str, _keep_last]  # 使用者輪廓
    answer: Annotated[str, _keep_last]        # 最終回覆（給 app.py 讀取）
    history: Annotated[list, operator.add]      # 路徑追蹤（除錯用）
    summary: Annotated[str, _keep_last]           # 對話摘要（記憶體管理用）
    next_agents: Annotated[list, _keep_last]    # 多 agent 派發清單
