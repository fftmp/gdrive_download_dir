#!/usr/bin/env python3
""" Download files and folders from google drive using direct access to files as browser does it.
    You only need to pass dir_id as param and result will be saved in cwd/dir_id.
    It's also possible to use this script as module.
    get_dir_tree function allow to get finenames and other metainfo about files in dir,
    download_file function just download one file ).
"""

import sys
import json
import logging as log
from os import makedirs
from os.path import getsize
from multiprocessing.dummy import Pool as ThreadPool
from time import sleep
import shutil
import requests

GDRIVE_MAGIC_KEY = 'AIzaSyC1qbk75NzWBvSaDh6KnsjjA9pIrP4lYIE'
GDRIVE_HOST = 'https://clients6.google.com'
DOWNLOAD_THREADS = 10
DOWNLOAD_ATTEMPTS = 5
TIMEOUT = 10

def get_dir_tree(ses, dir_name, dir_id):
    """Return info about files and dirs inside list of dict: [{size : '', name: '', _id: ''}]
       for given dir_id. Names are relative to dir. Call itself recursive for subdirs.
    """
    log.debug('get file list ' + dir_name)
    tree = list()
    next_page_token = ''
    url = GDRIVE_HOST + '/drive/v2beta/files?'
    common_params = {'q': '\'' + dir_id + '\' in parents',
                     'fields': 'items(mimeType,title,id,fileSize),nextPageToken',
                     'maxResults': '1000',
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
                nested_tree = get_dir_tree(ses, item['title'], item['id'])
                for _it in nested_tree:
                    _it['name'] = dir_name + '/' + _it['name']
                tree.extend(nested_tree)
            else:
                tree.append({'_id' : item['id'], 'name' : dir_name + '/' + item['title'],
                             'size' : int(item['fileSize'])})
            tree.append({'_id': dir_id, 'name': dir_name + '/'})
        if 'nextPageToken' in res.keys():
            next_page_token = res['nextPageToken']
        else: # got all filenames and id's
            return tree


def download_file(item):
    """ Download file and save it to name. Create dirs, if necessary.
        If name end with '/', treat it as a dir name an only create dir.
    """
    if item['name'].endswith('/'):
        #this is dir, not a file
        makedirs(item['name'], exist_ok=True)
        return
    path = item['name'].rsplit('/', maxsplit=1)[0]
    log.debug('Download ' + item['name'] + ' from ' + item['_id'] + ' path = ' + path)
    makedirs(path, exist_ok=True)

    for i in range(DOWNLOAD_ATTEMPTS):
        try:
            resp = requests.get('https://drive.google.com/uc?', params={'id': item['_id']},
                                stream=True, timeout=TIMEOUT)
            resp.raise_for_status()
            for cookie_name in resp.cookies.keys():
                if cookie_name.startswith('download_warning'):
                    log.debug('big file ' + item['name'] + ' id = ' + item['_id'])
                    resp = requests.post('https://drive.google.com/uc?', params={'id': item['_id']})
                    resp.raise_for_status()
                    # in response first line contain garbage. so we cut it
                    resp = requests.get(json.loads(resp.content.decode('utf8').
                                                   split('\n', maxsplit=1)[1])
                                        ['downloadUrl'],
                                        stream=True, timeout=TIMEOUT)
                    break
            with open(item['name'], 'wb') as _f:
                resp.raw.decode_content = True
                shutil.copyfileobj(resp.raw, _f)
            break
        except requests.exceptions.ConnectionError:
            if i < DOWNLOAD_ATTEMPTS - 1:
                log.warning('ConnectionError during download file ' + item['name'] +
                            ' with id = ' + item['_id'] + '. Retrying.')
                sleep(2)
            else:
                log.error('Couldn\'t download file ' + item['name'] +
                          ' with id = ' + item['_id'] + '. Skipping.')
                return

    real_size = getsize(item['name'])
    if  real_size != item['size']:
        raise Exception('Error during download file ' + item['name'] +
                        '. Expected size = ' + str(item['size']) + '. Get size = ' + str(real_size))

def download_dir_recursive(dir_id, dir_name):
    """ Download all files and dirs (including empty dirs) from dir with id=dir_id
        and save result in dir_name.
    """
    log.basicConfig(level=log.DEBUG)
    log.getLogger("urllib3").setLevel(log.WARNING)
    log.info('Start downloading ' + dir_id + ' to ' + dir_name)
    log.info('Prepare list of files')
    ses = requests.Session() #create session for activate keep alive
    tree = get_dir_tree(ses, dir_id, dir_name)
    total_size = 0
    for _it in tree:
        if 'size' in _it.keys():
            total_size += _it['size']
    log.info('Start downloading files. Total size = ' + str(total_size) + ' bytes')

    pool = ThreadPool(DOWNLOAD_THREADS)
    pool.map(download_file, tree)
    pool.close()
    pool.join()

    log.info('Done downloading ' + dir_id + ' to ' + dir_name)


if __name__ == '__main__':
    download_dir_recursive(sys.argv[1], sys.argv[1])
