import os
from datetime import datetime


def _format_size(size_bytes):
    '''Format a file size in bytes to a human-readable string.

    Parameters:
        size_bytes: File size in bytes.

    Returns:
        A string like "1.2MB", "200KB", or "512B".
    '''
    if size_bytes >= 1024 * 1024 * 1024:
        return f'{size_bytes / (1024 * 1024 * 1024):.1f}GB'
    elif size_bytes >= 1024 * 1024:
        return f'{size_bytes / (1024 * 1024):.1f}MB'
    elif size_bytes >= 1024:
        return f'{size_bytes / 1024:.1f}KB'
    else:
        return f'{size_bytes}B'


def _format_time(timestamp):
    '''Format a Unix timestamp to YYYY-MM-DD HH:MM.

    Parameters:
        timestamp: A float from os.path.getmtime() or os.stat().st_mtime.

    Returns:
        A formatted date string.
    '''
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')


def _sort_by_keep_rule(files, keep_rule):
    '''Sort a list of file info dicts so the file to KEEP comes first.

    Parameters:
        files:     A list of dicts with "path", "file_size", "last_modified".
        keep_rule: One of "oldest", "newest", "shortest_path", "first_found".

    Returns:
        A new sorted list (does not modify the original).
    '''
    if keep_rule == 'oldest':
        return sorted(files, key=lambda f: f['last_modified'])
    elif keep_rule == 'newest':
        return sorted(files, key=lambda f: f['last_modified'], reverse=True)
    elif keep_rule == 'shortest_path':
        return sorted(files, key=lambda f: len(f['path']))
    else:
        return list(files)


def generate_report(grouped_results, output_path, keep_rule='first_found'):
    '''Write a tab-separated duplicate report file.

    The first file in each group is marked KEEP, the rest are marked REMOVE.
    Files are sorted within each group according to keep_rule so the file
    that should be kept appears first.

    Parameters:
        grouped_results: Dict from find_all_duplicate_files() keyed by MD5 hash,
                         where each value is a list of file info dicts with keys
                         "path", "file_size", and "last_modified".
        output_path:     Path where the report file will be written.
        keep_rule:       Rule for choosing which file to keep — "oldest",
                         "newest", "shortest_path", or "first_found".

    Returns:
        None.
    '''
    with open(output_path, 'w', encoding='utf-8') as f:
        first_group = True
        for md5, files in grouped_results.items():
            if not first_group:
                f.write('\n')
            first_group = False

            sorted_files = _sort_by_keep_rule(files, keep_rule)
            size_str = _format_size(sorted_files[0]['file_size'])
            f.write(f'# [md5: {md5}] [size: {size_str}] [{len(sorted_files)} files]\n')

            for i, file_info in enumerate(sorted_files):
                action = 'KEEP' if i == 0 else 'REMOVE'
                time_str = _format_time(file_info['last_modified'])
                f.write(f'{action}\t{time_str}\t{file_info["path"]}\n')


def validate_report(report_path):
    '''Validate a report file for correctness without loading it.

    Checks that the file exists, can be parsed, and every group has at
    least one KEEP entry.

    Parameters:
        report_path: Path to the report file to validate.

    Returns:
        A tuple (valid, message). Returns (True, "") if the file is valid.
        Returns (False, "reason") with a human-readable error otherwise.
    '''
    if not os.path.exists(report_path):
        return (False, 'File not found')

    try:
        current_group = []
        current_md5 = None
        line_number = 0

        with open(report_path, 'r', encoding='utf-8') as f:
            for line in f:
                line_number += 1
                line = line.rstrip('\n')

                if line.startswith('#'):
                    if current_group:
                        keep_count = sum(1 for e in current_group if e == 'KEEP')
                        if keep_count == 0:
                            return (False, f'Group with {current_md5} has no KEEP entry')
                    current_group = []
                    current_md5 = line.split(']')[0].replace('# [', '')
                elif line.strip() == '':
                    continue
                else:
                    parts = line.split('\t')
                    if len(parts) < 3:
                        return (False, f'Invalid format on line {line_number}')
                    if parts[0] not in ('KEEP', 'REMOVE'):
                        return (False, f'Invalid action \'{parts[0]}\' on line {line_number}')
                    current_group.append(parts[0])

        if current_group:
            keep_count = sum(1 for e in current_group if e == 'KEEP')
            if keep_count == 0:
                return (False, f'Group with {current_md5} has no KEEP entry')

        return (True, '')
    except Exception as e:
        return (False, str(e))


def load_report(report_path):
    '''Parse a duplicate report file back into a list of action entries.

    Validates the report first using validate_report(). If validation fails,
    raises a ValueError with the error message.

    Parameters:
        report_path: Path to the report file to parse.

    Returns:
        A list of dicts, each with "action" (str) and "path" (str) keys.

    Raises:
        ValueError: If the file is missing, malformed, or any group has zero KEEP entries.
    '''
    valid, message = validate_report(report_path)
    if not valid:
        raise ValueError(message)

    entries = []
    with open(report_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            if line.startswith('#') or line.strip() == '':
                continue
            parts = line.split('\t')
            entries.append({'action': parts[0], 'path': parts[2]})

    return entries


def get_files_to_remove(report):
    '''Filter a parsed report to only the file paths marked REMOVE.

    Parameters:
        report: A list of dicts from load_report(), each with "action" and "path".

    Returns:
        A list of file path strings that are marked REMOVE.
    '''
    return [entry['path'] for entry in report if entry['action'] == 'REMOVE']
