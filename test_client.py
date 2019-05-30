import os
import json
import zipfile

import requests

fname = os.path.join('index.html')
file = open(fname, 'w')
file.write('<h1>Hello World</h1><h2>Test</h2>')
file.close()

zip_fname = 'test-upload.zip'
zipf = zipfile.ZipFile(zip_fname, 'w', zipfile.ZIP_DEFLATED)
zipf.write(fname)
zipf.close()

values = json.dumps({'version': '0.1.0', 'package': 'test', 'repository': 'xyz', 'language': 'python'})
response = requests.post('http://localhost/api/upload', data=values)
print(response.content.decode())
upload_url = response.content.decode().split('Location: ')[1][:-1]
print(upload_url)
response = requests.put(upload_url, files={'documentation': ('test-upload.zip', open(zip_fname, 'rb').read())})

print(response)
print(response.content)


