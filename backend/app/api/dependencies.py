from functools import lru_cache
from app.core.config import settings
from app.services.exiftool_service import ExifToolService
from app.services.file_service import FileService
from app.services.metadata_service import MetadataService
from app.services.privacy_service import PrivacyService

@lru_cache
def exiftool_service(): return ExifToolService(settings.exiftool_binary)
@lru_cache
def file_service(): return FileService(settings.workspace_root, settings.max_upload_size, settings.session_ttl_seconds)
@lru_cache
def metadata_service(): return MetadataService(exiftool_service())
@lru_cache
def privacy_service(): return PrivacyService()
