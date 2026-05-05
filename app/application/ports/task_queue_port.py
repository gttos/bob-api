from abc import ABC, abstractmethod
from typing import Optional

class TaskQueuePort(ABC):
    @abstractmethod
    async def enqueue(self, task_name: str, *args, correlation_id: Optional[str] = None) -> str:
        pass
