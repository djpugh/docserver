import os
import json
import zipfile
import tempfile

import click
import requests

PORT = 8000
HOST = "localhost"


def test(port, host):
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

        values = json.dumps({'version': '0.1.0', 'name': 'test', 'repository': 'abc', 'tags': ['python', 'demo']})
        response = requests.post(f'http://{host}:{port}/api/upload', data=values,
                                 headers={'permissions': json.dumps({'permissions': ['com/write']})})
        print(response.content.decode())
        upload_url = response.content.decode().split('Location: ')[1][:-1]
        print(upload_url)
        response = requests.put(upload_url, files={'documentation': ('test-upload.zip', open(zip_fname, 'rb').read())},
                                headers={'permissions': json.dumps({'permissions': ['com/write']})})
        print(response)
        print(response.content)

        values = json.dumps({'version': '0.2.0', 'name': 'test', 'repository': 'abc', 'tags': ['python', 'demo2']})
        response = requests.post(f'http://{host}:{port}/api/upload', data=values, headers={'permissions': json.dumps({'permissions': ['com/write']})})
        print(response.content.decode())
        upload_url = response.content.decode().split('Location: ')[1][:-1]
        print(upload_url)
        response = requests.put(upload_url, files={'documentation': ('test-upload.zip', open(zip_fname, 'rb').read())},
                                headers={'permissions': json.dumps({'permissions': ['com/write']})})
        print(response)
        print(response.content)

        values = json.dumps({'version': '0.1.0', 'name': 'test_secure', 'repository': 'def',
                             'tags': ['python', 'demo'], 'permissions': {'read_permission': 'com.test/read'}})
        response = requests.post(f'http://{host}:{port}/api/upload', data=values,
                                 headers={'permissions': json.dumps({'permissions': ['com/write']})})
        print(response.content.decode())
        upload_url = response.content.decode().split('Location: ')[1][:-1]
        print(upload_url)
        response = requests.put(upload_url, files={'documentation': ('test-upload.zip', open(zip_fname, 'rb').read())},
                                headers={'permissions': json.dumps({'permissions': ['com/write']})})
        print(response)
        print(response.content)
        os.chdir(cwd)
        print('-'*20)
        response = requests.get(f'http://{host}:{port}/api/list', headers={'permissions': json.dumps({'permissions': ['com/read']})})
        result1 = response.json()
        print(result1)
        assert len(result1) == 1
        response = requests.get(f'http://{host}:{port}/api/list', headers={'permissions': json.dumps({'permissions': ['com/read', 'com.test/read']})})
        result2 = response.json()
        print(result2)
        assert len(result2) == 2


@click.command()
@click.option('--port', default=PORT)
@click.option('--host', default=HOST)
def cli(port, host):
    test(port, host)


if __name__ == "__main__":
    cli()
