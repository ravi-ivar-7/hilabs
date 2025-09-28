from celery import Celery
import redis
from typing import Dict, Any, Optional
from ..core.config import get_settings

class CeleryService:
    def __init__(self):
        settings = get_settings()
        self.celery_app = Celery(
            'hilabs_backend',
            broker=settings.celery_broker_url,
            backend=settings.celery_result_backend
        )
        self.redis_client = redis.from_url(settings.redis_url)
    
    def queue_preprocessing_task(self, contract_id: str) -> str:
        task = self.celery_app.send_task(
            'tasks.contract_preprocessing.extract_contract_text',
            args=[contract_id],
            queue='contract_preprocessing'
        )
        return task.id
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        try:
            result = self.celery_app.AsyncResult(task_id)
            return {
                "status": result.status,
                "progress": result.info.get("progress", 0) if result.info else 0,
                "message": result.info.get("message", "") if result.info else "",
                "result": result.result if result.successful() else None
            }
        except Exception:
            return {
                "status": "UNKNOWN",
                "progress": 0,
                "message": "Task status unavailable",
                "result": None
            }
    
    def cancel_task(self, task_id: str) -> bool:
        try:
            self.celery_app.control.revoke(task_id, terminate=True)
            return True
        except Exception:
            return False
    
    def get_queue_length(self, queue_name: str = "contract_preprocessing") -> int:
        try:
            return self.redis_client.llen(f"celery:{queue_name}")
        except Exception:
            return 0
