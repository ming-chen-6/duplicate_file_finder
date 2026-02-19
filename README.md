# Duplicate File Finder

Scans a directory tree for duplicate files by comparing MD5 hashes. Generates an editable report so you can review what gets kept and what gets removed before executing.

Two ways to use it:
- **CLI** (`main.py`) — guided interactive prompts
- **Notebook** (`duplicate_finder.ipynb`) — configurable, cell-by-cell workflow

## Installation

```
pip install -r requirements.txt
```

Dependencies: `tqdm` (progress bars), `Send2Trash` (recycle bin support).

## Quick Start (CLI)

```
python main.py
```

1. Enter the root directory to scan (with trailing slash).
2. Review the generated `duplicate_report.txt` — edit KEEP/REMOVE labels if needed.
3. Choose trash or permanent delete.

## Notebook Usage

Open `duplicate_finder.ipynb` and run cells top-to-bottom:

1. Set config and filter variables.
2. Run the scan (progress bar included).
3. Generate the report, edit it externally if needed.
4. Load the report back, review the summary.
5. Uncomment the execution cell to delete.

## Configuration Reference

| Field | Type | Default | Description |
|---|---|---|---|
| `root_dir` | `str` | *(required)* | Directory to scan. Needs a trailing slash. |
| `resume` | `bool` | `False` | Resume a previous scan from checkpoint. |
| `report_path` | `str` | `"duplicate_report.txt"` | Path for the generated report file. |
| `delete_mode` | `str` | `"trash"` | `"trash"` or `"permanent"` (notebook only). **Warning: permanent is irreversible**|
| `default_keep_rule` | `str` | `"oldest"` | Which file to KEEP per group (see below). |
| `ignore_extensions` | `list[str]` | `None` | Extensions to skip (see Scan Filters). |
| `only_extensions` | `list[str]` | `None` | Extensions to scan exclusively (see Scan Filters). |
| `max_size` | `float` | `None` | Max file size to scan. |
| `max_size_unit` | `str` | `"MB"` | Unit for `max_size` — `"KB"`, `"MB"`, or `"GB"`. |
| `min_size` | `float` | `None` | Min file size to scan. |
| `min_size_unit` | `str` | `"KB"` | Unit for `min_size` — `"KB"`, `"MB"`, or `"GB"`. |

## Scan Filters

- **`ignore_extensions`** — Skip files with these extensions, e.g. `[".jpg", ".png"]`.
- **`only_extensions`** — Only scan files with these extensions, e.g. `[".pdf"]`.
- These two are **mutually exclusive** — setting both raises a `ValueError`.
- Extensions are matched **case-insensitively** (`.JPG` matches `.jpg`).
- **`min_size` / `max_size`** — Skip files outside the given size range. Set to `None` to disable.

## Report Format

The report is a tab-separated text file:

```
# [md5: a1b2c3d4] [size: 200KB] [3 files]
KEEP	2025-03-15 10:30	C:/photos/IMG_001.jpg
REMOVE	2025-03-15 10:30	C:/backup/IMG_001_copy.jpg
REMOVE	2025-06-01 14:22	C:/downloads/IMG_001(1).jpg
```

- Lines starting with `#` are group headers (metadata only).
- File lines are tab-separated: `ACTION	LAST_MODIFIED	PATH`.
- The first file in each group is marked `KEEP` (based on the keep rule), the rest `REMOVE`.
- You can edit the labels before executing. Change `REMOVE` to `KEEP` or vice versa.
- **Rule:** Every group must have at least one `KEEP`. The loader raises an error otherwise.

## Resume / Checkpoint

A SQLite database (`.dupfinder_cache.db`) is stored in the scanned directory. It records each file's path, MD5 hash, size, and modification time.

- If a scan is interrupted (Ctrl+C), progress is preserved — the DB commits after every file.
- On the next run, set `resume = True` to skip files that haven't changed since the last scan.
- Files that no longer exist on disk are automatically removed from the cache.
- To clear the checkpoint entirely, call `clear_checkpoint(root_dir)` or delete the `.dupfinder_cache.db` file.

## Keep Rules

The `default_keep_rule` controls which file in each duplicate group is marked `KEEP` by default when the report is generated:

| Rule | Behavior |
|---|---|
| `"oldest"` | Keep the file with the oldest modification time. |
| `"newest"` | Keep the file with the newest modification time. |
| `"shortest_path"` | Keep the file with the shortest path (shallowest in the tree). |
| `"first_found"` | Keep the first file encountered during the scan (no sorting). |

You can always override the defaults by editing the report file before executing.

## Delete Modes

- **`"trash"`** — Moves files to the OS recycle bin using Send2Trash. Files can be recovered.
- **`"permanent"`** — Deletes files from disk with `os.remove()`. This is irreversible.

In the CLI, you choose the mode interactively. In the notebook, set `delete_mode` in the config cell.
