import os

from src.duplicate_finder import (
    ScanConfig,
    find_all_duplicate_files,
    generate_report,
    load_report,
    get_files_to_remove,
    remove_files,
)

if __name__ == '__main__':
    try:
        root_dir = input('Please enter root directory for cleaning:\n'
                         'Note: needs a trailing slash (i.e. /root/dir/)\n')

        # Check for a previous scan checkpoint
        resume = False
        db_path = os.path.join(root_dir, '.dupfinder_cache.db')
        if os.path.exists(db_path):
            answer = input('A previous scan was found. Resume? Y/N: ')
            if answer.lower() == 'y':
                resume = True

        config = ScanConfig(root_dir=root_dir, resume=resume)
        print('Scanning ' + root_dir + ' ...\n')
        grouped = find_all_duplicate_files(config)

        if not grouped:
            print('No duplicate files found!')
        else:
            # Generate report for user review
            report_path = config.report_path
            generate_report(grouped, report_path)
            total_dupes = sum(len(files) for files in grouped.values())
            print(f'Found {len(grouped)} duplicate group(s) ({total_dupes} files total).')
            print(f'Report written to: {report_path}\n')

            answer = input('Review the report and edit if needed. '
                           'Press Enter when ready to continue, or type Q to quit: ')
            if answer.strip().lower() == 'q':
                print('Exiting. Report saved for next time.')
            else:
                report = load_report(report_path)
                to_remove = get_files_to_remove(report)
                to_keep = len(report) - len(to_remove)
                print(f'\n{len(to_remove)} file(s) to remove, {to_keep} file(s) to keep.')

                if to_remove:
                    confirm = input('Proceed with deletion? Y/N: ')
                    if confirm.lower() == 'y':
                        remove_files(to_remove)
                        print(f'Removed {len(to_remove)} file(s).')
                    else:
                        print('Deletion cancelled.')
                else:
                    print('Nothing to remove (all files marked KEEP).')

    except KeyboardInterrupt:
        print('\nScan paused. Run again to resume.')
