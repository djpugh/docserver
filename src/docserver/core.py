import os
from zipfile import ZipFile

from werkzeug.utils import secure_filename
from pkg_resources import parse_version
from pkg_resources.extern.packaging.version import LegacyVersion

from docserver import db, DOCS_DIR
from docserver.db.models import Package, Language


class DocsInformation:

    def __init__(self):
        self.docs_dir = DOCS_DIR

    @property
    def available_docs(self):
        if not hasattr(self, '_available_docs'):
            self._update_available_docs()
        return self._available_docs

    def _get_available_docs(self):
        return [u.name for u in os.scandir(self.docs_dir) if u.is_dir()]

    def _update_available_docs(self):
        self._available_docs = self._get_available_docs()

    def get_versions(self, package):
        package = secure_filename(package)
        package_dir = os.path.join(self.docs_dir, package)
        if package in self.available_docs:
            return ['latest'] + sorted([u.name for u in os.scandir(package_dir) if u.is_dir() and not u.is_symlink()],
                                       key=lambda x: parse_version(x), reverse=True)

    def register_package(self, metadata):
        session = db.SessionLocal()
        print('Registering package')
        package = session.query(Package).filter_by(name=metadata.package).first()
        if package is None:
            # Need to create a package
            print('Creating package')
            language = session.query(Language).filter_by(name=metadata.language).first()
            if language is None:
                print('Creating language')
                language = Language(name=metadata.language)
                session.add(language)
                session.commit()
            print(f'Language {language}')
            package = Package(name=metadata.package, repository=metadata.repository, language_id=language.id)
            session.add(package)
            session.commit()
        print(f'Package {package}')

    def validate_metadata(self, metadata):
        parsed_version = parse_version(metadata.version)
        self.register_package(metadata)
        if isinstance(parsed_version, LegacyVersion):
            raise ValueError('Expect semantic version string (Major.Minor.Patch)')
        if not int(os.getenv('DOCSERVER_ACCEPT_ALL', '0')) and parsed_version.local is not None:
            raise ValueError('Parsed version {parsed_version} is not a clean semantic version')
        # Check that there is no seps in the package name
        path = os.path.join(secure_filename(metadata.package), secure_filename(metadata.version))
        return metadata, path

    def save_documentation(self, zipfile, metadata):
        metadata, initial_path = self.validate_metadata(metadata)
        zf = ZipFile(zipfile)
        print(initial_path)
        path = self.make_path(initial_path)
        print(path)
        for subfile in zf.namelist():
            print(subfile)
            zf.extract(subfile, path)
        zf.close()
        self._update_available_docs()
        print('Updating latest')
        self.update_latest(metadata)
        self.update_redirect(metadata)
        return self.make_url(initial_path)

    def update_latest(self, metadata):
        if self.get_versions(metadata.package)[1] == metadata.version:
            package = secure_filename(metadata.package)
            package_dir = os.path.join(self.docs_dir, package)
            latest = os.path.join(package_dir, 'latest')
            # This is the latest version so update/create the symlink
            if os.path.exists(latest):
                os.remove(latest)
            os.symlink(os.path.join(package_dir, metadata.version), latest, target_is_directory=True)
            # We also want to setup a redirect to latest here

    def update_redirect(self, metadata):
        package = secure_filename(metadata.package)
        package_dir = os.path.join(self.docs_dir, package)
        index = os.path.join(package_dir, 'index.html')
        if not os.path.exists(index):
            print('Creating redirect')
            with open(index, 'w') as f:
                f.write("""<!DOCTYPE HTML>

<meta charset="UTF-8">
<meta http-equiv="refresh" content="1; url=latest/">

<script>
  window.location.href = "latest/"
</script>
<title>Page Redirection</title>
If you are not redirected automatically, here is the <a href='latest/'>latest documentation</a>""")
                f.close()

    def make_path(self, path):
        required_dir = os.path.join(self.docs_dir, path)
        if not os.path.exists(required_dir):
            os.makedirs(required_dir)
        return required_dir

    def make_url(self, path):
        return f"/packages/{path.replace(os.path.sep, '/')}"


docs_information = DocsInformation()
