from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from app.api.dependencies import file_service, metadata_service
from app.models.file_info import FileInfo
from app.models.metadata import FileMetadataResponse
from app.services.file_service import FileService
from app.services.metadata_service import MetadataService

router=APIRouter(prefix="/files", tags=["arquivos"])
@router.post("", response_model=FileMetadataResponse, status_code=201)
async def upload(file: UploadFile=File(...), fs: FileService=Depends(file_service), ms: MetadataService=Depends(metadata_service)):
    session=await fs.create(file)
    try:
        raw=ms.read_raw(session.working)
    except Exception:
        fs.delete(session.id)
        raise
    return FileMetadataResponse(file=fs.info(session,raw), metadata=ms.organize(raw))
@router.get("/{file_id}", response_model=FileInfo)
def get_file(file_id: str, fs: FileService=Depends(file_service), ms: MetadataService=Depends(metadata_service)):
    session=fs.get(file_id); return fs.info(session,ms.read_raw(session.working))
@router.delete("/{file_id}", status_code=204)
def delete_file(file_id: str, fs: FileService=Depends(file_service)): fs.delete(file_id)
@router.post("/{file_id}/restore", response_model=FileMetadataResponse)
def restore(file_id: str, fs: FileService=Depends(file_service), ms: MetadataService=Depends(metadata_service)):
    session=fs.restore(file_id); raw=ms.read_raw(session.working); return FileMetadataResponse(file=fs.info(session,raw),metadata=ms.organize(raw))
@router.get("/{file_id}/download")
def download(file_id: str, finalize: bool = False, fs: FileService=Depends(file_service)):
    session=fs.get(file_id); stem, suffix=__import__('pathlib').Path(session.display_name).stem, __import__('pathlib').Path(session.display_name).suffix
    return FileResponse(session.working, filename=f"{stem}-editado{suffix}", media_type="application/octet-stream", background=BackgroundTask(fs.delete, file_id) if finalize else None)
