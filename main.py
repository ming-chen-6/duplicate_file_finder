import os

from tqdm import tqdm

from src.duplicate_finder import (
    ScanConfig,
    find_all_duplicate_files,
    generate_report,
    load_report,
    validate_report,
    get_files_to_remove,
    remove_files,
    trash_files,
    clear_checkpoint,
    validate_checkpoint,
)


def _run_scan(config):
    '''Run the scan with a tqdm progress bar and return grouped results.'''
    pbar = tqdm(desc="Scanning", unit=" files")
    grouped = find_all_duplicate_files(config, on_progress=lambda f: pbar.update(1))
    pbar.close()
    return grouped


def _review_and_execute(report_path):
    '''Load a report, show summary, and prompt for deletion.'''
    report = load_report(report_path)
    to_remove = get_files_to_remove(report)
    to_keep = len(report) - len(to_remove)
    print(f'\n{len(to_remove)} file(s) to remove, {to_keep} file(s) to keep.')

    if not to_remove:
        print('Nothing to remove (all files marked KEEP).')
        return

    print('\nHow do you want to handle duplicates?')
    print('1. Move to trash (recoverable)')
    print('2. Permanently delete')
    choice = input('Enter 1 or 2: ')

    if choice == '1':
        trash_files(to_remove)
        print(f'Moved {len(to_remove)} file(s) to trash.')
    elif choice == '2':
        confirm = input('This is irreversible. Are you sure? Y/N: ')
        if confirm.lower() == 'y':
            remove_files(to_remove)
            print(f'Permanently removed {len(to_remove)} file(s).')
        else:
            print('Deletion cancelled.')
    else:
        print('Invalid choice. Deletion cancelled.')


if __name__ == '__main__':
    try:
        print('Duplicate File Finder')
        print('  1. New scan')
        print('  2. Resume previous scan')
        print('  3. Load report file')
        choice = input('Choice: ')

        if choice == '1':
            root_dir = input('Root directory (with trailing slash): ')
            clear_checkpoint(root_dir)
            config = ScanConfig(root_dir=root_dir)
            grouped = _run_scan(config)

            if not grouped:
                print('No duplicate files found!')
            else:
                report_path = config.report_path
                generate_report(grouped, report_path, keep_rule=config.default_keep_rule)
                total = sum(len(f) for f in grouped.values())
                print(f'Found {len(grouped)} duplicate group(s) ({total} files total).')
                print(f'Report written to: {report_path}\n')

                answer = input('Review the report and edit if needed. '
                               'Press Enter to continue, or Q to quit: ')
                if answer.strip().lower() != 'q':
                    _review_and_execute(report_path)
                else:
                    print('Exiting. Report saved for next time.')

        elif choice == '2':
            while True:
                root_dir = input('Root directory (with trailing slash): ')
                if validate_checkpoint(root_dir):
                    break
                print('No valid checkpoint found in that directory. Try again.')

            config = ScanConfig(root_dir=root_dir, resume=True)
            grouped = _run_scan(config)

            if not grouped:
                print('No duplicate files found!')
            else:
                report_path = config.report_path
                generate_report(grouped, report_path, keep_rule=config.default_keep_rule)
                total = sum(len(f) for f in grouped.values())
                print(f'Found {len(grouped)} duplicate group(s) ({total} files total).')
                print(f'Report written to: {report_path}\n')

                answer = input('Review the report and edit if needed. '
                               'Press Enter to continue, or Q to quit: ')
                if answer.strip().lower() != 'q':
                    _review_and_execute(report_path)
                else:
                    print('Exiting. Report saved for next time.')

        elif choice == '3':
            while True:
                report_path = input('Report file path: ')
                valid, message = validate_report(report_path)
                if valid:
                    break
                print(f'Invalid report: {message}. Try again.')

            _review_and_execute(report_path)

        else:
            print('Invalid choice.')

    except KeyboardInterrupt:
        print('\nScan paused. Run again to resume.')
