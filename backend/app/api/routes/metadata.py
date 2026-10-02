from fastapi import APIRouter, Depends
from app.api.dependencies import file_service, metadata_service
from app.models.metadata import FileMetadataResponse
from app.models.requests import MetadataUpdateRequest
router=APIRouter(prefix="/files/{file_id}", tags=["metadados"])
def response(file_id, fs, ms):
    s=fs.get(file_id); raw=ms.read_raw(s.working); return FileMetadataResponse(file=fs.info(s,raw),metadata=ms.organize(raw))
@router.get("/metadata",response_model=FileMetadataResponse)
def metadata(file_id: str, fs=Depends(file_service),ms=Depends(metadata_service)): return response(file_id,fs,ms)
@router.patch("/metadata",response_model=FileMetadataResponse)
def update(file_id: str,payload: MetadataUpdateRequest,fs=Depends(file_service),ms=Depends(metadata_service)):
    s=fs.get(file_id); ms.update(s.working,{x.tag:x.value for x in payload.changes}); return response(file_id,fs,ms)
@router.post("/remove-gps",response_model=FileMetadataResponse)
def remove_gps(file_id: str,fs=Depends(file_service),ms=Depends(metadata_service)):
    s=fs.get(file_id); ms.exiftool.remove_gps(s.working); return response(file_id,fs,ms)
@router.post("/remove-metadata",response_model=FileMetadataResponse)
def remove_all(file_id: str,fs=Depends(file_service),ms=Depends(metadata_service)):
    s=fs.get(file_id); ms.exiftool.remove_all_metadata(s.working); return response(file_id,fs,ms)
