import os

from send2trash import send2trash


def remove_files(file_list):
    '''Permanently remove all files whose paths are listed in the given list.

    Iterates over the list and deletes each file from disk. This is
    irreversible — files cannot be recovered.

    Parameters:
        file_list: A list of file path strings to delete.

    Returns:
        None.
    '''
    for file in file_list:
        os.remove(file)


def trash_files(file_list):
    '''Move all files whose paths are listed in the given list to the OS trash.

    Uses the system recycle bin / trash, so files can be recovered afterwards.

    Parameters:
        file_list: A list of file path strings to move to trash.

    Returns:
        None.
    '''
    for file in file_list:
        send2trash(file)
