import logging, mimetypes, re, shutil, time, uuid
from dataclasses import dataclass
from pathlib import Path
from fastapi import UploadFile
from app.models.file_info import FileInfo

logger = logging.getLogger(__name__)

class FileNotFoundError_(LookupError): pass
class UploadTooLargeError(ValueError): pass

@dataclass(frozen=True)
class FileSession:
    id: str
    directory: Path
    original: Path
    working: Path
    display_name: str

class FileService:
    def __init__(self, root: Path, max_size: int, ttl_seconds: int) -> None:
        self.root, self.max_size, self.ttl_seconds = root, max_size, ttl_seconds
        root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def sanitize_name(name: str | None) -> str:
        raw = Path((name or "arquivo").replace("\\", "/")).name
        safe = re.sub(r"[\x00-\x1f<>:\"/\\|?*]", "_", raw).strip(" .")
        return (safe or "arquivo")[:180]

    async def create(self, upload: UploadFile) -> FileSession:
        file_id, name = str(uuid.uuid4()), self.sanitize_name(upload.filename)
        directory = self.root / file_id
        directory.mkdir(mode=0o700)
        original, working = directory / f"original{Path(name).suffix[:20]}", directory / f"working{Path(name).suffix[:20]}"
        size = 0
        try:
            with original.open("wb") as target:
                while chunk := await upload.read(1024 * 1024):
                    size += len(chunk)
                    if size > self.max_size: raise UploadTooLargeError("O arquivo excede o limite configurado.")
                    target.write(chunk)
            if size == 0: raise ValueError("O arquivo está vazio.")
            shutil.copy2(original, working)
            (directory / "name.txt").write_text(name, encoding="utf-8")
        except Exception:
            shutil.rmtree(directory, ignore_errors=True)
            raise
        finally:
            await upload.close()
        logger.info("Upload criado: sessão=%s tamanho=%s", file_id, size)
        return FileSession(file_id, directory, original, working, name)

    def get(self, file_id: str) -> FileSession:
        try: uuid.UUID(file_id)
        except ValueError as exc: raise FileNotFoundError_("Sessão não encontrada.") from exc
        directory = self.root / file_id
        name_file = directory / "name.txt"
        candidates = list(directory.glob("original*")) if directory.is_dir() else []
        workings = list(directory.glob("working*")) if directory.is_dir() else []
        if not name_file.is_file() or len(candidates) != 1 or len(workings) != 1: raise FileNotFoundError_("Sessão não encontrada.")
        directory.touch(exist_ok=True)
        return FileSession(file_id, directory, candidates[0], workings[0], name_file.read_text(encoding="utf-8"))

    def info(self, session: FileSession, raw: dict | None = None) -> FileInfo:
        raw = raw or {}; mime = str(raw.get("File:MIMEType") or mimetypes.guess_type(session.display_name)[0] or "application/octet-stream")
        return FileInfo(id=session.id, name=session.display_name, size=session.working.stat().st_size, mime_type=mime, type=str(raw.get("File:FileType") or Path(session.display_name).suffix.lstrip(".").upper() or "Arquivo"), extension=Path(session.display_name).suffix, modified=session.working.stat().st_mtime_ns != session.original.stat().st_mtime_ns or session.working.stat().st_size != session.original.stat().st_size)

    def restore(self, file_id: str) -> FileSession:
        session = self.get(file_id); shutil.copy2(session.original, session.working); return session
    def delete(self, file_id: str) -> None:
        session = self.get(file_id); shutil.rmtree(session.directory)
    def cleanup(self) -> int:
        removed, cutoff = 0, time.time() - self.ttl_seconds
        for path in self.root.iterdir():
            if path.is_dir() and path.stat().st_mtime < cutoff:
                shutil.rmtree(path, ignore_errors=True); removed += 1
        if removed: logger.info("Sessões temporárias removidas: %s", removed)
        return removed
