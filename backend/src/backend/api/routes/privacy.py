from fastapi import APIRouter, Depends

from backend.models.metadata import FileMetadataResponse, PrivacyResponse
from backend.models.requests import SelectiveRemovalRequest
from backend.api.dependencies import file_service, metadata_service, privacy_service

router = APIRouter(prefix="/files/{file_id}", tags=["privacidade"])


@router.get("/privacy", response_model=PrivacyResponse)
def privacy(file_id: str, fs=Depends(file_service), ms=Depends(metadata_service), ps=Depends(privacy_service)):
    s = fs.get(file_id)
    return PrivacyResponse(items=ps.analyze(ms.organize(ms.read_raw(s.working))))


@router.post("/remove-selected", response_model=FileMetadataResponse)
def remove_selected(
    file_id: str, payload: SelectiveRemovalRequest, fs=Depends(file_service), ms=Depends(metadata_service)
):
    s = fs.get(file_id)
    ms.exiftool.remove_tags(s.working, payload.tags)
    raw = ms.read_raw(s.working)
    return FileMetadataResponse(file=fs.info(s, raw), metadata=ms.organize(raw))
