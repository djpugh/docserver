import os
import json

import requests

file = open(os.path.join('test.html'), 'rb')
values = json.dumps({'version': '0.1.0', 'package': 'test', 'url': 'xyz'})
response = requests.post('http://localhost/api/v0/docs/upload', files={'documentation': file},
                         data=values, content_type='application/json'
                         )
file.close()
print(response.content)