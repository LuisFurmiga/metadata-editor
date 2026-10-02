import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.dependencies import exiftool_service,file_service
from app.api.routes import export,files,metadata,privacy
from app.core.config import settings
from app.core.logging import configure_logging
from app.services.exiftool_service import ExifToolError
from app.services.file_service import FileNotFoundError_,UploadTooLargeError
configure_logging(); logger=logging.getLogger(__name__)

def error(status:int,code:str,message:str,details=None): return JSONResponse(status_code=status,content={"error":{"code":code,"message":message,"details":details}})
@asynccontextmanager
async def lifespan(app: FastAPI):
 removed=file_service().cleanup(); version=exiftool_service().get_version(); logger.info("Inicialização: ExifTool=%s limpeza=%s",version or "indisponível",removed); yield
app=FastAPI(title=settings.app_name,version="1.0.0",lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=settings.allowed_origins,allow_credentials=False,allow_methods=["GET","POST","PATCH","DELETE"],allow_headers=["Content-Type"])
for router in (files.router,metadata.router,privacy.router,export.router): app.include_router(router,prefix="/api")
@app.get("/api/health")
def health():
 service=exiftool_service(); version=service.get_version(); return {"status":"ok" if version else "degraded","exiftool":{"available":bool(version),"version":version,"executable":service.find_executable()}}
@app.exception_handler(FileNotFoundError_)
def not_found(_:Request,exc:FileNotFoundError_): return error(404,"FILE_NOT_FOUND",str(exc))
@app.exception_handler(UploadTooLargeError)
def too_large(_:Request,exc:UploadTooLargeError): return error(413,"UPLOAD_TOO_LARGE",str(exc))
@app.exception_handler(ExifToolError)
def exif_error(_:Request,exc:ExifToolError): logger.exception("Falha no ExifTool"); return error(422,"EXIFTOOL_ERROR","Não foi possível analisar ou modificar o arquivo.",str(exc))
@app.exception_handler(RequestValidationError)
def validation(_:Request,exc:RequestValidationError): return error(422,"VALIDATION_ERROR","Os dados enviados são inválidos.",str(exc.errors()))
@app.exception_handler(ValueError)
def value_error(_:Request,exc:ValueError): return error(400,"INVALID_INPUT",str(exc))
