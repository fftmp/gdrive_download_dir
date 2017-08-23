# About
This script aims to allow download shared folders from google drive without authorization.  
Currently (Aug 2017), "download all" button in web interface works buggy.  
For example some files can absent in result zip or zip create endless.  
See more:
1. https://productforums.google.com/forum/#!topic/drive/MTDDCtXTRyQ
1. https://productforums.google.com/forum/#!topic/drive/m_uJ8TTQce0
1. https://productforums.google.com/forum/#!topic/drive/YUseY-VPG-Q

Another ways (via various applications) require authorization.

# How it works
Script emulates browser behavior. It downloads list of files in folder (in JSON format), then download each file by file_id.
To get list of files need to use some magic string - need to investigate, what is it and can this string change or not.

# Usage example
./gdrive_download_dir.py 0B0HtNZkqn9bwM0NCRXRmMTdzY1U  
(You can use https://drive.google.com/drive/folders/0B0HtNZkqn9bwM0NCRXRmMTdzY1U for tests)

# TODO
*   add parallel download
*   check successfull download
*   add option for download or skip trashed files
*   add ability to download big (>2Gb) files
