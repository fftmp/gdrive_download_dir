#!/usr/bin/env python3

import sys
import json
import requests

GDRIVE_MAGIC_KEY = 'AIzaSyC1qbk75NzWBvSaDh6KnsjjA9pIrP4lYIE'
GDRIVE_HOST = 'https://clients6.google.com'
MAX_RESULTS = '5000'

def main():
    print("Try to download files from " + sys.argv[1])
    folder_id = sys.argv[1].rsplit('/', maxsplit=1)[1]
    print("folder_id = " + folder_id)
    flist = requests.get(GDRIVE_HOST + "/drive/v2beta/files?" +
                         "&q='" + folder_id + "' in parents" +
                         "&fields=items(mimeType,title,id),incompleteSearch" +
                         "&maxResults=" + MAX_RESULTS +
                         '&key=' + GDRIVE_MAGIC_KEY,
                         headers={'referer': 'https://drive.google.com/drive/folders/' + folder_id})
    print(flist.content.decode('utf8').replace("'", '"'))

    res = json.loads(flist.content.decode('utf8').replace("'", '"'))

    print("Start downloading " + str(len(res['items'])) + " files")
    exit(0)
    for item in res['items']:
        print("Try to download " + item['title'] + ' from ' + item['id'])

        resp = requests.get('https://docs.google.com/uc?id=' + item['id'])
        file_jpeg = open(item['title'], 'wb+')
        file_jpeg.write(resp.content)
        file_jpeg.close()
    print("Done")


if __name__ == '__main__':
    main()
