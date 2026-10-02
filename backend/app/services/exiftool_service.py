"""Safe process adapter for ExifTool, including Windows executable discovery."""

import importlib
import json
import logging
import os
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
        # -sep only affects list-type tags. Scalar fields keep semicolons verbatim,
        # while values such as PDF:Keywords are split into proper list entries.
        arguments = ["-overwrite_original", "-sep", "; "]
        arguments.extend(
            f"-{tag}={self._format(tag, value)}" for tag, value in changes.items()
        )
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
    def _format(tag: str, value: Any) -> str:
        if value is True:
            return "true"
        if value is False:
            return "false"
        if isinstance(value, list):
            return "; ".join(str(item) for item in value)

        text = str(value)
        is_list_tag = tag.casefold().endswith(":keywords") or tag.casefold() == "xmp-dc:subject"
        if is_list_tag and text.lstrip().startswith("["):
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                return text
            if isinstance(parsed, list):
                return "; ".join(str(item) for item in parsed)
        return text

    @staticmethod
    def _ensure_file(path: Path) -> None:
        if not path.is_file():
            raise ExifToolError("Arquivo não encontrado.")
