from pydantic import BaseModel, ConfigDict

class FileInfo(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    name: str
    size: int
    mime_type: str
    type: str
    extension: str
    modified: bool = False
