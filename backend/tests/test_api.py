from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.api.dependencies import exiftool_service,file_service,metadata_service
from app.services.file_service import FileService
from app.services.metadata_service import MetadataService

class FakeExif:
 def get_version(self): return "13.0"
 def read_metadata(self,path): return {"File:FileType":"TXT","File:MIMEType":"text/plain","XMP:Artist":"Ana","EXIF:GPSLatitude":-22.0}
 def write_metadata(self,path,changes): path.write_bytes(path.read_bytes()+b"!")
 def remove_gps(self,path): path.write_bytes(path.read_bytes()+b"g")
 def remove_all_metadata(self,path): path.write_bytes(path.read_bytes()+b"m")
 def remove_tags(self,path,tags): path.write_bytes(path.read_bytes()+b"s")

def test_complete_api_flow(tmp_path):
 fs=FileService(tmp_path,1000,3600); ex=FakeExif(); ms=MetadataService(ex)
 app.dependency_overrides[file_service]=lambda:fs;app.dependency_overrides[exiftool_service]=lambda:ex;app.dependency_overrides[metadata_service]=lambda:ms
 with TestClient(app) as c:
  uploaded=c.post("/api/files",files={"file":("arquivo com acento ç.txt",b"hello","text/plain")}); assert uploaded.status_code==201
  fid=uploaded.json()["file"]["id"]
  assert c.get(f"/api/files/{fid}/metadata").status_code==200
  assert c.patch(f"/api/files/{fid}/metadata",json={"changes":[{"tag":"XMP:Artist","value":"Luís"}]}).status_code==200
  assert c.get(f"/api/files/{fid}/privacy").json()["items"]
  assert c.post(f"/api/files/{fid}/remove-gps").status_code==200
  assert c.post(f"/api/files/{fid}/remove-selected",json={"tags":["XMP:Artist"]}).status_code==200
  assert c.post(f"/api/files/{fid}/remove-metadata").status_code==200
  assert c.get(f"/api/files/{fid}/export/csv").status_code==200
  assert c.post(f"/api/files/{fid}/restore").status_code==200
  assert c.get(f"/api/files/{fid}/download?finalize=true").content.startswith(b"hello")
  assert c.get(f"/api/files/{fid}").status_code==404
 app.dependency_overrides.clear()
