#!/usr/bin/env python3

import sys
import json
import logging as log
from os import makedirs
from multiprocessing.dummy import Pool as ThreadPool
import requests

GDRIVE_MAGIC_KEY = 'AIzaSyC1qbk75NzWBvSaDh6KnsjjA9pIrP4lYIE'
GDRIVE_HOST = 'https://clients6.google.com'
CHUNK_SIZE = 32768
DOWNLOAD_THREADS = 10

def get_dir_tree(ses, dir_name, dir_id):
    """Return by dict with filenames and dirnames and their ids for given dir_id.
       Names are relative to dir.
       Call itself recursive for subdirs.
    """
    log.debug('get file list ' + dir_name)
    tree = dict()
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
                nested_tree = get_dir_tree(ses, item['title'], item['id'])
                for file_id, filename in nested_tree.items():
                    tree[file_id] = dir_name + '/' + filename
            else:
                tree[item['id']] = dir_name + '/' + item['title']
            tree[dir_id] = dir_name + '/' # every directory also present in ''
        if 'nextPageToken' in res.keys():
            next_page_token = res['nextPageToken']
        else:
            break # got all filenames and id's
    return tree


def download_file(_id, name):
    """ Download file and save it to name. Create dirs, if necessary.
        If name end with '/', treat it as a dir name an only create dir.
    """
    def save_response_content(response, destination):
        with open(destination, "wb+") as _f:
            for chunk in response.iter_content(CHUNK_SIZE):
                if chunk: # filter out keep-alive new chunks
                    _f.write(chunk)

    if name.endswith('/'):
        #this is folder item, not a file
        makedirs(name, exist_ok=True)
        return
    path = name.rsplit('/', maxsplit=1)[0]
    log.debug('Download ' + name + ' from ' + _id + ' path = ' + path)
    makedirs(path, exist_ok=True)
    ses = requests.Session()
    resp = ses.get('https://drive.google.com/uc?', params={'id': _id})
    resp.raise_for_status()
    for cookie_name in resp.cookies.keys():
        if cookie_name.startswith('download_warning'):
            #big file
            resp = ses.post('https://drive.google.com/uc?', params={'id': _id})
            resp.raise_for_status()
            # in response first line contain garbage. so we cut it
            _resp_json = json.loads(resp.content.decode('utf8').split('\n', maxsplit=1)[1])
            download_url = _resp_json['downloadUrl']
            resp = ses.get(download_url)
    save_response_content(resp, name)

def main():
    log.basicConfig(level=log.DEBUG)
    log.info('Start ' + sys.argv[0])
    log.info('Prepare list of files')
    ses = requests.Session() #create session for activate keep alive
    tree = get_dir_tree(ses, sys.argv[1], sys.argv[1])
    log.info('Start downloading files')

    pool = ThreadPool(DOWNLOAD_THREADS)
    pool.starmap(download_file, tree.items())
    pool.close()
    pool.join()

    log.info('Done ' + sys.argv[0])


if __name__ == '__main__':
    main()
