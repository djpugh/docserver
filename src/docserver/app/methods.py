import os


from docserver.app.config import app_config
from docserver.app import schemas
from docserver.db.config import db_config
from docserver.db.models import Package, DocumentationVersion


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


class ApplicationMethods:

    @property
    def available_docs(self):
        if not hasattr(self, '_available_docs'):
            self._update_available_docs()
        return self._available_docs

    @staticmethod
    def _get_available_docs():
        packages = Package.read(db=db_config.local_session(), limit=None, params=None)
        for package in packages:
            if package.description is None:
                package.description = ''
        return sorted(packages, key=lambda x: x.name)

    def _update_available_docs(self):
        self._available_docs = self._get_available_docs()

    @staticmethod
    def get_versions(package: schemas.Package):
        db_package = Package.read(db_config.local_session(), package=package)
        return ['latest'] + db_package.sorted_versions

    @staticmethod
    def register_package(package: schemas.CreatePackage):
        Package.get_or_create(db_config.local_session(), package)

    @staticmethod
    def delete_package(package: schemas.Package):
        Package.delete(db_config.local_session(), package)

    def save_documentation(self, zipfile, package: schemas.CreatePackage):
        print('Saving')
        document_version = DocumentationVersion.get_or_create(db_config.local_session(), package, zipfile)
        self._update_available_docs()
        print('Updating latest')
        self.check_redirect(package)
        return document_version.url

    @staticmethod
    def check_redirect(package: schemas.Package):
        index = os.path.join(package.get_dir(), 'index.html')
        if not os.path.exists(index):
            print('Creating redirect')
            with open(index, 'w') as f:
                f.write(HTML_LATEST_REDIRECT)
                f.close()

    @staticmethod
    def make_path(path):
        required_dir = os.path.join(app_config.docs_dir, path)
        if not os.path.exists(required_dir):
            os.makedirs(required_dir)
        return required_dir
