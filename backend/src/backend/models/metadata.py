from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from .file_info import FileInfo


class MetadataField(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    group: str
    name: str
    full_name: str = Field(serialization_alias="fullName")
    display_name: str = Field(serialization_alias="displayName")
    value: Any
    editable: bool
    suggested: bool = False
    help_text: str | None = Field(default=None, serialization_alias="helpText")
    value_type: Literal["text", "number", "boolean", "date", "long_text"] = Field(serialization_alias="valueType")


class FileMetadataResponse(BaseModel):
    file: FileInfo
    metadata: list[MetadataField]


class PrivacyItem(BaseModel):
    category: str
    label: str
    severity: Literal["low", "medium", "high"]
    tags: list[str]


class PrivacyResponse(BaseModel):
    items: list[PrivacyItem]
