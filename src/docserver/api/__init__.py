from docserver.api.base import api
from docserver.api.base import blueprint  # noqa F401
from docserver.api.docs import api as docs_api


api.add_namespace(docs_api, path='/docs')
