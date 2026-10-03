"""Endpoint to check background Celery task status."""

from __future__ import annotations

from typing import Any, Dict
from celery.result import AsyncResult
from fastapi import APIRouter

from app.workers.celery_app import celery_app

router = APIRouter()


@router.get("/{task_id}")
async def get_task_status(task_id: str) -> Dict[str, Any]:
    """Retrieve execution status and result of a Celery background task."""
    result = AsyncResult(task_id, app=celery_app)
    response: Dict[str, Any] = {
        "task_id": task_id,
        "status": result.status,
    }
    if result.ready():
        if result.successful():
            response["result"] = result.result
        else:
            response["error"] = str(result.result)
    return response

