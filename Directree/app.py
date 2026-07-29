import os
import shutil
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QLabel,
    QPlainTextEdit, QPushButton, QFileDialog, QMessageBox,
    QDialog, QDialogButtonBox, QVBoxLayout,
)
from PySide6.QtGui import QFontDatabase, QShortcut, QKeySequence
from PySide6.QtCore import Qt

from Directree.constants import DEFAULT_FONT_SIZE, MAX_PREVIEW_DIMENSION
from Directree.models import OperationResult, ParsedLine
from Directree.theme import apply_global_theme, toggle_global_theme
from Directree.utils import (
    app_base_dir, safe_join_under_root, safe_resolve_relative_path,
    sanitize_name,
)
from Directree.tree_parser import parse_creation_lines, compare_trees, infer_is_directory
from Directree.scanner import scan_directory_to_tree
from Directree.sync_dialog import SyncDialog
from Directree.edit_tab import EditTab
from Directree.image_tab import ImageTab
from Directree.scan_tab import ScanTab
from Directree.log_tab import LogTab


class DirecTreeApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DirecTree \u2014 Directory Structure Creator")
        self.setGeometry(100, 100, 1020, 740)

        self.root_dir = app_base_dir()
        self.undo_stack: list[OperationResult] = []
        self.action_log: list[str] = []
        self.original_tree: str | None = None
        self.sync_mode = False
        self.sync_root_path: str | None = None
        self.sync_root_name: str | None = None

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.edit_tab = EditTab()
        self.image_tab = ImageTab()
        self.scan_tab = ScanTab()
        self.log_tab = LogTab()

        self.tabs.addTab(self.edit_tab, "\u270f  Edit & Create")
        self.tabs.addTab(self.image_tab, "\U0001f5bc  Save Image")
        self.tabs.addTab(self.scan_tab, "\U0001f4c2  Scan Folder")
        self.tabs.addTab(self.log_tab, "\U0001f4cb  Log")

        self.tabs.currentChanged.connect(self._on_tab_changed)

        self.theme_btn = QPushButton("\u263d")
        self.theme_btn.setProperty("flat", True)
        self.theme_btn.setToolTip("Toggle dark / light theme")
        self.theme_btn.setFixedSize(28, 28)
        self.theme_btn.clicked.connect(self._toggle_theme)
        self.tabs.setCornerWidget(self.theme_btn, Qt.Corner.TopRightCorner)

        self.edit_tab.edit.textChanged.connect(self.image_tab.schedule_preview)

        self.edit_tab.refresh_root_lbl(self.root_dir)

        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
        self.status_lbl = QLabel("Ready")
        self.status_bar.addWidget(self.status_lbl, 1)

        self._stats_lbl = QLabel("")
        self.status_bar.addPermanentWidget(self._stats_lbl)

        self._setup_shortcuts()
        self._setup_drag_drop()

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+Return"), self, self.create_dirs)
        QShortcut(QKeySequence("Ctrl+Shift+P"), self, self.preview_create_plan)
        QShortcut(QKeySequence("Ctrl+Shift+I"), self, self._open_image_tab)
        QShortcut(QKeySequence("Ctrl+Shift+O"), self, self._open_scan_tab)
        QShortcut(QKeySequence("Ctrl+Shift+Z"), self, self.undo_last)
        QShortcut(QKeySequence("Ctrl+Shift+L"), self, self._open_log_tab)

    def _open_image_tab(self):
        self.tabs.setCurrentIndex(1)
        self.image_tab.schedule_preview()

    def _open_scan_tab(self):
        self.tabs.setCurrentIndex(2)

    def _open_log_tab(self):
        self.tabs.setCurrentIndex(3)
        self.log_tab.refresh()

    def _toggle_theme(self):
        new = toggle_global_theme(QApplication.instance())
        self.theme_btn.setText("\u2600" if new == "dark" else "\u263d")

    def _setup_drag_drop(self):
        self.edit_tab.edit.setAcceptDrops(True)

        orig_drag_enter = self.edit_tab.edit.dragEnterEvent
        orig_drop = self.edit_tab.edit.dropEvent

        def on_drag_enter(event):
            if event.mimeData().hasUrls():
                event.acceptProposedAction()
            else:
                orig_drag_enter(event)

        def on_drop(event):
            urls = event.mimeData().urls()
            if urls:
                path = urls[0].toLocalFile()
                if os.path.isdir(path):
                    self._scan_and_import(path)
                    return
            orig_drop(event)

        self.edit_tab.edit.dragEnterEvent = on_drag_enter
        self.edit_tab.edit.dropEvent = on_drop

    def _scan_and_import(self, path: str):
        tree, stats, _warnings = scan_directory_to_tree(path)
        self.edit_tab.edit.setPlainText(tree)
        self.original_tree = tree
        self.sync_mode = True
        self.sync_root_path = os.path.abspath(path)
        self.sync_root_name = os.path.basename(self.sync_root_path)
        self.edit_tab.enter_sync_mode(self.sync_root_name)
        self.log("--- Action: Drag-drop scan ---")
        self.log(f"Scanned: {self.sync_root_path}")
        self.status_bar.showMessage(f"Imported {stats['directories']} dirs, {stats['files']} files")

    def _on_tab_changed(self, index: int):
        if index == 1:
            self.image_tab.schedule_preview()
        elif index == 3:
            self.log_tab.refresh()

    def clear_input(self):
        if self.edit_tab.edit.toPlainText().strip():
            answer = QMessageBox.question(
                self, "Clear Input",
                "Clear the current input and leave sync mode?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return

        self.edit_tab.edit.clear()
        self.original_tree = None
        self.sync_mode = False
        self.sync_root_path = None
        self.sync_root_name = None
        self.edit_tab.leave_sync_mode()
        self.status_bar.showMessage("Input cleared")

    def cancel_sync(self):
        self.original_tree = None
        self.sync_mode = False
        self.sync_root_path = None
        self.sync_root_name = None
        self.edit_tab.leave_sync_mode()
        self.status_bar.showMessage("Sync cancelled")

    def pick_root(self):
        selected = QFileDialog.getExistingDirectory(self, "Select Root Directory", self.root_dir)
        if selected:
            self.root_dir = selected
            self.edit_tab.refresh_root_lbl(self.root_dir)
            self.status_bar.showMessage("Root directory set")

    def copy_to_clipboard(self):
        text = self.edit_tab.edit.toPlainText()
        if not text.strip():
            QMessageBox.warning(self, "Empty", "Nothing to copy.")
            return
        QApplication.clipboard().setText(text)
        self.status_bar.showMessage("Copied to clipboard")

    def current_extensionless_policy(self) -> str:
        text = self.edit_tab.kind_combo.currentText()
        if text == "Extensionless items are folders":
            return text
        if text == "Extensionless items are files":
            return text
        return "Smart detection"

    def preview_create_plan(self):
        text = self.edit_tab.edit.toPlainText()
        if not text.strip():
            QMessageBox.warning(self, "Input Empty", "Please provide a directory structure.")
            return

        result = self._process_structure(text.splitlines(), self.root_dir, dry_run=True)
        self.show_result_dialog("Preview Create Plan", result, planned=True)

    def create_dirs(self):
        text = self.edit_tab.edit.toPlainText()
        if not text.strip():
            QMessageBox.warning(self, "Input Empty", "Please provide a directory structure.")
            return

        plan = self._process_structure(text.splitlines(), self.root_dir, dry_run=True)

        if plan.has_errors:
            self.show_result_dialog("Validation Errors", plan, planned=True)
            self.status_bar.showMessage("Creation blocked \u2014 validation errors")
            return

        if plan.total_created == 0:
            self.show_result_dialog("Nothing New To Create", plan, planned=True)
            self.status_bar.showMessage("Nothing new to create")
            return

        message = (
            f"Create structure under:\n{os.path.abspath(self.root_dir)}\n\n"
            f"New directories: {len(plan.created_dirs)}\n"
            f"New files: {len(plan.created_files)}\n"
            f"Skipped existing: {len(plan.skipped)}\n"
            f"Warnings: {len(plan.warnings)}\n\n"
            "Existing files will not be overwritten.\n"
            "Undo will remove only newly-created items."
        )

        answer = QMessageBox.question(
            self, "Confirm Creation", message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            self.status_bar.showMessage("Creation cancelled")
            return

        actual = self._process_structure(text.splitlines(), self.root_dir, dry_run=False)

        if actual.total_created:
            self.undo_stack.append(actual)
            self.edit_tab.set_undo_enabled(True)

        self.log(f"--- Action: Create at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
        self.log_operation(actual)

        if actual.errors:
            self.show_result_dialog("Creation Completed With Errors", actual, planned=False)

        self._update_stats_display(actual)
        self.status_bar.showMessage(
            f"Created {actual.total_created} item(s); skipped {len(actual.skipped)}; errors {len(actual.errors)}"
        )

    def _process_structure(self, lines: list[str], root: str, dry_run: bool) -> OperationResult:
        result = OperationResult()
        root_abs = os.path.abspath(root)

        if not os.path.isdir(root_abs):
            result.errors.append(f"Root directory does not exist: {root_abs}")
            return result

        parsed, warnings = parse_creation_lines(
            lines,
            include_first_root=self.edit_tab.include_root_check.isChecked(),
        )
        result.warnings.extend(warnings)

        if not parsed:
            result.warnings.append("No usable structure lines were found.")
            return result

        policy = self.current_extensionless_policy()

        stack: list[dict] = [{"depth": -1, "path": root_abs}]
        planned_dirs: set[str] = set()

        for index, item in enumerate(parsed):
            has_children = index + 1 < len(parsed) and parsed[index + 1].depth > item.depth

            raw_name = item.name.strip()
            if "#" in raw_name:
                raw_name = raw_name.split("#", 1)[0].rstrip()
            clean_name, explicit_dir, name_warnings, error = sanitize_name(raw_name)
            for warn in name_warnings:
                result.warnings.append(f"Line {item.line_no}: {warn}")

            inferred_dir = (
                infer_is_directory(clean_name, explicit_dir, has_children, policy)
                if not error else (has_children or explicit_dir)
            )

            while stack and item.depth <= int(stack[-1]["depth"]):
                stack.pop()
            if not stack:
                stack = [{"depth": -1, "path": root_abs}]

            parent = stack[-1]["path"]

            if error:
                result.errors.append(f"Line {item.line_no}: {error}")
                if inferred_dir:
                    stack.append({"depth": item.depth, "path": None})
                continue

            if parent is None:
                result.skipped.append(f"Line {item.line_no}: skipped {item.name!r} (invalid parent)")
                if inferred_dir:
                    stack.append({"depth": item.depth, "path": None})
                continue

            full_path, path_error = safe_join_under_root(root=root_abs, parent=str(parent), name=clean_name)

            if path_error or full_path is None:
                result.errors.append(f"Line {item.line_no}: {path_error}")
                if inferred_dir:
                    stack.append({"depth": item.depth, "path": None})
                continue

            if inferred_dir:
                self._handle_directory(result, full_path, item, stack, planned_dirs, dry_run)
            else:
                self._handle_file(result, full_path, str(parent), item, planned_dirs, dry_run)

        return result

    def _handle_directory(self, result, full_path, item, stack, planned_dirs, dry_run):
        if os.path.exists(full_path):
            if os.path.isdir(full_path):
                result.skipped.append(f"Line {item.line_no}: already exists: {full_path}")
                stack.append({"depth": item.depth, "path": full_path})
            else:
                result.errors.append(f"Line {item.line_no}: file blocks dir: {full_path}")
                stack.append({"depth": item.depth, "path": None})
            return
        if dry_run:
            result.created_dirs.append(full_path)
            planned_dirs.add(full_path)
            stack.append({"depth": item.depth, "path": full_path})
            return
        try:
            os.mkdir(full_path)
            result.created_dirs.append(full_path)
            stack.append({"depth": item.depth, "path": full_path})
        except OSError as exc:
            result.errors.append(f"Line {item.line_no}: mkdir failed: {full_path}: {exc}")
            stack.append({"depth": item.depth, "path": None})

    def _handle_file(self, result, full_path, parent, item, planned_dirs, dry_run):
        parent_ready = os.path.isdir(parent) or parent in planned_dirs
        if not parent_ready:
            result.errors.append(f"Line {item.line_no}: parent missing: {parent}")
            return
        if os.path.exists(full_path):
            if os.path.isfile(full_path):
                result.skipped.append(f"Line {item.line_no}: already exists: {full_path}")
            else:
                result.errors.append(f"Line {item.line_no}: dir blocks file: {full_path}")
            return
        if dry_run:
            result.created_files.append(full_path)
            return
        try:
            with open(full_path, "x", encoding="utf-8"):
                pass
            result.created_files.append(full_path)
        except OSError as exc:
            result.errors.append(f"Line {item.line_no}: create file failed: {full_path}: {exc}")

    def sync_changes(self):
        if not self.sync_mode or not self.original_tree or not self.sync_root_path:
            QMessageBox.warning(self, "Not in Sync Mode",
                "Sync is available after scanning a directory.")
            return

        current_tree = self.edit_tab.edit.toPlainText().strip()
        if not current_tree:
            QMessageBox.warning(self, "Empty Input", "No tree structure to sync.")
            return

        changes = compare_trees(self.original_tree, current_tree)

        if changes["root_changed"]:
            QMessageBox.warning(self, "Root Rename Not Supported",
                "The root line was changed. Sync does not rename the scanned root folder.\n"
                "Restore the original root line or rename the folder manually.")
            return

        if not changes["added"] and not changes["removed"]:
            QMessageBox.information(self, "No Changes", "No changes detected.")
            return

        dialog = SyncDialog(changes, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            self.status_bar.showMessage("Sync cancelled")
            return

        result = self._apply_sync_changes(changes)

        self.log(f"--- Action: Sync at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
        self.log_operation(result)

        if result.total_created:
            self.undo_stack.append(result)
            self.edit_tab.set_undo_enabled(True)

        if result.errors or result.warnings:
            self.show_result_dialog("Sync Result", result, planned=False)

        if not result.errors:
            self.original_tree = current_tree
            self.edit_tab.enter_sync_mode(self.sync_root_name or "")

        self._update_stats_display(result)
        self.status_bar.showMessage(
            f"Sync: created {result.total_created}, deleted {result.total_deleted}, "
            f"skipped {len(result.skipped)}, errors {len(result.errors)}"
        )

    def _apply_sync_changes(self, changes: dict) -> OperationResult:
        result = OperationResult()
        if not self.sync_root_path:
            result.errors.append("Internal: missing sync root path")
            return result

        sync_root = os.path.abspath(self.sync_root_path)

        renames_sorted = sorted(
            changes.get("renamed", []),
            key=lambda item: item[0].count("/"),
        )

        for old_rel, new_rel, is_dir in renames_sorted:
            old_full, ow, oe = safe_resolve_relative_path(sync_root, old_rel)
            result.warnings.extend(ow)
            if oe or old_full is None:
                result.errors.append(f"Cannot resolve rename source {old_rel!r}: {oe}")
                continue

            new_full, nw, ne = safe_resolve_relative_path(sync_root, new_rel)
            result.warnings.extend(nw)
            if ne or new_full is None:
                result.errors.append(f"Cannot resolve rename target {new_rel!r}: {ne}")
                continue

            if not os.path.exists(old_full):
                result.skipped.append(f"Rename source already gone: {old_full}")
                continue

            if os.path.exists(new_full):
                result.errors.append(
                    f"Cannot rename {old_full} to {new_full}: target already exists."
                )
                continue

            try:
                shutil.move(old_full, new_full)
                if is_dir:
                    result.created_dirs.append(new_full)
                    result.deleted_dirs.append(old_full)
                else:
                    result.created_files.append(new_full)
                    result.deleted_files.append(old_full)
                result.renamed.append((old_rel, new_rel, is_dir))
            except OSError as exc:
                result.errors.append(f"Failed to rename {old_full} to {new_full}: {exc}")

        for rel_path, is_dir in sorted(changes["removed"], key=lambda x: x[0].count("/"), reverse=True):
            full_path, warnings, error = safe_resolve_relative_path(sync_root, rel_path)
            result.warnings.extend(warnings)
            if error or full_path is None:
                result.errors.append(f"Cannot remove {rel_path!r}: {error}")
                continue
            if not os.path.exists(full_path):
                result.skipped.append(f"Already gone: {full_path}")
                continue
            try:
                if is_dir:
                    if os.path.isdir(full_path):
                        os.rmdir(full_path)
                        result.deleted_dirs.append(full_path)
                    else:
                        result.errors.append(f"Expected dir, found file: {full_path}")
                else:
                    if os.path.isfile(full_path):
                        os.remove(full_path)
                        result.deleted_files.append(full_path)
                    else:
                        result.errors.append(f"Expected file, found dir: {full_path}")
            except OSError as exc:
                result.errors.append(f"Remove failed {full_path}: {exc}")

        for rel_path, is_dir in sorted(changes["added"], key=lambda x: x[0].count("/")):
            full_path, warnings, error = safe_resolve_relative_path(sync_root, rel_path)
            result.warnings.extend(warnings)
            if error or full_path is None:
                result.errors.append(f"Cannot create {rel_path!r}: {error}")
                continue
            if os.path.exists(full_path):
                result.skipped.append(f"Already exists: {full_path}")
                continue
            try:
                if is_dir:
                    os.makedirs(full_path, exist_ok=False)
                    result.created_dirs.append(full_path)
                else:
                    parent = os.path.dirname(full_path)
                    os.makedirs(parent, exist_ok=True)
                    with open(full_path, "x", encoding="utf-8"):
                        pass
                    result.created_files.append(full_path)
            except OSError as exc:
                result.errors.append(f"Create failed {full_path}: {exc}")

        return result

    def undo_last(self):
        if not self.undo_stack:
            return

        answer = QMessageBox.question(
            self, "Confirm Safe Undo",
            "Undo the last creation?\n\n"
            "Only files created by the last action will be removed.\n"
            "Directories are removed only if empty.\n"
            "Sync-deleted files cannot be restored.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            self.status_bar.showMessage("Undo cancelled")
            return

        op = self.undo_stack.pop()
        rm_files = 0
        rm_dirs = 0
        failures: list[str] = []

        for path in reversed(op.created_files):
            try:
                if os.path.isfile(path):
                    os.remove(path)
                    rm_files += 1
            except OSError as exc:
                failures.append(f"File {path}: {exc}")

        for path in reversed(op.created_dirs):
            try:
                if os.path.isdir(path):
                    os.rmdir(path)
                    rm_dirs += 1
            except OSError as exc:
                failures.append(f"Dir {path}: {exc}")

        self.edit_tab.set_undo_enabled(bool(self.undo_stack))
        self.log(f"--- Action: Undo at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
        self.log(f"Removed {rm_dirs} dirs, {rm_files} files")
        for f in failures:
            self.log(f"Undo warning: {f}")

        self.status_bar.showMessage(f"Undo: {rm_dirs} dirs, {rm_files} files removed")
        if failures:
            QMessageBox.warning(self, "Undo With Warnings",
                "\n".join(failures[:20]) + ("\n\u2026" if len(failures) > 20 else ""))

    def _update_stats_display(self, result: OperationResult):
        parts = []
        if result.created_dirs:
            parts.append(f"{len(result.created_dirs)} dirs")
        if result.created_files:
            parts.append(f"{len(result.created_files)} files")
        if result.deleted_dirs:
            parts.append(f"{len(result.deleted_dirs)} rm-dirs")
        if result.deleted_files:
            parts.append(f"{len(result.deleted_files)} rm-files")
        if result.skipped:
            parts.append(f"{len(result.skipped)} skipped")
        if result.errors:
            parts.append(f"{len(result.errors)} errors")
        self._stats_lbl.setText("  " + " | ".join(parts) if parts else "")

    def log(self, text: str):
        self.action_log.append(text)

    def log_operation(self, result: OperationResult):
        for w in result.warnings:
            self.log(f"Warning: {w}")
        for s in result.skipped:
            self.log(f"Skipped: {s}")
        for e in result.errors:
            self.log(f"Error: {e}")
        for d in result.created_dirs:
            self.log(f"Created dir: {d}")
        for f in result.created_files:
            self.log(f"Created file: {f}")
        for old_path, new_path, is_dir in result.renamed:
            self.log(f"Renamed ({'folder' if is_dir else 'file'}): {old_path} -> {new_path}")
        for d in result.deleted_dirs:
            self.log(f"Deleted dir: {d}")
        for f in result.deleted_files:
            self.log(f"Deleted file: {f}")

    def format_result(self, result: OperationResult, planned: bool) -> str:
        dir_hdr = "Directories that would be created" if planned else "Directories created"
        file_hdr = "Files that would be created" if planned else "Files created"
        title = "Preview Summary" if planned else "Result Summary"

        lines = [
            title, "",
            f"Directories: {len(result.created_dirs)}",
            f"Files: {len(result.created_files)}",
            f"Deleted dirs: {len(result.deleted_dirs)}",
            f"Deleted files: {len(result.deleted_files)}",
            f"Renamed: {len(result.renamed)}",
            f"Skipped: {len(result.skipped)}",
            f"Warnings: {len(result.warnings)}",
            f"Errors: {len(result.errors)}",
            "",
        ]
        for label, vals in [
            (dir_hdr, result.created_dirs),
            (file_hdr, result.created_files),
            ("Directories deleted", result.deleted_dirs),
            ("Files deleted", result.deleted_files),
            ("Renamed", [f"{old} -> {new}" for old, new, _ in result.renamed]),
            ("Skipped", result.skipped),
            ("Warnings", result.warnings),
            ("Errors", result.errors),
        ]:
            if vals:
                lines.append(f"{label}:")
                lines.extend(f"  {v}" for v in vals)
                lines.append("")
        return "\n".join(lines)

    def show_result_dialog(self, title: str, result: OperationResult, planned: bool):
        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.setMinimumSize(750, 500)
        lay = QVBoxLayout(dlg)
        ed = QPlainTextEdit()
        ed.setReadOnly(True)
        ed.setPlainText(self.format_result(result, planned))
        f = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        f.setPointSize(10)
        ed.setFont(f)
        lay.addWidget(ed)
        btn = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btn.rejected.connect(dlg.close)
        lay.addWidget(btn)
        dlg.exec()
