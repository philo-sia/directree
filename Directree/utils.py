import sys
import os
import re

from Directree.constants import INVALID_CHARS_RE, ANSI_RE, WINDOWS_RESERVED_NAMES


def app_base_dir() -> str:
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except NameError:
        return os.getcwd()


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text).replace("\ufeff", "")


def sanitize_name(name: str) -> tuple[str, bool, list[str], str | None]:
    warnings: list[str] = []

    original = name.strip()
    explicit_dir = original.endswith(("/", "\\"))

    if explicit_dir:
        original = original.rstrip("/\\").rstrip()

    if not original:
        return "", explicit_dir, warnings, "Empty item name."

    if original in {".", ".."}:
        return "", explicit_dir, warnings, f"Unsafe path component {original!r} is not allowed."

    if os.path.isabs(original) or re.match(r"^[A-Za-z]:[\\/]", original):
        return "", explicit_dir, warnings, f"Absolute paths are not allowed: {original!r}"

    sanitized = INVALID_CHARS_RE.sub("_", original).strip()

    if sanitized != original:
        warnings.append(
            f"Renamed {original!r} to {sanitized!r} because it contained invalid filename characters."
        )

    if not sanitized:
        return "", explicit_dir, warnings, f"Item {name!r} became empty after sanitization."

    if sanitized in {".", ".."}:
        return "", explicit_dir, warnings, f"Unsafe path component {sanitized!r} is not allowed."

    stem = sanitized.split(".", 1)[0].upper()
    if stem in WINDOWS_RESERVED_NAMES:
        old = sanitized
        sanitized = f"{sanitized}_"
        warnings.append(
            f"Renamed reserved Windows filename {old!r} to {sanitized!r}."
        )

    if sys.platform == "win32":
        stripped = sanitized.rstrip(". ")
        if stripped != sanitized:
            warnings.append(
                f"Trimmed trailing spaces/periods from {sanitized!r} for Windows compatibility."
            )
            sanitized = stripped

        if not sanitized:
            return "", explicit_dir, warnings, f"Item {name!r} became empty after Windows trimming."

    return sanitized, explicit_dir, warnings, None


def safe_join_under_root(root: str, parent: str, name: str) -> tuple[str | None, str | None]:
    root_abs = os.path.abspath(root)
    full_path = os.path.abspath(os.path.join(parent, name))

    try:
        common = os.path.commonpath([root_abs, full_path])
    except ValueError:
        return None, "Path escapes root or is on another drive."

    if common != root_abs:
        return None, f"Path escapes selected root: {full_path}"

    return full_path, None


def safe_resolve_relative_path(root: str, rel_path: str) -> tuple[str | None, list[str], str | None]:
    warnings: list[str] = []
    parts = [part for part in rel_path.replace("\\", "/").split("/") if part]

    if not parts:
        return None, warnings, "Empty relative path."

    root_abs = os.path.abspath(root)
    current_parent = root_abs

    for part in parts:
        clean, _explicit_dir, part_warnings, error = sanitize_name(part)
        warnings.extend(part_warnings)

        if error:
            return None, warnings, error

        full_path, path_error = safe_join_under_root(root_abs, current_parent, clean)
        if path_error or full_path is None:
            return None, warnings, path_error

        current_parent = full_path

    return current_parent, warnings, None
