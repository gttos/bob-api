from typing import Optional
from celery import Celery

from app.application.ports.task_queue_port import TaskQueuePort
from app.infrastructure.tasks.celery_app import celery_app

class CeleryTaskQueueAdapter(TaskQueuePort):
    def __init__(self, celery_app_instance: Celery):
        self.celery_app = celery_app_instance

    async def enqueue(self, task_name: str, *args, correlation_id: Optional[str] = None) -> str:
        # Pass correlation_id as kwarg so task can extract it
        kwargs = {"correlation_id": correlation_id} if correlation_id else {}

        result = self.celery_app.send_task(task_name, args=args, kwargs=kwargs)
        return result.id
