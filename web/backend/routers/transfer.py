from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse

from core.exceptions import TransferError
from core.transfer.direction import build_adapters
from core.transfer.engine import TransferEngine
from core.transfer.reporter import write_report
from web.backend.deps import require_csrf, require_session
from web.backend.jobs import JobManager, JobState, get_jobs
from web.backend.routers.playlists import _spotify_adapter, _ytmusic_adapter
from web.backend.schemas import JobCreated, JobSnapshot, TransferRequest
from web.backend.sessions import SessionData

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transfer", tags=["transfer"])


def _run_engine(
    job: JobState,
    request: TransferRequest,
    spotify_adapter,
    ytmusic_adapter,
    jobs: JobManager,
    loop: asyncio.AbstractEventLoop,
):
    job.status = "running"
    source, target = build_adapters(request.direction, spotify_adapter, ytmusic_adapter)

    def callback(event):
        loop.call_soon_threadsafe(jobs.push_event, job, event)

    try:
        engine = TransferEngine(
            source=source,
            target=target,
            direction=request.direction,
            progress_callback=callback,
        )
        report = engine.transfer(request.playlist_ids, idempotency=request.idempotency)
        path = write_report(report)
        job.report = report
        job.report_path = str(path)
        job.status = "done"
    except TransferError as exc:
        logger.exception("Transfer failed")
        job.status = "error"
        job.error = str(exc)
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Unexpected transfer failure")
        job.status = "error"
        job.error = f"unexpected: {exc}"
    finally:
        loop.call_soon_threadsafe(job.finished.set)


@router.post("", response_model=JobCreated)
async def create_transfer(
    body: TransferRequest,
    background: BackgroundTasks,
    session: SessionData = Depends(require_csrf),
    jobs: JobManager = Depends(get_jobs),
) -> JobCreated:
    if not body.playlist_ids:
        raise HTTPException(status_code=400, detail="No playlist_ids provided")
    spotify_adapter = _spotify_adapter(session)
    ytmusic_adapter = _ytmusic_adapter(session)

    job = jobs.create(body.direction, body.idempotency)
    loop = asyncio.get_running_loop()

    background.add_task(
        asyncio.to_thread,
        _run_engine,
        job,
        body,
        spotify_adapter,
        ytmusic_adapter,
        jobs,
        loop,
    )
    return JobCreated(job_id=job.job_id)


@router.get("/{job_id}", response_model=JobSnapshot)
def get_job(job_id: str, _: SessionData = Depends(require_session),
            jobs: JobManager = Depends(get_jobs)) -> JobSnapshot:
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobSnapshot(**jobs.snapshot(job))


@router.get("/{job_id}/report", response_model=None)
def get_report(job_id: str, _: SessionData = Depends(require_session),
               jobs: JobManager = Depends(get_jobs)):
    job = jobs.get(job_id)
    if not job or not job.report_path:
        raise HTTPException(status_code=404, detail="Report not available yet")
    path = Path(job.report_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report file missing")
    return FileResponse(path, media_type="application/json", filename=path.name)


@router.websocket("/{job_id}/stream")
async def stream_job(websocket: WebSocket, job_id: str) -> None:
    jobs = get_jobs()
    job = jobs.get(job_id)
    if not job:
        await websocket.close(code=4404)
        return
    await websocket.accept()
    try:
        # First: replay existing events so a late connection still gets context
        for event in list(job.last_events):
            await websocket.send_text(json.dumps(event))
        while not job.finished.is_set() or not job.queue.empty():
            try:
                event = await asyncio.wait_for(job.queue.get(), timeout=30.0)
            except asyncio.TimeoutError:
                await websocket.send_text(json.dumps({"type": "ping"}))
                continue
            await websocket.send_text(json.dumps(event))
        await websocket.send_text(
            json.dumps({"type": "stream_closed", "status": job.status, "error": job.error})
        )
    except WebSocketDisconnect:
        return
