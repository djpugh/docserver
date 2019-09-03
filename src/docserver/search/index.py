import json
import os

from bs4 import BeautifulSoup

from docserver.api import schemas
from docserver.config import config
from docserver.search import lunr_js, py_mini_racer
from docserver.storage.filesystem import make_path


def get_search_index_js(packages):
    search_index = {}
    for package in packages:
        search_index.update(package.search_index)
    docs_js = f"""var store = {json.dumps(search_index)}"""
    search_index_js = f"""
                      {docs_js}
                      """ \
        """
        var idx = lunr(function () {
                        this.ref('link')
                        this.field('body')
                        this.field('tags')
                        this.field('description')
                        this.field('name')
                        this.field('version')
                        this.field('repository')
                        Object.keys(store).forEach(function(key) {
                              this.add(store[key])
                        }, this)
                       })"""
    if py_mini_racer:
        ctx = py_mini_racer.MiniRacer()
        ctx.eval(lunr_js)
        ctx.eval(search_index_js)
        search_index = ctx.eval("""JSON.stringify(idx)""")
        search_index_js = f"""{docs_js}\nvar idx = lunr.Index.load(JSON.parse('{search_index}'))"""
    return search_index_js


def get_index_filename(name, version):
    return os.path.join(config.search_index_dir, f'{name}-{version}.json')


def save_index(package, index):
    # Save this as a JSON
    make_path(config.search_index_dir)
    index_filename = get_index_filename(package.name, package.version)
    with open(index_filename, 'w') as f:
        json.dump(index, f)


def build_index(package: schemas.CreatePackage):
    url = f'{config.package_url_slug}/{package.name}/{package.version}'
    index = {}
    base_dir = os.path.join(package.get_dir(), package.version)
    tags = []
    for tag in package.tags:
        if isinstance(tag, str):
            tags.append(tag)
        else:
            tags.append(tag.name)
    tag_str = ';'.join(tags)
    for (root, _, files) in os.walk(base_dir):
        for filename in files:
            if filename.endswith('.html'):
                filepath = os.path.join(root, filename)
                with open(filepath) as f:
                    soup = BeautifulSoup(f.read(), features="html.parser")
                    # Build the link
                    link = f'{url}/{os.path.relpath(filepath, base_dir)}'.replace(os.path.sep, '/')
                    if soup.title:
                        title = soup.title.string
                    else:
                        title = os.path.split(filename)[-1]
                    doc = dict(body=soup.get_text(' '), link=link, title=title)
                    doc['tags'] = tag_str
                    doc['description'] = package.description
                    doc['name'] = package.name
                    doc['repository'] = package.repository
                    doc['root_url'] = url
                    doc['version'] = package.version
                    index[doc['link']] = doc
    return index
