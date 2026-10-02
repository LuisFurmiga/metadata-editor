"""Safe process adapter for ExifTool, including Windows executable discovery."""

import importlib
import json
import logging
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ExifToolError(RuntimeError):
    """Raised when ExifTool cannot be found or complete an operation."""


class ExifToolService:
    def __init__(self, binary: str = "exiftool", timeout: int = 60) -> None:
        self.binary = binary.strip().strip('"')
        self.timeout = timeout

    def find_executable(self) -> str | None:
        """Resolve ExifTool, also reading updated Windows user/machine PATH values.

        A running backend does not inherit environment changes made after its
        terminal was opened. Reading the registry makes an ExifTool installation
        visible without requiring the user to restart Windows or that terminal.
        """
        configured_path = Path(self.binary).expanduser()
        if configured_path.is_file():
            return str(configured_path.resolve())

        executable = shutil.which(self.binary)
        if executable:
            return executable

        if os.name != "nt":
            return None

        registry_path = self._windows_registry_path()
        return shutil.which(self.binary, path=registry_path) if registry_path else None

    @staticmethod
    def _windows_registry_path() -> str:
        winreg = importlib.import_module("winreg")
        locations = (
            (winreg.HKEY_CURRENT_USER, r"Environment"),
            (
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
            ),
        )
        paths = [os.environ.get("PATH", "")]
        for hive, key_name in locations:
            try:
                with winreg.OpenKey(hive, key_name) as key:
                    value, _ = winreg.QueryValueEx(key, "Path")
                    paths.append(winreg.ExpandEnvironmentStrings(str(value)))
            except OSError:
                logger.debug("Não foi possível ler PATH do registro: %s", key_name)
        return os.pathsep.join(filter(None, paths))

    def _run(self, arguments: list[str]) -> subprocess.CompletedProcess[str]:
        executable = self.find_executable()
        if not executable:
            raise ExifToolError(
                "ExifTool não foi localizado. Reinicie o terminal após instalá-lo "
                "ou configure METADATA_EXIFTOOL_BINARY com o caminho completo."
            )
        try:
            result = subprocess.run(
                [executable, *arguments],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout,
                check=False,
                shell=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise ExifToolError("O ExifTool excedeu o tempo limite da operação.") from exc
        except OSError as exc:
            raise ExifToolError("Não foi possível iniciar o ExifTool.") from exc
        if result.returncode != 0:
            logger.error("ExifTool retornou código %s", result.returncode)
            raise ExifToolError(
                result.stderr.strip() or "O ExifTool não conseguiu processar o arquivo."
            )
        return result

    def check_available(self) -> bool:
        return self.get_version() is not None

    def get_version(self) -> str | None:
        try:
            return self._run(["-ver"]).stdout.strip()
        except ExifToolError as exc:
            logger.warning("Diagnóstico do ExifTool: %s", exc)
            return None

    def read_metadata(self, file_path: Path) -> dict[str, Any]:
        self._ensure_file(file_path)
        result = self._run(
            ["-json", "-G", "-s", "-charset", "filename=UTF8", str(file_path)]
        )
        try:
            payload = json.loads(result.stdout)
            if not isinstance(payload, list) or not payload or not isinstance(payload[0], dict):
                raise ValueError
            return payload[0]
        except (json.JSONDecodeError, ValueError) as exc:
            raise ExifToolError("O ExifTool retornou dados inválidos.") from exc

    def write_metadata(self, file_path: Path, changes: dict[str, Any]) -> None:
        self._ensure_file(file_path)
        arguments = ["-overwrite_original"]
        for tag, value in changes.items():
            if self.is_list_tag(tag):
                # Clear first, then append each item separately. Passing a joined
                # string with -sep made some PDF writers retain the delimiter in
                # an item, producing doubled semicolons after the next read.
                arguments.append(f"-{tag}=")
                arguments.extend(
                    f"-{tag}+={item}" for item in self.normalize_list_value(value)
                )
            else:
                arguments.append(f"-{tag}={self._format_scalar(value)}")
        self._run([*arguments, str(file_path)])

    def remove_tags(self, file_path: Path, tags: list[str]) -> None:
        self._ensure_file(file_path)
        self._run(["-overwrite_original", *[f"-{tag}=" for tag in tags], str(file_path)])

    def remove_all_metadata(self, file_path: Path) -> None:
        self._ensure_file(file_path)
        self._run(["-overwrite_original", "-all=", str(file_path)])

    def remove_gps(self, file_path: Path) -> None:
        self._ensure_file(file_path)
        self._run(["-overwrite_original", "-gps:all=", "-xmp:geotag=", str(file_path)])

    @staticmethod
    def is_list_tag(tag: str) -> bool:
        normalized = tag.casefold()
        return normalized.endswith(":keywords") or normalized == "xmp-dc:subject"

    @classmethod
    def normalize_list_value(cls, value: Any) -> list[str]:
        if isinstance(value, list):
            candidates = value
        else:
            text = str(value).strip()
            candidates: list[Any]
            if text.startswith("["):
                try:
                    parsed = json.loads(text)
                except json.JSONDecodeError:
                    parsed = None
                candidates = parsed if isinstance(parsed, list) else re.split(r"\s*;+\s*", text)
            else:
                candidates = re.split(r"\s*;+\s*", text)

        result: list[str] = []
        seen: set[str] = set()
        for candidate in candidates:
            item = str(candidate).strip().strip(";").strip()
            identity = item.casefold()
            if item and identity not in seen:
                result.append(item)
                seen.add(identity)
        return result

    @staticmethod
    def _format_scalar(value: Any) -> str:
        if value is True:
            return "true"
        if value is False:
            return "false"
        return str(value)

    @staticmethod
    def _ensure_file(path: Path) -> None:
        if not path.is_file():
            raise ExifToolError("Arquivo não encontrado.")
