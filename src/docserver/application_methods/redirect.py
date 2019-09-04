import os
import logging

from docserver.api import schemas


logger = logging.getLogger(__name__)


HTML_LATEST_REDIRECT = """
<!DOCTYPE HTML>

<meta charset="UTF-8">
<meta http-equiv="refresh" content="1; url=latest/">

<script>
  window.location.href = "latest/"
</script>
<title>Page Redirection</title>
If you are not redirected automatically, here is the <a href='latest/'>latest documentation</a>
"""


def check_redirect(package: schemas.Package):
    index = os.path.join(package.get_dir(), 'index.html')
    if not os.path.exists(index):
        logger.debug(f'Creating redirect for {package}')
        with open(index, 'w') as f:
            f.write(HTML_LATEST_REDIRECT)
            f.close()
