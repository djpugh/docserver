from docserver import __version__

if 'untagged' in __version__ or 'unknown':
    api_version = 0
else:
    api_version = __version__.split('.')[0]
