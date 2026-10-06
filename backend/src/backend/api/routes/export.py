import csv
import io
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from backend.api.dependencies import file_service, metadata_service

router = APIRouter(prefix="/files/{file_id}/export", tags=["exportação"])


@router.get("/{format}")
def export(file_id: str, format: str, fs=Depends(file_service), ms=Depends(metadata_service)):
    s = fs.get(file_id)
    fields = ms.organize(ms.read_raw(s.working))
    data = {f.full_name: f.value for f in fields}
    if format == "json":
        content = json.dumps({"file": s.display_name, "metadata": data}, ensure_ascii=False, indent=2)
        media = "application/json"
    elif format == "csv":
        out = io.StringIO()
        writer = csv.writer(out)
        writer.writerow(["Tag", "Nome", "Grupo", "Valor"])
        writer.writerows((f.full_name, f.display_name, f.group, str(f.value)) for f in fields)
        content = out.getvalue()
        media = "text/csv"
    elif format == "txt":
        content = "\n".join(f"{f.full_name}={f.value}" for f in fields)
        media = "text/plain"
    else:
        raise HTTPException(404, "Formato de exportação não suportado.")
    return Response(
        content,
        media_type=f"{media}; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="metadados-{file_id[:8]}.{format}"'},
    )
