import glob
import hashlib
import os
import traceback
import logging

#----------- HELPER FUNCTIONS ---------------

# function that generates md5 of a given file
def FileMd5Generator(file_name):
    data = open(file_name, 'rb').read()    # read contents of the file
    return hashlib.md5(data).hexdigest()    # pipe contents of the file through and return md5

# function that finds all 
def FindAllDuplicateFiles(root_dir):
    duplicate_file_queue = []   #array used to store duplicate files
    exist_md5_dict = {}         #dict used to store md5 of existing files
    try:
        for filename in glob.iglob(root_dir + '**/**', recursive=True):  
            if os.path.isdir(filename):
                continue
            curr_md5 = FileMd5Generator(filename)
            if curr_md5 in exist_md5_dict:      #add md5 to queue if md5 already exist
                duplicate_file_queue.append(filename)
            else:                               #otherwise add it to dict
                exist_md5_dict.update({curr_md5: 1})

    except Exception as e:
        logging.error(traceback.format_exc())
        print(e.message, e.args)

    return duplicate_file_queue

# function that remove all files in array passed in
def RemoveAllFIlesInArray(duplicate_file_queue):
    for file in duplicate_file_queue:
        os.remove(file)
        print('file ' + file +' removed')
#///////////// END OF HELPER FUNCTIONS \\\\\\\\\\\\





#----------------- MAIN ---------------------

# root_dir needs a trailing slash (i.e. /root/dir/)
root_dir = input('please enter root directory for cleaning:\nNote: needs a trailing slash (i.e. /root/dir/\n')
print('cleaning files in ' + root_dir + '\n')
duplicate_file_queue = FindAllDuplicateFiles(root_dir)

# display all duplicate files
print('duplicate files found:\n--------------------------------')
for file in duplicate_file_queue:
    print(file)
print('--------------------------------')

# asking if user want to remove duplicate files
if len(duplicate_file_queue) != 0:
    respond_for_cleaning = input('\n Do you want to remove all of them? Y/N')
    if (respond_for_cleaning == 'Y') or (respond_for_cleaning == 'n'):
        print('cleaning start\n---------------------------------------------')
        RemoveAllFIlesInArray(duplicate_file_queue)
else:
    print('No duplicate file found!')

# end the program
end_program_indicator = input('\n##########################\n###### PROGRAM ENDS ###### \n # ENTER ANY KEY TO EXIT #')

#//////////////// END OF MAIN \\\\\\\\\\\\\\\
