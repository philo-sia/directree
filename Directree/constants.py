import sys
import os
import re

DEFAULT_FONT_SIZE = 14
IMAGE_PADDING = 20
TEXT_COLOR = "black"
BUNDLED_FONT = "DejaVuSansMono.ttf"

MAX_PREVIEW_DIMENSION = 4096
MAX_PAGE_HEIGHT = 16384

FALLBACK_FONTS = [
    "Consolas",
    "Courier New",
    "Menlo",
    "Monaco",
    "DejaVu Sans Mono",
    "monospace",
]

SUPPORTED_FONTS = [
    "DejaVu Sans Mono",
    "Consolas",
    "Courier New",
    "Menlo",
    "Monaco",
    "Arial",
    "Times New Roman",
]

FONT_FILENAME_MAP = {
    "consolas": "consola.ttf",
    "courier new": "cour.ttf",
    "arial": "arial.ttf",
    "times new roman": "times.ttf",
}

SKIP_DIRECTORIES = {
    "__pycache__", "node_modules", ".git", ".svn", ".hg",
    "venv", "env", ".venv", "dist", "build", ".eggs",
    ".idea", ".vscode", ".vs", "bin", "obj", ".tox",
    "eggs", ".mypy_cache", ".pytest_cache", ".coverage",
    "htmlcov", ".sass-cache", "bower_components",
}

COMMON_EXTENSIONLESS_FILES = {
    "Makefile", "Dockerfile", "LICENSE", "LICENCE", "README", "CHANGELOG",
    "Procfile", "Gemfile", "Rakefile", "Vagrantfile", "CODEOWNERS",
    "AUTHORS", "MANIFEST", "Brewfile", "Justfile", "CMakeLists",
    "COPYING", "NOTICE", ".gitignore", ".gitattributes", ".dockerignore",
    ".editorconfig", ".env", ".env.example", ".npmrc", ".nvmrc",
    ".python-version",
}

COMMON_HIDDEN_DIRS = {
    ".github", ".gitlab", ".vscode", ".idea", ".config", ".cache", ".venv",
    ".git",
}

WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}

INVALID_CHARS_RE = re.compile(r'[<>:"/\\|?*\x00-\x1F]')
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

TREE_SKIP_RE = re.compile(
    r"^(folder path listing|volume serial number|directory path listing|"
    r"\d+\s+directories?,\s+\d+\s+files?|"
    r"\d+\s+dirs?,\s+\d+\s+files?|"
    r"[-\s]+)$",
    re.IGNORECASE,
)

TREE_BRANCH_RE = re.compile(
    r"(?P<branch>(?:├|└|╞|╘|╠|╚)[─═-]{2,}|(?:\+|\\|`|\|)-{2,3})"
)

_MONOSPACE_FONTS = {
    "DejaVu Sans Mono", "Consolas", "Courier New", "Menlo", "Monaco",
}
