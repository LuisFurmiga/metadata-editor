from backend.models.metadata import MetadataField, PrivacyItem

RULES = [
    ("location", "Localização GPS", "high", ("gps", "location", "geotag")),
    ("identity", "Autor ou proprietário", "medium", ("artist", "author", "owner", "creator")),
    ("device", "Identificador do dispositivo", "medium", ("serialnumber", "deviceid", "cameraid")),
    ("system", "Informação do sistema", "medium", ("hostname", "username", "directory", "filepath")),
    ("editing", "Software e histórico de edição", "low", ("software", "history", "documentancestors")),
    ("comments", "Comentários ou descrição", "low", ("comment", "description")),
]


class PrivacyService:
    def analyze(self, metadata: list[MetadataField]) -> list[PrivacyItem]:
        items = []
        for category, label, severity, needles in RULES:
            tags = [
                f.full_name
                for f in metadata
                if f.value not in (None, "", []) and any(n in f.full_name.lower() for n in needles)
            ]
            if tags:
                items.append(PrivacyItem(category=category, label=label, severity=severity, tags=tags))
        return items
