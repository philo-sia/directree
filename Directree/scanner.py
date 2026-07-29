import os

from Directree.constants import SKIP_DIRECTORIES


def scan_directory_to_tree(root_path: str, show_hidden: bool = False, max_depth: int | None = None):
    lines: list[str] = []
    warnings: list[str] = []

    root_path = os.path.abspath(root_path)
    root_name = os.path.basename(root_path) or root_path
    lines.append(f"{root_name}/")

    stats = {
        "directories": 1,
        "files": 0,
        "skipped": 0,
        "warnings": 0,
    }

    def should_skip(name: str, hidden: bool) -> bool:
        if name in SKIP_DIRECTORIES:
            return True

        if hidden and not show_hidden:
            return True

        return False

    def scan_recursive(path: str, prefix: str = "", depth: int = 0):
        if max_depth is not None and depth >= max_depth:
            return

        try:
            entries = list(os.scandir(path))
        except PermissionError:
            warnings.append(f"Permission denied: {path}")
            stats["warnings"] += 1
            return
        except OSError as exc:
            warnings.append(f"Could not read {path}: {exc}")
            stats["warnings"] += 1
            return

        dirs = []
        files = []

        for entry in sorted(entries, key=lambda item: item.name.lower()):
            hidden = entry.name.startswith(".")

            if should_skip(entry.name, hidden):
                stats["skipped"] += 1
                continue

            if entry.is_symlink():
                warnings.append(f"Skipped symlink: {entry.path}")
                stats["skipped"] += 1
                continue

            try:
                if entry.is_dir(follow_symlinks=False):
                    dirs.append(entry)
                else:
                    files.append(entry)
            except OSError as exc:
                warnings.append(f"Skipped unreadable entry {entry.path}: {exc}")
                stats["skipped"] += 1

        all_entries = dirs + files

        for index, entry in enumerate(all_entries):
            is_last = index == len(all_entries) - 1
            connector = "└── " if is_last else "├── "
            extension = "    " if is_last else "│   "

            is_dir = entry in dirs
            display_name = f"{entry.name}/" if is_dir else entry.name
            lines.append(f"{prefix}{connector}{display_name}")

            if is_dir:
                stats["directories"] += 1
                scan_recursive(entry.path, prefix + extension, depth + 1)
            else:
                stats["files"] += 1

    scan_recursive(root_path)

    return "\n".join(lines), stats, warnings
