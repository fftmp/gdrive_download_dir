# About
This script aims to allow download shared folders from google drive without authorization.

At Aug 2017 "download all" button in web interface worked buggy:
1. some files can absent in result zip
1. zip create endless sometimes
1. some filenames are mangled

Now (Nov 2022) seems, that "download all" works ok, so this script still exist due to historical reasons, but excessive mangling still applied:
1. File COM1 will be renamed to _COM1. Similar behaviour for other filenames, that have special meaning in Windows.
1. if dot/space is last symbol in filename, dot/space will be changed to underscore.
1. newline will be changed to underscore (at least leading newline, but likely all).
1. Seems filenames are case-insensitive. Likely this is property of zip creation. So files 'a' and 'A' will be renamed to 'a' and 'a(1)' in zip.
1. Some other special symbols will be changed to underscore also. You can check this in detail using gen_test_dir.sh script.

# How it works
Script emulates browser behavior. It downloads list of files in folder (in JSON format), then download each file by file_id.
To get list of files need to use some magic string - need to investigate, what is it and can this string change or not.
For downloading big files (those, that can't verified against viruses) used idea from [turdus-merula and Andrew Hundt on stackoverflow](https://stackoverflow.com/a/39225039),


# Usage example
`./gdrive_download_dir.py 0B0HtNZkqn9bwM0NCRXRmMTdzY1U rename|overwrite|skip`

Script creates folder with given folder_id in cwd and place downloaded content there.

Last arg - strategy to resolve conflicts, if dst already contain file with same name:
* rename - save to new file, whose name will be 'orig_name + file_id'.
* overwrite - overwrite existing file.
* skip - do not (re)download file, if file with same name already exist. Default behaviour.


# TODO
* Sometimes can't download any file (connection closed from server side). Possibly this is problem of my connection, because after some time (10-30 min) same code begin to work ok.
* There is race because of possible interrupt point between checking file existance and creating file. Affect only multy-threaded download and have very low chance.
