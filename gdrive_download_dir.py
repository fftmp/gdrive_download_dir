#!/usr/bin/env python3

import sys
import json
import requests

print("Try to read file IDs and filenames from ", sys.argv[1])

res_file = open(sys.argv[1])
res = json.load(res_file)
res_file.close()
print("Try to download " + str(len(res['items'])) + " files")
for item in res['items']:
    print("Try to download " + item['title'])
    resp = requests.get('https://docs.google.com/uc?id=' + item['id'])
    file_jpeg = open(item['title'], 'wb+')
    file_jpeg.write(resp.content)
    file_jpeg.close()
print("Done")
