# DirecTree User Manual

**Version 8.0** | Directory Structure Creator with Bidirectional Sync & Rename Detection

---

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Main Interface](#main-interface)
5. [Features](#features)
   - [Creating Directory Structures](#creating-directory-structures)
   - [Scanning Existing Directories](#scanning-existing-directories)
   - [Bidirectional Sync](#bidirectional-sync)
   - [Exporting as Image](#exporting-as-image)
6. [Tree Syntax Reference](#tree-syntax-reference)
7. [Keyboard Shortcuts](#keyboard-shortcuts)
8. [Troubleshooting](#troubleshooting)
9. [FAQ](#faq)

---

## Overview

DirecTree is a desktop application for creating, visualizing, and synchronizing directory structures using ASCII tree notation. It enables you to:

- **Create** folder and file structures from ASCII tree diagrams
- **Scan** existing directories to generate tree representations
- **Sync** changes between edited trees and the actual filesystem — with **rename detection** that moves files/folders instead of deleting and recreating
- **Export** tree diagrams as PNG or JPEG images (multi-page for tall trees)

### Use Cases

- Scaffolding new projects from templates
- Documenting existing project structures
- Refactoring directory layouts
- Creating visual documentation for README files

---

## Installation

### Requirements

- Python 3.8 or higher
- PySide6 (`pip install PySide6`)

### Setup

1. Copy the entire `Directree/` package folder and `launch.pyw` to your desired location
2. (Optional) Place `DejaVuSansMono.ttf` in the same directory for best font rendering
3. Run with: `python launch.pyw` or `python -m Directree`

---

## Quick Start

### Creating a New Project Structure

1. Paste or type a tree structure in the editor:
   ```
   my-project/
   ├── src/
   │   ├── main.py
   │   └── utils.py
   ├── tests/
   │   └── test_main.py
   └── README.md
   ```
2. Click **Select Root Directory** to choose where to create the structure
3. Click **Create Directory Structure**
4. Confirm the action

### Scanning and Editing an Existing Directory

1. Switch to the **Scan Folder** tab and browse for a folder
2. Configure options (hidden files, depth)
3. Click **Generate Tree** — the tree auto-loads into the editor and switches to it
4. Edit the tree in the **Edit & Create** tab
5. Click **🔄 Sync Changes** to apply modifications (renamed items are moved, not deleted)

---

## Main Interface

The app uses a **tabbed interface** with 4 tabs:

| Tab | Content |
|-----|---------|
| **✏ Edit & Create** | Tree editor, root selector, create/sync/undo buttons |
| **🖼 Save Image** | Live preview, settings, and save controls for image export |
| **📂 Scan Folder** | Browse & scan directories with configurable options |
| **📋 Log** | Persistent action history log |

### Edit & Create Tab

```
┌─────────────────────────────────────────────────────────────┐
│  [⇩ Import] [✖ Clear] [⎘ Copy]                 [MODE LABEL] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   (Tree Editor Area)                                        │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  [ ] Include first root line    Extensionless names: [Smart ▾] │
├─────────────────────────────────────────────────────────────┤
│  [📂 Select Root Directory]  Root: /path/to/dir              │
├─────────────────────────────────────────────────────────────┤
│  [🔍 Preview Plan] [▶ Create Structure] [🔄 Sync Changes]    │
│  [✖ Cancel Sync]                              [↩ Undo]      │
├─────────────────────────────────────────────────────────────┤
│  Status: Ready                                              │
└─────────────────────────────────────────────────────────────┘
```

### Tab Bar

| Button | Description |
|--------|-------------|
| **☽/☀** | Toggles between dark and light theme (top-right corner) |

### Action Buttons (Edit & Create tab)

| Button | Description |
|--------|-------------|
| **Clear** / **✖ Clear** | Clears the editor and exits sync mode |
| **Import Folder** / **⇩ Import** | Opens the Scan Folder tab |
| **Copy** / **⎘ Copy** | Copies tree text to system clipboard |
| **Preview Plan** / **🔍 Preview Plan** | Shows what would be created |
| **Create Structure** / **▶ Create Structure** | Creates folders/files from tree (normal mode) |
| **Sync Changes** / **🔄 Sync Changes** | Applies edits to filesystem (sync mode) |
| **Cancel Sync** / **✖ Cancel Sync** | Exits sync mode without applying changes |
| **Undo Last Creation** / **↩ Undo** | Removes the last created items |

---

## Features

### Creating Directory Structures

1. Enter a tree structure in the text editor using ASCII notation
2. Select your target root directory
3. Click **Create Directory Structure**
4. Review the confirmation dialog
5. The app creates all folders and files

**File vs Directory Detection:**

| Pattern | Interpreted As |
|---------|----------------|
| `name/` or `name\` | Directory (explicit) |
| `file.txt`, `script.py` | File (has extension) |
| `.gitignore`, `.env` | File (dotfile) |
| `Makefile`, `Dockerfile` | File (known extensionless) |
| `utils`, `components` | Directory (no extension) |

### Scanning Existing Directories

The **Scan Folder** tab allows you to import existing folder structures:

1. Switch to the **Scan Folder** tab
2. Click **Browse…** to select a directory
3. Configure scan options:
   - **Include hidden**: Show files/folders starting with `.` (e.g., `.gitignore`, `.env`)
   - **Max depth**: Limit recursion depth (0 = unlimited)
4. Click **Generate Tree** — the tree auto-loads into the editor and switches to it

**Auto-Filtered Directories:**

The scanner automatically excludes common build/cache directories:
- `__pycache__`, `node_modules`, `.git`, `.svn`
- `venv`, `env`, `.venv`, `dist`, `build`
- `.idea`, `.vscode`, `.vs`, `.mypy_cache`
- `bower_components`, `.sass-cache`, `.tox`

### Bidirectional Sync with Rename Detection

After scanning a directory, the app enters **Sync Mode**, allowing you to edit the tree and apply changes to the actual filesystem.

**Sync Mode Workflow:**

1. Scan a directory (automatically enters sync mode)
2. Edit the tree:
   - Add lines to create new files/folders
   - Delete lines to remove items
   - **Rename** items by changing their name in the tree
3. Click **🔄 Sync Changes**
4. Review the change summary:
   - **Added**: Items to be created
   - **Removed**: Items to be deleted
   - **Renamed**: Items that will be **moved** (not deleted/recreated)
5. Confirm to apply changes

**Rename Detection:**

When a file or folder is renamed within the same parent directory, DirecTree detects this as a **rename** and uses `shutil.move()` instead of delete+create. This preserves:

- File contents and metadata
- All children inside a renamed directory

Renames are shown in orange in the Sync dialog with an `->` arrow. The pairing heuristic matches items at the same depth in the same parent directory, sorted alphabetically.

**Mode Indicators:**

| Label | Meaning |
|-------|---------|
| SYNC — *name* | Sync mode active, ready to edit |
| MODIFIED | Changes detected, ready to sync |

**Warning:** Removed items are permanently deleted from disk!

### Exporting as Image

Create visual representations of your tree structures:

1. Switch to the **Save Image** tab
2. Configure settings:
   - **Scale**: 50% - 500%
   - **Bottom padding**: Padding below content
   - **Font**: DejaVu Sans Mono, Consolas, etc.
   - **Background**: White, gray, black, navy
   - **Text color**: Black, white, colors
3. Preview updates automatically (short debounce delay)
4. Navigate multi-page trees with **◀ Prev / Next ▶**
5. Click **Save PNG** or **Save JPEG**

**Multi-page support:** Trees taller than ~16,000px are split into multiple page files (`name_1.png`, `name_2.png`, …) to ensure compatibility with common image viewers.

---

## Tree Syntax Reference

### Basic Structure

```
project/
├── folder/
│   ├── file.txt
│   └── another.py
└── root-file.md
```

### Supported Tree Characters

| Character | Unicode | Usage |
|-----------|---------|-------|
| `├` | U+251C | Branch connector |
| `└` | U+2514 | Last item connector |
| `│` | U+2502 | Vertical line |
| `─` | U+2500 | Horizontal line |

**ASCII Alternatives:** `+`, `-`, `|`, `` ` `` (backtick)

### Comments and Placeholders

```
project/
├── src/
│   └── main.py  # Entry point
├── (additional files here)
└── README.md
```

- Text after `#` is treated as a comment (ignored)
- Lines in parentheses `(...)` are skipped

### Known Extensionless Files

These are automatically recognized as files:

```
Makefile, Dockerfile, LICENSE, README, CHANGELOG,
Procfile, Gemfile, Rakefile, Vagrantfile, CODEOWNERS,
AUTHORS, MANIFEST, Brewfile, Justfile, CMakeLists
```

---

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Create directory structure | **Ctrl+Enter** |
| Preview create plan | **Ctrl+Shift+P** |
| Open Save Image tab | **Ctrl+Shift+I** |
| Open Scan Folder tab | **Ctrl+Shift+O** |
| Undo last creation | **Ctrl+Shift+Z** |
| Open Log tab | **Ctrl+Shift+L** |
| Select all text | Ctrl+A |
| Copy | Ctrl+C |
| Paste | Ctrl+V |
| Cut | Ctrl+X |
| Undo (text) | Ctrl+Z |
| Redo (text) | Ctrl+Y |

---

## Troubleshooting

### Tree Not Parsing Correctly

**Problem:** Files created as directories or vice versa

**Solutions:**
- Add explicit `/` suffix for directories: `components/`
- Add extension for files: `config.json`
- Use `[f]` or `[d]` prefixes in comments

### Hidden Files Not Appearing in Scan

**Problem:** `.gitignore`, `.env` not showing

**Solution:** Check the **Include hidden files** checkbox in the Scan Directory dialog before generating the tree.

### Sync Shows No Changes

**Problem:** Edits not detected

**Solutions:**
- Ensure you're modifying the structure (not just whitespace)
- Check that items have proper indentation
- Directory names must end with `/`

### Dark / Light Theme

Toggle the theme by clicking the **☽** (moon) or **☀** (sun) icon in the top-right corner of the tab bar. The app starts in dark mode by default.

### Font Rendering Issues

**Problem:** Tree characters appear as boxes

**Solutions:**
- Place `DejaVuSansMono.ttf` in the same directory as the script
- Select a different font in the Save Image tab
- Install a monospace font with Unicode support

### Permission Denied Errors

**Problem:** Cannot create files in target directory

**Solutions:**
- Run the application with appropriate permissions
- Choose a different root directory
- Check folder write permissions

---

## FAQ

**Q: Can I use output from the `tree` command?**

A: Yes! TreeMaker fully supports the standard `tree` command output format.

**Q: Will sync delete files with content?**

A: Yes. When you remove a line and sync, the corresponding file/folder is permanently deleted, including all contents. Always review the sync dialog carefully.

**Q: Can I sync to a different directory than I scanned?**

A: The sync operation works relative to the scanned directory's parent. Changing the root directory may cause unexpected behavior in sync mode.

**Q: How do I create an empty file vs directory?**

A: Files need either an extension (`data.txt`), a dot prefix (`.env`), or be in the known files list. Everything else becomes a directory. Use explicit `/` for directories.

**Q: Can I undo a sync operation?**

A: Only **created** items can be undone. Deleted items cannot be recovered. Consider backing up before major sync operations.

**Q: What's the maximum tree depth?**

A: There's no hard limit, but very deep structures (50+ levels) may impact performance. Use the Max depth setting when scanning to limit recursion.

---

## Version History

| Version | Changes |
|---------|---------|
| 9.0 | Refactored into modular `Directree/` package: split into 14 modules (constants, models, theme, utils, tree_parser, image_renderer, scanner, sync_dialog, edit_tab, image_tab, scan_tab, log_tab, app, \_\_main\_\_). Launcher renamed to `launch.pyw`. |
| 8.0 | Tabbed interface, dark/light theme, QPainter image rendering with multi-page support, drag-and-drop import, keyboard shortcuts, rename detection in sync, inline `#` comment stripping restored, `(...)` placeholder skipping restored, `root_dir` no longer overwritten on scan |
| 7.0 | Added bidirectional sync, fixed hidden files checkbox, added Copy to Clipboard in scanner |
| 6.0 | Initial release with PySide6, image export, undo support |

---

## License

TreeMaker is provided as-is for personal and commercial use.

---

*Generated: July 2026 — v9.0*
