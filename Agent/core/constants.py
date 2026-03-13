import re
from core.config import EXTRACTION_CONFIG

PHONE_REGEX = re.compile(
    EXTRACTION_CONFIG.get("phone_regex", r'09\d{2}[\-\s]?\d{3}[\-\s]?\d{3}')
)
ADDRESS_REGEX = re.compile(
    EXTRACTION_CONFIG.get("address_regex",
        r'[\u4e00-\u9fff]*(?:市|縣)[\u4e00-\u9fff]*(?:區|鄉|鎮|市)'
        r'[\u4e00-\u9fff\d\s\-]*(?:路|街|巷|弄|號|樓)[\u4e00-\u9fff\d\s\-]*'
    )
)
