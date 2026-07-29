from dataclasses import dataclass, field


@dataclass
class ParsedLine:
    line_no: int
    raw: str
    depth: int
    name: str
    has_branch: bool


@dataclass
class OperationResult:
    created_files: list[str] = field(default_factory=list)
    created_dirs: list[str] = field(default_factory=list)
    deleted_files: list[str] = field(default_factory=list)
    deleted_dirs: list[str] = field(default_factory=list)
    renamed: list[tuple[str, str, bool]] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def total_created(self) -> int:
        return len(self.created_files) + len(self.created_dirs)

    @property
    def total_deleted(self) -> int:
        return len(self.deleted_files) + len(self.deleted_dirs)

    @property
    def total_renamed(self) -> int:
        return len(self.renamed)

    @property
    def total_changed(self) -> int:
        return self.total_created + self.total_deleted + self.total_renamed

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)
