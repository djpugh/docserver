import pkg_resources

try:
    from py_mini_racer import py_mini_racer
except ImportError:
    py_mini_racer = False


if py_mini_racer:
    lunr_js_file = pkg_resources.resource_filename('docserver.ui.static.js', 'lunr.js')
    with open(lunr_js_file) as f:
        lunr_js = f.read()
else:
    lunr_js = ''