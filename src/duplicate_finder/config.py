from dataclasses import dataclass


@dataclass
class ScanConfig:
    '''Configuration for a duplicate file scan.

    Holds all settings needed to run a scan. Pass an instance of this
    to find_all_duplicate_files() to control scan behavior.

    Attributes:
        root_dir:           Directory to scan. Needs a trailing slash.
        resume:             Whether to resume a previous scan from checkpoint.
        report_path:        Path for the generated duplicate report file.
        ignore_extensions:  List of extensions to skip (e.g. [".jpg", ".png"]).
        only_extensions:    List of extensions to scan exclusively (e.g. [".pdf"]).
        max_size:           Maximum file size to scan, or None for no limit.
        max_size_unit:      Unit for max_size — "KB", "MB", or "GB".
        min_size:           Minimum file size to scan, or None for no limit.
        min_size_unit:      Unit for min_size — "KB", "MB", or "GB".

    Raises:
        ValueError: If both ignore_extensions and only_extensions are set.
    '''
    root_dir: str
    resume: bool = False
    report_path: str = 'duplicate_report.txt'
    ignore_extensions: list[str] = None
    only_extensions: list[str] = None
    max_size: float = None
    max_size_unit: str = 'MB'
    min_size: float = None
    min_size_unit: str = 'KB'

    def __post_init__(self):
        if self.ignore_extensions is not None and self.only_extensions is not None:
            raise ValueError(
                'ignore_extensions and only_extensions are mutually exclusive'
            )
