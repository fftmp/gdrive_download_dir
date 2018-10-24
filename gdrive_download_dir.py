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
from os.path import exists
from multiprocessing.dummy import Pool as ThreadPool
from time import sleep, time
import shutil
import requests

GDRIVE_MAGIC_KEY = 'AIzaSyC1qbk75NzWBvSaDh6KnsjjA9pIrP4lYIE'
GDRIVE_HOST = 'https://clients6.google.com'
DOWNLOAD_THREADS = 10
DOWNLOAD_ATTEMPTS = 5
TIMEOUT = 10

def get_dir_tree(dir_name, dir_id, ses=None):
    """Return info about files and dirs inside list of dict: [{size : '', name: '', id: ''}]
       for given dir_id. Names are relative to dir. Call itself recursive for subdirs.
    """
    log.debug('get file list %s', dir_name)
    if not ses:
        ses = requests.Session()
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
                nested_tree = get_dir_tree(item['title'], item['id'], ses)
                if not nested_tree:
                    #empty folder
                    tree.append({'id' : item['id'],
                                 'name' : dir_name + '/' + item['title'] + '/',
                                 'size' : 0})
                for _it in nested_tree:
                    _it['name'] = dir_name + '/' + _it['name']
                tree.extend(nested_tree)
            else:
                tree.append({'id' : item['id'],
                             'name' : dir_name + '/' + item['title'],
                             'size' : int(item['fileSize'])})
        if 'nextPageToken' in res.keys():
            next_page_token = res['nextPageToken']
        else: # got all filenames and id's
            return tree


def download_file(id_, name, overwrite=False):
    """ Download file and save it to name. Create dirs, if necessary.
        If name end with '/', treat it as a dir name an only create dir.
    """
    if name.endswith('/'):
        #this is dir, not a file
        makedirs(name, exist_ok=True)
        return

    if exists(name) and not overwrite:
        log.debug('%s already exists. Skipping.', name)
        return

    path = name.rsplit('/', maxsplit=1)[0]
    log.debug('Download %s from %s', name, id_)
    makedirs(path, exist_ok=True)

    for i in range(DOWNLOAD_ATTEMPTS):
        try:
            session = requests.Session()
            resp = session.get('https://drive.google.com/uc?', params={'id': id_},
                               stream=True, timeout=TIMEOUT)
            resp.raise_for_status()
            for cookie_name, cookie_value in resp.cookies.items():
                if cookie_name.startswith('download_warning'):
                    log.debug('big file %s with id = %s', name, id_)
                    resp = session.get('https://drive.google.com/uc?',
                                       params={'id': id_, 'confirm': cookie_value}, stream=True)
                    resp.raise_for_status()
                    break
            with open(name, 'wb') as _f:
                resp.raw.decode_content = True
                shutil.copyfileobj(resp.raw, _f)
                return
        except (requests.exceptions.RequestException, requests.exceptions.BaseHTTPError) as _e:
            if i < DOWNLOAD_ATTEMPTS - 1:
                log.warning('%s during download file %s with id = %s. Retrying.', type(_e).__name__,
                            name, id_)
                sleep(2)
            else:
                log.error('Couldn\'t download file %s with id = %s. Skipping.', name, id_)
                return

def download_dir_recursive(src_dir_id, dst_dir):
    """ Download all files and dirs (including empty dirs) from dir with id=src_dir_id
        and save result in dst_dir.
    """
    log.info('Start downloading %s to %s', src_dir_id, dst_dir)
    begin_ts = time()
    tree = get_dir_tree(src_dir_id, dst_dir)
    log.debug('get_dir_tree executed in %d seconds', time() - begin_ts)
    total_size = sum(_it['size'] for _it in tree)

    log.info('Start downloading files. Total size = %d bytes', total_size)
    pool = ThreadPool(DOWNLOAD_THREADS)
    begin_ts = time()
    pool.starmap(download_file, [(elem['id'], elem['name']) for elem in tree])
    log.debug('parallel download_file executed in %d seconds', time() - begin_ts)
    pool.close()
    pool.join()

    log.info('Done downloading %s to %s', src_dir_id, dst_dir)


if __name__ == '__main__':
    log.basicConfig(level=log.DEBUG)
    log.getLogger("urllib3").setLevel(log.WARNING)
    download_dir_recursive(sys.argv[1], sys.argv[1])
