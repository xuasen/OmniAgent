"""Audit API endpoints."""

from fastapi import APIRouter

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
async def query_audit_logs() -> list[dict]:
    return []


@router.get("/export")
async def export_audit_logs() -> str:
    raise NotImplementedError


@router.get("/metrics")
async def get_metrics() -> dict:
    raise NotImplementedError
