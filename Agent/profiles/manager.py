import asyncio
import re
from pathlib import Path


class ProfileManager:
    def __init__(self, config: dict):
        self.enabled = config.get("enabled", False)
        self.base_dir = Path(config.get("profile_dir", "./data/profiles"))
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_profile_path(self, user_id: str) -> Path:
        safe_name = re.sub(r'[^\w\-]', '_', user_id)
        return self.base_dir / f"{safe_name}.md"

    async def load_profile(self, user_id: str) -> str:
        if not self.enabled:
            return ""
        path = self._get_profile_path(user_id)

        def _read():
            if path.exists():
                return path.read_text(encoding="utf-8")
            return ""

        return await asyncio.to_thread(_read)

    async def save_profile(self, user_id: str, content: str) -> None:
        if not self.enabled:
            return
        path = self._get_profile_path(user_id)

        def _write():
            path.write_text(content, encoding="utf-8")

        await asyncio.to_thread(_write)
