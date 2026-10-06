"""Normalize ExifTool output into editable, user-facing metadata fields."""

import re
from typing import Any

from backend.models.metadata import MetadataField

from backend.services.exiftool_service import ExifToolService

FRIENDLY = {
    "Artist": "Autor",
    "Author": "Autor",
    "Copyright": "Direitos autorais",
    "DateTimeOriginal": "Data da captura",
    "CreateDate": "Data de criação",
    "ModifyDate": "Data de modificação",
    "Make": "Fabricante",
    "Model": "Modelo do dispositivo",
    "Software": "Software",
    "ImageWidth": "Largura",
    "ImageHeight": "Altura",
    "GPSLatitude": "Latitude",
    "GPSLongitude": "Longitude",
    "GPSAltitude": "Altitude",
    "Comment": "Comentário",
    "Description": "Descrição",
    "Title": "Título",
    "Subject": "Assunto",
    "Keywords": "Palavras-chave",
    "Language": "Idioma",
}
HELP_TEXT = {
    "Title": "Use um título curto e descritivo para identificar o documento.",
    "Author": "Informe o nome da pessoa ou organização autora do conteúdo.",
    "Artist": "Informe o nome da pessoa ou organização autora do conteúdo.",
    "Subject": "Resuma o tema principal do documento em uma frase curta.",
    "Keywords": "Use um único ponto e vírgula para separar cada palavra-chave. Espaços extras e separadores repetidos serão corrigidos. Exemplo: Java; Spring Boot; PostgreSQL; Docker.",
    "Description": "Descreva brevemente o conteúdo e a finalidade do arquivo.",
    "Language": "Use um código de idioma, como pt-BR para português do Brasil ou en-US para inglês dos EUA.",
    "Creator": "Programa que criou o documento. Normalmente, é melhor manter o valor existente.",
    "Producer": "Programa que gerou o PDF. Normalmente, é melhor manter o valor existente.",
    "CreateDate": "Use a data real de criação. Formato ExifTool: AAAA:MM:DD HH:mm:ss com fuso opcional.",
    "ModifyDate": "Use a data real da última modificação. Formato ExifTool: AAAA:MM:DD HH:mm:ss com fuso opcional.",
}
READ_ONLY_GROUPS = {"File", "System", "Composite", "ExifTool"}
READ_ONLY_NAMES = {
    "FileName",
    "Directory",
    "FileSize",
    "FilePermissions",
    "FileType",
    "FileTypeExtension",
    "MIMEType",
    "ExifToolVersion",
}

# ExifTool only returns tags that already exist. These profiles expose useful,
# writable tags as empty fields so users can add document metadata from scratch.
SUGGESTED_FIELDS: dict[str, tuple[str, ...]] = {
    "PDF": (
        "PDF:Title",
        "PDF:Author",
        "PDF:Subject",
        "PDF:Keywords",
        "XMP-dc:Description",
        "XMP-dc:Language",
    ),
}


class MetadataService:
    def __init__(self, exiftool: ExifToolService) -> None:
        self.exiftool = exiftool

    def read_raw(self, path):
        return self.exiftool.read_metadata(path)

    def organize(self, raw: dict[str, Any]) -> list[MetadataField]:
        fields = [self._field(key, value) for key, value in raw.items() if key != "SourceFile"]
        existing = {field.full_name.casefold() for field in fields}
        file_type = str(raw.get("File:FileType", "")).upper()

        for full_name in SUGGESTED_FIELDS.get(file_type, ()):
            if full_name.casefold() not in existing:
                fields.append(self._field(full_name, "", suggested=True))

        return sorted(fields, key=lambda field: (field.group.lower(), field.display_name.lower()))

    def _field(self, key: str, value: Any, suggested: bool = False) -> MetadataField:
        group, name = key.split(":", 1) if ":" in key else ("Outros", key)
        if ExifToolService.is_list_tag(f"{group}:{name}"):
            value = ExifToolService.normalize_list_value(value)
        return MetadataField(
            group=group,
            name=name,
            full_name=f"{group}:{name}",
            display_name=FRIENDLY.get(name, self._humanize(name)),
            value=value,
            editable=group not in READ_ONLY_GROUPS and name not in READ_ONLY_NAMES,
            value_type=self._type(name, value),
            suggested=suggested,
            help_text=HELP_TEXT.get(name),
        )

    def update(self, path, changes: dict[str, Any]) -> None:
        for tag, value in changes.items():
            self.validate(tag, value)
        self.exiftool.write_metadata(path, changes)

    @staticmethod
    def validate(tag: str, value: Any) -> None:
        if not re.fullmatch(r"[A-Za-z0-9_-]+:[A-Za-z0-9_-]+", tag):
            raise ValueError("Tag inválida.")
        if tag.split(":", 1)[0] in READ_ONLY_GROUPS:
            raise ValueError("Esta tag é somente leitura.")
        if "GPSLatitude" in tag and not -90 <= float(value) <= 90:
            raise ValueError("Latitude inválida.")
        if "GPSLongitude" in tag and not -180 <= float(value) <= 180:
            raise ValueError("Longitude inválida.")

    @staticmethod
    def _humanize(name: str) -> str:
        return re.sub(r"(?<!^)(?=[A-Z])", " ", name).replace("_", " ").strip()

    @staticmethod
    def _type(name: str, value: Any) -> str:
        if isinstance(value, bool):
            return "boolean"
        if isinstance(value, (int, float)):
            return "number"
        if "Date" in name or "Time" in name:
            return "date"
        if isinstance(value, str) and len(value) > 100:
            return "long_text"
        return "text"
