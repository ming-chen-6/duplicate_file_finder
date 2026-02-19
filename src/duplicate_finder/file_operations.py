import os


def remove_files(file_list):
    '''Remove all files whose paths are listed in the given list.

    Iterates over the list and deletes each file from disk.

    Parameters:
        file_list: A list of file path strings to delete.

    Returns:
        None.
    '''
    for file in file_list:
        os.remove(file)
