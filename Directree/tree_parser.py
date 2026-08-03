import os
import re

from Directree.models import ParsedLine
from Directree.utils import strip_ansi
from Directree.constants import TREE_SKIP_RE, TREE_BRANCH_RE, COMMON_HIDDEN_DIRS, COMMON_EXTENSIONLESS_FILES

ANNOTATION_MARKERS = ("\u2190", "\u2192", "<-", "->", "#")


def strip_tree_annotations(name: str) -> str:
    positions = [name.find(marker) for marker in ANNOTATION_MARKERS]
    positions = [pos for pos in positions if pos != -1]
    if positions:
        name = name[: min(positions)]
    return name.strip()


def parse_tree_line(raw_line: str, line_no: int) -> ParsedLine | None:
    line = strip_ansi(raw_line).rstrip()

    if not line.strip():
        return None

    stripped = line.strip()

    if stripped.startswith("#"):
        return None

    if TREE_SKIP_RE.match(stripped):
        return None

    branch_match = TREE_BRANCH_RE.search(line)

    if branch_match:
        prefix = line[:branch_match.start()].expandtabs(4)
        depth = len(prefix) // 4
        name = strip_tree_annotations(line[branch_match.end():])

        if not name:
            return None

        if name.startswith("(") and name.endswith(")"):
            return None

        return ParsedLine(
            line_no=line_no,
            raw=raw_line,
            depth=depth,
            name=name,
            has_branch=True,
        )

    expanded = line.expandtabs(4)
    leading_spaces = len(expanded) - len(expanded.lstrip(" "))
    depth = leading_spaces // 4
    name = strip_tree_annotations(expanded.strip())

    if not name:
        return None

    if name.startswith("(") and name.endswith(")"):
        return None

    return ParsedLine(
        line_no=line_no,
        raw=raw_line,
        depth=depth,
        name=name,
        has_branch=False,
    )


def parse_all_tree_lines(text_or_lines) -> list[ParsedLine]:
    if isinstance(text_or_lines, str):
        lines = text_or_lines.splitlines()
    else:
        lines = text_or_lines

    parsed: list[ParsedLine] = []

    for index, line in enumerate(lines, start=1):
        item = parse_tree_line(line, index)
        if item is not None:
            parsed.append(item)

    return parsed


def parse_creation_lines(lines: list[str], include_first_root: bool) -> tuple[list[ParsedLine], list[str]]:
    warnings: list[str] = []
    parsed = parse_all_tree_lines(lines)

    if not parsed:
        return [], warnings

    first = parsed[0]
    first_name = first.name.strip()

    if first_name in {".", "./"}:
        warnings.append(
            f"Line {first.line_no}: skipped root marker {first_name!r}; selected root directory is used instead."
        )
        return parsed[1:], warnings

    looks_like_tree_root = (
        len(parsed) > 1
        and not first.has_branch
        and parsed[1].has_branch
        and parsed[1].depth == 0
    )

    if looks_like_tree_root:
        if include_first_root:
            for item in parsed[1:]:
                item.depth += 1
            warnings.append(f"Line {first.line_no}: using {first.name!r} as top-level folder.")
        else:
            warnings.append(
                f"Line {first.line_no}: skipped apparent tree root header {first.name!r}."
            )
            parsed = parsed[1:]

    return parsed, warnings


def infer_is_directory(clean_name: str, explicit_dir: bool, has_children: bool, policy: str) -> bool:
    if explicit_dir:
        return True

    if has_children:
        return True

    lower = clean_name.lower()

    if lower in {item.lower() for item in COMMON_HIDDEN_DIRS}:
        return True

    if lower in {item.lower() for item in COMMON_EXTENSIONLESS_FILES}:
        return False

    _, extension = os.path.splitext(clean_name)

    if extension:
        return False

    if policy == "Extensionless items are files":
        return False

    return True


def parse_tree_to_paths(tree_text: str) -> tuple[str, set[tuple[str, bool]], list[str]]:
    warnings: list[str] = []
    parsed = parse_all_tree_lines(tree_text)

    if not parsed:
        return "", set(), ["No parseable tree lines found."]

    root_name = parsed[0].name.rstrip("/\\").strip()
    nodes = parsed[1:]

    paths: set[tuple[str, bool]] = set()
    stack: list[tuple[int, str]] = []

    for index, item in enumerate(nodes):
        has_children = index + 1 < len(nodes) and nodes[index + 1].depth > item.depth

        raw_name = item.name.strip()
        explicit_dir = raw_name.endswith(("/", "\\"))
        raw_name = raw_name.rstrip("/\\").strip()

        if not raw_name:
            warnings.append(f"Line {item.line_no}: skipped empty item.")
            continue

        while stack and item.depth <= stack[-1][0]:
            stack.pop()

        rel_parts = [part for _, part in stack] + [raw_name]
        rel_path = "/".join(rel_parts)

        is_dir = explicit_dir or has_children

        paths.add((rel_path, is_dir))

        if is_dir:
            stack.append((item.depth, raw_name))

    return root_name, paths, warnings


def compare_trees(original_tree: str, edited_tree: str) -> dict:
    original_root, original_paths, original_warnings = parse_tree_to_paths(original_tree)
    edited_root, edited_paths, edited_warnings = parse_tree_to_paths(edited_tree)

    warnings = original_warnings + edited_warnings

    if original_root and edited_root and original_root != edited_root:
        warnings.append(
            f"Root rename detected: {original_root!r} -> {edited_root!r}. "
            "Sync keeps the original scanned directory path and does not rename the root folder."
        )

    raw_removed = original_paths - edited_paths
    raw_added = edited_paths - original_paths
    unchanged = original_paths & edited_paths

    removed, added, renames = detect_renames(raw_removed, raw_added)

    if renames:
        warnings.append(
            f"Detected {len(renames)} rename(s). "
            "Sync will move these rather than delete and recreate."
        )

    return {
        "original_root": original_root,
        "edited_root": edited_root,
        "root_changed": bool(original_root and edited_root and original_root != edited_root),
        "added": sorted(added, key=lambda item: item[0]),
        "removed": sorted(removed, key=lambda item: item[0]),
        "renamed": renames,
        "unchanged": sorted(unchanged, key=lambda item: item[0]),
        "warnings": warnings,
    }


def detect_renames(removed: set, added: set) -> tuple[set, set, list]:
    renames = []
    still_removed = set(removed)
    still_added = set(added)

    removed_by_key = {}
    for path, is_dir in removed:
        parent = "/".join(path.split("/")[:-1])
        key = (parent, is_dir)
        removed_by_key.setdefault(key, []).append(path)

    added_by_key = {}
    for path, is_dir in added:
        parent = "/".join(path.split("/")[:-1])
        key = (parent, is_dir)
        added_by_key.setdefault(key, []).append(path)

    for key, removed_paths in removed_by_key.items():
        if key not in added_by_key:
            continue
        added_paths = added_by_key[key]
        for old_path, new_path in zip(sorted(removed_paths), sorted(added_paths)):
            renames.append((old_path, new_path, key[1]))
            still_removed.discard((old_path, key[1]))
            still_added.discard((new_path, key[1]))

    return still_removed, still_added, renames
