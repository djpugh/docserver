import os
import json
import zipfile
import tempfile

import requests


with tempfile.TemporaryDirectory() as td:
    fname = os.path.join(td, 'index.html')
    file = open(fname, 'w')
    file.write('<h1>Hello World</h1><h2>Test</h2>')
    file.close()
    cwd = os.getcwd()
    os.chdir(td)

    zip_fname = os.path.join('test-upload.zip')
    zipf = zipfile.ZipFile(zip_fname, 'w', zipfile.ZIP_DEFLATED)
    zipf.write('index.html')
    zipf.close()

    values = json.dumps({'version': '0.1.0', 'name': 'test', 'repository': 'abc', 'tags': [{'name': 'python'}, {'name': 'demo'}]  })
    response = requests.post('http://localhost:8001/api/upload', data=values)
    print(response.content.decode())
    upload_url = response.content.decode().split('Location: ')[1][:-1]
    print(upload_url)
    response = requests.put(upload_url, files={'documentation': ('test-upload.zip', open(zip_fname, 'rb').read())})
    print(response)
    print(response.content)

    values = json.dumps({'version': '0.2.0', 'name': 'test', 'repository': 'abc', 'tags': [{'name': 'python'}, {'name': 'demo2'}]  })
    response = requests.post('http://localhost:8001/api/upload', data=values)
    print(response.content.decode())
    upload_url = response.content.decode().split('Location: ')[1][:-1]
    print(upload_url)
    response = requests.put(upload_url, files={'documentation': ('test-upload.zip', open(zip_fname, 'rb').read())})
    print(response)
    print(response.content)
    os.chdir(cwd)
