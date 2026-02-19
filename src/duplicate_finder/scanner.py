import glob
import hashlib
import logging
import os
import traceback

from .config import ScanConfig
from .checkpoint import open_checkpoint, get_scanned_files, save_scanned_file, remove_missing_files


def size_to_bytes(value: float, unit: str) -> int:
    '''Convert a size value with a unit string to bytes.

    Parameters:
        value: The numeric size value.
        unit:  One of "KB", "MB", or "GB".

    Returns:
        The size in bytes as an integer.
    '''
    multipliers = {'KB': 1024, 'MB': 1024 ** 2, 'GB': 1024 ** 3}
    return int(value * multipliers[unit])


def should_skip_file(file_path: str, file_size: int, config: ScanConfig) -> bool:
    '''Check whether a file should be skipped based on scan filters.

    Evaluates the file against extension filters (ignore_extensions or
    only_extensions) and size filters (min_size, max_size) from the config.

    Parameters:
        file_path: Path to the file being checked.
        file_size: Size of the file in bytes.
        config:    A ScanConfig instance with filter fields.

    Returns:
        True if the file should be skipped, False if it should be scanned.
    '''
    ext = os.path.splitext(file_path)[1].lower()

    if config.ignore_extensions is not None:
        if ext in [e.lower() for e in config.ignore_extensions]:
            return True

    if config.only_extensions is not None:
        if ext not in [e.lower() for e in config.only_extensions]:
            return True

    if config.min_size is not None:
        if file_size < size_to_bytes(config.min_size, config.min_size_unit):
            return True

    if config.max_size is not None:
        if file_size > size_to_bytes(config.max_size, config.max_size_unit):
            return True

    return False


def file_md5_generator(file_path: str) -> str:
    '''Generate the MD5 hash of a file's contents.

    Parameters:
        file_path: Path to the file to hash.

    Returns:
        A string containing the hexadecimal MD5 digest of the file.
    '''
    data = open(file_path, 'rb').read()
    return hashlib.md5(data).hexdigest()


def find_all_duplicate_files(config: ScanConfig) -> dict[str, list[dict]]:
    '''Find all duplicate files in a directory tree by comparing MD5 hashes.

    Recursively walks the directory specified in config.root_dir. For each
    file, computes its MD5 hash (or reuses a cached hash when resuming) and
    groups files that share the same hash.

    Files are checked against scan filters (extensions, size) before hashing.

    When config.resume is True, previously scanned files are loaded from
    the checkpoint database and files that haven't changed are skipped
    instead of being re-hashed.

    Progress is saved to the checkpoint database after each file so the
    scan can be resumed if interrupted.

    Parameters:
        config: A ScanConfig instance with root_dir, resume, and filter fields.

    Returns:
        A dict keyed by MD5 hash. Each value is a list of file info dicts
        with keys "path" (str), "file_size" (int), and "last_modified" (float).
        Only groups with 2 or more files are included.
    '''
    md5_groups = {}
    conn = open_checkpoint(config.root_dir)

    try:
        # Collect all file paths first for cleanup
        all_paths = set()
        for filename in glob.iglob(config.root_dir + '**/**', recursive=True):
            if not os.path.isdir(filename):
                all_paths.add(filename)

        # Load cached data if resuming
        cached = {}
        if config.resume:
            remove_missing_files(conn, all_paths)
            cached = get_scanned_files(conn)

        for filename in all_paths:
            stat = os.stat(filename)

            # Apply filters before hashing
            if should_skip_file(filename, stat.st_size, config):
                continue

            # Check if we can reuse a cached hash
            if filename in cached:
                c_md5, c_size, c_mtime = cached[filename]
                if stat.st_size == c_size and stat.st_mtime == c_mtime:
                    curr_md5 = c_md5
                else:
                    curr_md5 = file_md5_generator(filename)
                    save_scanned_file(conn, filename, curr_md5, stat.st_size, stat.st_mtime)
            else:
                curr_md5 = file_md5_generator(filename)
                save_scanned_file(conn, filename, curr_md5, stat.st_size, stat.st_mtime)

            file_info = {
                'path': filename,
                'file_size': stat.st_size,
                'last_modified': stat.st_mtime,
            }

            if curr_md5 not in md5_groups:
                md5_groups[curr_md5] = []
            md5_groups[curr_md5].append(file_info)

    except KeyboardInterrupt:
        logging.info('Scan interrupted. Progress has been saved to checkpoint.')
        raise
    except Exception as e:
        logging.error(traceback.format_exc())
        raise
    finally:
        conn.close()

    return {md5: files for md5, files in md5_groups.items() if len(files) >= 2}
