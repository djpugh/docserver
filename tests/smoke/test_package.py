import os
import json
import zipfile
import tempfile

import click
import requests

PORT = os.environ.get('PORT', 8001)
HOST = os.environ.get('HOST', 'localhost')
USERNAME = os.environ.get('USERNAME')
API_TOKEN = os.environ.get('API_TOKEN')
SPECIAL_PERMISSION = "com.special/read"


def test(port, host):
    if port == 8001:
        method = "http"
    else:
        method = "https"
    base_url = f'{method}://{host}:{port}'
    r = requests.get(f'{base_url}/api/auth/token/upload', headers={'Authorization': f'Bearer {API_TOKEN}'})
    r.raise_for_status()
    print(r.content)
    token = r.json()['access_token']
    token = API_TOKEN
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

        # v 0.1.0 default permissions
        print('UPLOADING')
        values = json.dumps({'version': '0.1.0', 'name': 'test', 'repository': 'https://github.com/a', 'tags': ['python', 'demo']})
        response = requests.post(f'{base_url}/api/docs/upload', data=values,
                                 headers={'Authorization': f'Bearer {token}'})
        print(response.content.decode())
        response.raise_for_status()
        upload_url = response.content.decode().split('Location: ')[1][:-1]
        print(upload_url)
        response = requests.put(upload_url, files={'documentation': ('test-upload.zip', open(zip_fname, 'rb').read())},
                                headers={'Authorization': f'Bearer {token}'})
        print(response)
        print(response.content)
        response.raise_for_status()

        values = json.dumps({'version': '0.2.0', 'name': 'test', 'repository': 'https://github.com/a', 'tags': ['python', 'demo2']})
        response = requests.post(f'{base_url}/api/docs/upload', data=values, headers={'Authorization': f'Bearer {token}'})
        print(response.content.decode())
        response.raise_for_status()
        upload_url = response.content.decode().split('Location: ')[1][:-1]
        print(upload_url)
        response = requests.put(upload_url, files={'documentation': ('test-upload.zip', open(zip_fname, 'rb').read())},
                                headers={'Authorization': f'Bearer {token}'})
        print(response)
        print(response.content)

        values = json.dumps({'version': '0.1.0', 'name': 'test_secure', 'repository': 'https://github.com/b',
                             'tags': ['python', 'demo'], 'permissions': {'read_permission': SPECIAL_PERMISSION}})
        response = requests.post(f'{base_url}/api/docs/upload', data=values,
                                 headers={'Authorization': f'Bearer {token}'})
        print(response.content.decode())
        response.raise_for_status()
        upload_url = response.content.decode().split('Location: ')[1][:-1]
        print(upload_url)
        response = requests.put(upload_url, files={'documentation': ('test-upload.zip', open(zip_fname, 'rb').read())},
                                headers={'Authorization': f'Bearer {token}'})
        print(response)
        print(response.content)
        os.chdir(cwd)
        print('-'*20)
        response = requests.get(f'{base_url}/api/docs/list', headers={'Authorization': f'Bearer {API_TOKEN}'})
        result1 = response.json()
        print(result1)
        # assert len(result1) == 1
        requests.post(f'{base_url}/api/permissions/add', headers={'Authorization': f'Bearer {API_TOKEN}'},
                      data=json.dumps({'username': USERNAME,
                                       'permission': SPECIAL_PERMISSION}))

        response = requests.get(f'{base_url}/api/docs/list', headers={'Authorization': f'Bearer {API_TOKEN}'})
        result2 = response.json()
        print(result2)
        # assert len(result2) == 2
        requests.post(f'{base_url}/api/permissions/remove', headers={'Authorization': f'Bearer {API_TOKEN}'},
                      data=json.dumps({'username': USERNAME,
                                       'permission': SPECIAL_PERMISSION}))
        response = requests.get(f'{base_url}/api/docs/list', headers={'Authorization': f'Bearer {API_TOKEN}'})
        result1 = response.json()
        print(result1)
        # assert len(result1) == 1
        print('-'*20)
        values = json.dumps({'version': '0.1.0', 'name': 'test3', 'repository': 'https://dev.azure.com/a', 'tags': ['python', 'demo']})
        response = requests.post(f'{base_url}/api/docs/upload', data=values,
                                 headers={'Authorization': f'Bearer {token}'})
        print(response.content.decode())
        response.raise_for_status()
        upload_url = response.content.decode().split('Location: ')[1][:-1]
        print(upload_url)
        response = requests.put(upload_url, files={'documentation': ('test-upload.zip', open(zip_fname, 'rb').read())},
                                headers={'Authorization': f'Bearer {token}'})
        print(response)
        print(response.content)
        response.raise_for_status()
        print('-'*20)
        values = json.dumps({'version': '0.1.0', 'name': 'test4', 'repository': 'https://gitlab.com/a', 'tags': ['python', 'demo']})
        response = requests.post(f'{base_url}/api/docs/upload', data=values,
                                 headers={'Authorization': f'Bearer {token}'})
        print(response.content.decode())
        response.raise_for_status()
        upload_url = response.content.decode().split('Location: ')[1][:-1]
        print(upload_url)
        response = requests.put(upload_url, files={'documentation': ('test-upload.zip', open(zip_fname, 'rb').read())},
                                headers={'Authorization': f'Bearer {token}'})
        print(response)
        print(response.content)
        response.raise_for_status()
        print('-'*20)
        values = json.dumps({'version': '0.1.0', 'name': 'test5', 'repository': 'https://custom.com/a', 'tags': ['python', 'demo']})
        response = requests.post(f'{base_url}/api/docs/upload', data=values,
                                 headers={'Authorization': f'Bearer {token}'})
        print(response.content.decode())
        response.raise_for_status()
        upload_url = response.content.decode().split('Location: ')[1][:-1]
        print(upload_url)
        response = requests.put(upload_url, files={'documentation': ('test-upload.zip', open(zip_fname, 'rb').read())},
                                headers={'Authorization': f'Bearer {token}'})
        print(response)
        print(response.content)
        response.raise_for_status()


@click.command()
@click.option('--port', default=PORT)
@click.option('--host', default=HOST)
def cli(port, host):
    test(port, host)


if __name__ == "__main__":
    cli()
