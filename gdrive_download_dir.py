#!/usr/bin/env python3

import sys
import json
import logging as log
from os import makedirs
from os.path import getsize
from multiprocessing.dummy import Pool as ThreadPool
import shutil
import requests

GDRIVE_MAGIC_KEY = 'AIzaSyC1qbk75NzWBvSaDh6KnsjjA9pIrP4lYIE'
GDRIVE_HOST = 'https://clients6.google.com'
DOWNLOAD_THREADS = 10

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
                             'size' : item['fileSize']})
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

    resp = requests.get('https://drive.google.com/uc?', params={'id': item['_id']})
    resp.raise_for_status()
    for cookie_name in resp.cookies.keys():
        if cookie_name.startswith('download_warning'):
            log.debug('big file ' + item['name'] + ' id = ' + item['_id'])
            resp = requests.post('https://drive.google.com/uc?', params={'id': item['_id']})
            resp.raise_for_status()
            # in response first line contain garbage. so we cut it
            resp = requests.get(json.loads(resp.content.decode('utf8').split('\n', maxsplit=1)[1])
                                ['downloadUrl'],
                                stream=True)
            break
    with open(item['name'], 'wb') as _f:
        resp.raw.decode_content = True
        shutil.copyfileobj(resp.raw, _f)

    real_size = getsize(item['name'])
    if  real_size != item['size']:
        raise Exception('Error during download file ' + item['name'] +
                        '. Expected size = ' + item['size'] + '. Get size = ' + real_size)

def main():
    log.basicConfig(level=log.DEBUG)
    log.info('Start ' + sys.argv[0])
    log.info('Prepare list of files')
    ses = requests.Session() #create session for activate keep alive
    tree = get_dir_tree(ses, sys.argv[1], sys.argv[1])
    log.info('Start downloading files')

    pool = ThreadPool(DOWNLOAD_THREADS)
    pool.map(download_file, tree)
    pool.close()
    pool.join()

    log.info('Done ' + sys.argv[0])


if __name__ == '__main__':
    main()
