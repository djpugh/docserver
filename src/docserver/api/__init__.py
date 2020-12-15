from docserver._version import get_versions

__version__ = get_versions()['version']

if 'untagged' in __version__ or 'unknown':
    api_version = 0
else:
    api_version = __version__.split('.')[0]
