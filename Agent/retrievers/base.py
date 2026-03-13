from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseRetriever(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.setup()

    @abstractmethod
    def setup(self):
        pass

    @abstractmethod
    async def aretrieve(self, question: str) -> str:
        pass