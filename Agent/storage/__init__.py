from .sqlite_impl import build_sqlite_storage, close_sqlite_storage
from .postgres_impl import build_postgres_storage

STORAGE_REGISTRY = {
    "sqlite": build_sqlite_storage,
    "postgres": build_postgres_storage,
}

_storage_instance = None


async def get_storage(config: dict):
    global _storage_instance
    storage_type = config.get("type", "sqlite")
    print(f"[*] 初始化審計日誌模組: 使用 {storage_type} 機制...")

    builder = STORAGE_REGISTRY.get(storage_type)
    if not builder:
        raise ValueError(f"不支援的審計日誌類型: {storage_type}，可用: {', '.join(STORAGE_REGISTRY)}")
    _storage_instance = await builder(config)
    return _storage_instance


async def close_storage():
    global _storage_instance
    if _storage_instance is not None:
        await close_sqlite_storage()
        _storage_instance = None
