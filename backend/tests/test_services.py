import json
import subprocess
from pathlib import Path
from unittest.mock import Mock

import pytest

from backend.services.exiftool_service import ExifToolError, ExifToolService
from backend.services.file_service import FileService
from backend.services.metadata_service import MetadataService
from backend.services.privacy_service import PrivacyService


@pytest.fixture(autouse=True)
def mock_exiftool_lookup(monkeypatch):
    monkeypatch.setattr("backend.services.exiftool_service.shutil.which", lambda name, path=None: name)


def test_exiftool_reads_json_once(tmp_path, monkeypatch):
    p = tmp_path / "foto com espaço.jpg"
    p.write_bytes(b"x")
    run = Mock(return_value=subprocess.CompletedProcess([], 0, json.dumps([{"EXIF:Artist": "Luís"}]), ""))
    monkeypatch.setattr(subprocess, "run", run)
    assert ExifToolService().read_metadata(p)["EXIF:Artist"] == "Luís"
    assert run.call_count == 1
    assert run.call_args.kwargs["shell"] is False


def test_exiftool_invalid_json(tmp_path, monkeypatch):
    p = tmp_path / "x"
    p.write_bytes(b"x")
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: subprocess.CompletedProcess([], 0, "no", ""))
    with pytest.raises(ExifToolError):
        ExifToolService().read_metadata(p)


def test_batch_write_is_single_safe_process(tmp_path, monkeypatch):
    p = tmp_path / "x.jpg"
    p.write_bytes(b"x")
    run = Mock(return_value=subprocess.CompletedProcess([], 0, "ok", ""))
    monkeypatch.setattr(subprocess, "run", run)
    ExifToolService().write_metadata(p, {"XMP:Artist": "A; rm -rf /", "XMP:Copyright": "©"})
    args = run.call_args.args[0]
    assert "-XMP:Artist=A; rm -rf /" in args and run.call_count == 1


def test_metadata_friendly_and_privacy():
    service = MetadataService(Mock())
    fields = service.organize({"EXIF:Artist": "Ana", "EXIF:GPSLatitude": -20.1, "File:FileName": "x"})
    assert next(x for x in fields if x.name == "Artist").display_name == "Autor"
    assert not next(x for x in fields if x.name == "FileName").editable
    items = PrivacyService().analyze(fields)
    assert {i.category for i in items} >= {"location", "identity"}


def test_validation_rejects_traversal_tag():
    with pytest.raises(ValueError):
        MetadataService.validate("../../x", "a")


def test_file_name_sanitization_and_cleanup(tmp_path):
    fs = FileService(tmp_path, 10, 0)
    assert fs.sanitize_name("../../olá ?.jpg") == "olá _.jpg"
    old = tmp_path / "old"
    old.mkdir()
    assert fs.cleanup() == 1


def test_exiftool_resolves_binary_from_path(tmp_path, monkeypatch):
    executable = tmp_path / "exiftool.exe"
    executable.write_bytes(b"")
    monkeypatch.setattr("backend.services.exiftool_service.shutil.which", lambda name, path=None: str(executable))
    assert ExifToolService().find_executable() == str(executable)


def test_exiftool_reports_missing_binary(monkeypatch):
    monkeypatch.setattr("backend.services.exiftool_service.shutil.which", lambda name, path=None: None)
    monkeypatch.setattr("backend.services.exiftool_service.os.name", "posix")
    with pytest.raises(ExifToolError, match="METADATA_EXIFTOOL_BINARY"):
        ExifToolService()._run(["-ver"])


def test_exiftool_reloads_windows_registry_path(monkeypatch):
    calls = []

    def lookup(name, path=None):
        calls.append(path)
        return r"C:\Tools\ExifTool\exiftool.exe" if path == "updated-path" else None

    monkeypatch.setattr("backend.services.exiftool_service.shutil.which", lookup)
    monkeypatch.setattr("backend.services.exiftool_service.os.name", "nt")
    monkeypatch.setattr(ExifToolService, "_windows_registry_path", lambda self: "updated-path")
    assert ExifToolService().find_executable() == r"C:\Tools\ExifTool\exiftool.exe"
    assert calls == [None, "updated-path"]


def test_pdf_includes_absent_writable_document_fields():
    service = MetadataService(Mock())
    fields = service.organize({"File:FileType": "PDF", "PDF:Creator": "LaTeX"})
    by_tag = {field.full_name: field for field in fields}
    assert by_tag["PDF:Title"].suggested and by_tag["PDF:Title"].editable
    assert by_tag["PDF:Author"].display_name == "Autor"
    assert by_tag["PDF:Subject"].display_name == "Assunto"
    assert by_tag["PDF:Keywords"].display_name == "Palavras-chave"
    assert by_tag["XMP-dc:Description"].display_name == "Descrição"
    assert by_tag["XMP-dc:Language"].display_name == "Idioma"
    assert by_tag["PDF:Creator"].value == "LaTeX"


def test_pdf_does_not_duplicate_existing_suggested_field():
    service = MetadataService(Mock())
    fields = service.organize({"File:FileType": "PDF", "PDF:Title": "Currículo"})
    titles = [field for field in fields if field.full_name == "PDF:Title"]
    assert len(titles) == 1
    assert not titles[0].suggested
    assert titles[0].value == "Currículo"


def test_metadata_fields_include_contextual_filling_help():
    service = MetadataService(Mock())
    fields = service.organize({"File:FileType": "PDF"})
    by_tag = {field.full_name: field for field in fields}
    assert "ponto e vírgula" in by_tag["PDF:Keywords"].help_text
    assert "pt-BR" in by_tag["XMP-dc:Language"].help_text
    assert by_tag["PDF:Title"].help_text


def test_keyword_lists_are_written_with_exiftool_separator(tmp_path, monkeypatch):
    p = tmp_path / "cv.pdf"
    p.write_bytes(b"pdf")
    run = Mock(return_value=subprocess.CompletedProcess([], 0, "ok", ""))
    monkeypatch.setattr(subprocess, "run", run)
    ExifToolService().write_metadata(
    p,
    {"PDF:Keywords": '["Luis Furmiga","curriculum vitæ","résumé","developer"]'},
    )
    args = run.call_args.args[0]
    assert "-sep" not in args
    assert "-PDF:Keywords=" in args
    assert "-PDF:Keywords+=Luis Furmiga" in args
    assert "-PDF:Keywords+=curriculum vitæ" in args
    assert "-PDF:Keywords+=résumé" in args
    assert "-PDF:Keywords+=developer" in args


def test_repeated_semicolons_and_empty_items_are_removed():
    assert ExifToolService.normalize_list_value("Tag01;; Tag02; ; tag02") == [
    "Tag01",
    "Tag02",
    ]


def test_scalar_values_keep_semicolons():
    assert ExifToolService._format_scalar("Backend; Developer") == "Backend; Developer"


def test_metadata_read_normalizes_legacy_keyword_separators():
    service = MetadataService(ExifToolService())
    fields = service.organize(
    {"File:FileType": "PDF", "PDF:Keywords": ["Tag01;", "", "Tag02"]}
    )
    keywords = next(field for field in fields if field.full_name == "PDF:Keywords")
    assert keywords.value == ["Tag01", "Tag02"]
