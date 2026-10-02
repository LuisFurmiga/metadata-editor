from typing import Any
from pydantic import BaseModel, Field, field_validator

class MetadataChange(BaseModel):
    tag: str = Field(min_length=1, max_length=200, pattern=r"^[A-Za-z0-9_-]+:[A-Za-z0-9_-]+$")
    value: Any
    @field_validator("value")
    @classmethod
    def safe_value(cls, value: Any) -> Any:
        if isinstance(value, (dict, list)) or value is None:
            raise ValueError("O valor deve ser texto, número ou booleano")
        if isinstance(value, str) and len(value) > 100_000:
            raise ValueError("Valor muito longo")
        return value

class MetadataUpdateRequest(BaseModel):
    changes: list[MetadataChange] = Field(min_length=1, max_length=200)

class SelectiveRemovalRequest(BaseModel):
    tags: list[str] = Field(min_length=1, max_length=100)
    @field_validator("tags")
    @classmethod
    def safe_tags(cls, tags: list[str]) -> list[str]:
        import re
        if any(not re.fullmatch(r"[A-Za-z0-9_-]+:[A-Za-z0-9_-]+", tag) for tag in tags):
            raise ValueError("Tag inválida")
        return list(dict.fromkeys(tags))
