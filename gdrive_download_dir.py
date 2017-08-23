#!/usr/bin/env python3

import sys
import json
import logging as log
from os import makedirs
import requests

GDRIVE_MAGIC_KEY = 'AIzaSyC1qbk75NzWBvSaDh6KnsjjA9pIrP4lYIE'
GDRIVE_HOST = 'https://clients6.google.com'
CHUNK_SIZE = 32768

def get_filelist(ses, dir_name, dir_id):
    log.debug('get files from ' + dir_name)
    files = dict()
    next_page_token = ''
    url = GDRIVE_HOST + '/drive/v2beta/files?'
    common_params = {'q': '\'' + dir_id + '\' in parents',
                     'fields': 'items(mimeType,title,id),nextPageToken',
                     'maxResults': '50',
                     'key': GDRIVE_MAGIC_KEY}
    headers = {'referer': 'https://drive.google.com/drive/folders/' + sys.argv[1]}

    while True:
        params = common_params
        if next_page_token != '':
            params['pageToken'] = next_page_token

        resp = ses.get(url, params=params, headers=headers)
        resp.raise_for_status()
        res = json.loads(resp.content.decode('utf8').replace('\'', '"'))
        for item in res['items']:
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                nested_files = get_filelist(ses, item['title'], item['id'])
                for file_id, filename in nested_files.items():
                    files[file_id] = dir_name + '/' + filename
            else:
                files[item['id']] = dir_name + '/' + item['title']
        if 'nextPageToken' in res.keys():
            next_page_token = res['nextPageToken']
        else:
            break # got all filenames and id's
    log.debug('got ' + str(len(files)) + ' files')
    return files


def download_file(file_id, filename):
    def get_confirm_token(cookies):
        for key, value in cookies.items():
            if key.startswith('download_warning'):
                return value
        return None

    def save_response_content(response, destination):
        with open(destination, "wb+") as _f:
            for chunk in response.iter_content(CHUNK_SIZE):
                if chunk: # filter out keep-alive new chunks
                    _f.write(chunk)

    path = filename.rsplit('/', maxsplit=1)[0]
    log.debug('Download ' + filename + ' from ' + file_id + ' path = ' + path)
    makedirs(path, exist_ok=True)
    resp = requests.get('https://drive.google.com/uc?export=download',
                        params={'id': file_id},
                        stream=True)
    resp.raise_for_status()
    token = get_confirm_token(resp.cookies)
    if token:
        resp = requests.get('https://drive.google.com/uc?export=download',
                            params={'id': file_id, 'confirm' : token},
                            stream=True)
        resp.raise_for_status()
    save_response_content(resp, filename)

def main():
    log.basicConfig(level=log.DEBUG)
    log.info('Start downloading files from folder id = ' + sys.argv[1])
    ses = requests.Session() #create session for activate keep alive
    files = get_filelist(ses, sys.argv[1], sys.argv[1])
    log.info('Start downloading ' + str(len(files)) + ' files')

    for file_id, filename in files.items():
        download_file(file_id, filename)
    log.info('Done')


if __name__ == '__main__':
    main()
