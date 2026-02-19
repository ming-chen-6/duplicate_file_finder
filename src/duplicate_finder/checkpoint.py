import os
import sqlite3

DB_FILENAME = '.dupfinder_cache.db'


def open_checkpoint(root_dir):
    '''Create or open the checkpoint database for a given root directory.

    The database file is stored as .dupfinder_cache.db inside root_dir.
    Creates the scanned_files table if it does not already exist.

    Parameters:
        root_dir: The root directory where the DB file will be stored.

    Returns:
        A sqlite3.Connection to the checkpoint database.
    '''
    db_path = os.path.join(root_dir, DB_FILENAME)
    conn = sqlite3.connect(db_path)
    conn.execute(
        '''CREATE TABLE IF NOT EXISTS scanned_files (
            file_path TEXT PRIMARY KEY,
            md5 TEXT,
            file_size INTEGER,
            last_modified REAL
        )'''
    )
    conn.commit()
    return conn


def get_scanned_files(conn):
    '''Load all previously scanned file records from the checkpoint database.

    Parameters:
        conn: A sqlite3.Connection returned by open_checkpoint().

    Returns:
        A dict mapping file_path to a tuple of (md5, file_size, last_modified).
    '''
    cursor = conn.execute('SELECT file_path, md5, file_size, last_modified FROM scanned_files')
    return {row[0]: (row[1], row[2], row[3]) for row in cursor}


def save_scanned_file(conn, file_path, md5, file_size, last_modified):
    '''Insert or update a single scanned file record in the checkpoint database.

    Commits immediately so progress is preserved if the scan is interrupted.

    Parameters:
        conn:          A sqlite3.Connection returned by open_checkpoint().
        file_path:     Absolute path to the scanned file.
        md5:           MD5 hex digest of the file contents.
        file_size:     Size of the file in bytes.
        last_modified: Last modification time of the file (os.path.getmtime value).

    Returns:
        None.
    '''
    conn.execute(
        'INSERT OR REPLACE INTO scanned_files (file_path, md5, file_size, last_modified) VALUES (?, ?, ?, ?)',
        (file_path, md5, file_size, last_modified)
    )
    conn.commit()


def remove_missing_files(conn, existing_paths):
    '''Delete checkpoint rows for files that no longer exist on disk.

    Parameters:
        conn:           A sqlite3.Connection returned by open_checkpoint().
        existing_paths: A set of file path strings that currently exist.

    Returns:
        None.
    '''
    cursor = conn.execute('SELECT file_path FROM scanned_files')
    stale = [row[0] for row in cursor if row[0] not in existing_paths]
    for path in stale:
        conn.execute('DELETE FROM scanned_files WHERE file_path = ?', (path,))
    if stale:
        conn.commit()


def clear_checkpoint(root_dir):
    '''Delete the checkpoint database file entirely.

    Parameters:
        root_dir: The root directory containing the .dupfinder_cache.db file.

    Returns:
        None.
    '''
    db_path = os.path.join(root_dir, DB_FILENAME)
    if os.path.exists(db_path):
        os.remove(db_path)
