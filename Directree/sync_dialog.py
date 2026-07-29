from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QListWidget, QDialogButtonBox,
)


class SyncDialog(QDialog):
    def __init__(self, changes: dict, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Sync Changes")
        self.setMinimumSize(700, 550)

        layout = QVBoxLayout(self)

        summary = QLabel(
            f"<b>Changes detected:</b><br>"
            f"<span style='color: #a6e3a1;'>Added: {len(changes['added'])}</span><br>"
            f"<span style='color: #f38ba8;'>Removed: {len(changes['removed'])}</span><br>"
            f"<span style='color: #fab387;'>Renamed: {len(changes.get('renamed', []))}</span><br>"
            f"Unchanged: {len(changes['unchanged'])}"
        )
        layout.addWidget(summary)

        if changes.get("warnings"):
            warning_label = QLabel(
                "<b style='color: #fab387;'>Warnings:</b><br>"
                + "<br>".join(changes["warnings"][:10])
            )
            warning_label.setWordWrap(True)
            layout.addWidget(warning_label)

        if changes.get("renamed"):
            layout.addWidget(QLabel("<b style='color: #fab387;'>Items to rename (move):</b>"))
            renamed_list = QListWidget()
            for old_path, new_path, is_dir in changes["renamed"]:
                kind = "Folder" if is_dir else "File"
                renamed_list.addItem(f"{kind}: {old_path}  ->  {new_path}")
            renamed_list.setMaximumHeight(120)
            layout.addWidget(renamed_list)

        if changes["added"]:
            layout.addWidget(QLabel("<b style='color: #a6e3a1;'>Items to create:</b>"))
            added_list = QListWidget()
            for path, is_dir in changes["added"]:
                added_list.addItem(f"{'[D]' if is_dir else '[F]'}: {path}")
            added_list.setMaximumHeight(150)
            layout.addWidget(added_list)

        if changes["removed"]:
            layout.addWidget(QLabel("<b style='color: #f38ba8;'>Items to remove:</b>"))
            removed_list = QListWidget()
            for path, is_dir in changes["removed"]:
                removed_list.addItem(f"{'[D]' if is_dir else '[F]'}: {path}")
            removed_list.setMaximumHeight(150)
            layout.addWidget(removed_list)

            warning = QLabel(
                "<b style='color: #f38ba8;'>Warning:</b> Files removed during sync "
                "are permanently deleted. Directories are removed only if empty."
            )
            warning.setWordWrap(True)
            layout.addWidget(warning)

        layout.addStretch()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Apply Safe Sync")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)
