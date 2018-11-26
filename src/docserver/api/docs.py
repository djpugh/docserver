import os
import json
from tempfile import TemporaryDirectory
import uuid

from flask import request
from werkzeug.datastructures import FileStorage
from flask_restplus import Resource, Namespace, fields
from itsdangerous import URLSafeSerializer

from docserver.core import docs_information

s = URLSafeSerializer(os.getenv('DOCSERVER_KEY', 'random'), salt=os.getenv('DOCSERVER_SALT', 'salt'))
api = Namespace('docs', description='Get and check available documentation')

upload_parser = api.parser()
upload_parser.add_argument('documentation', location='files',
                           type=FileStorage, required=True)


package_model = api.model('package', {
    'package': fields.String(required=True),
    'version': fields.String(required=True),
    'repository': fields.String(required=True),
    'customer': fields.String(required=True),
    'language': fields.String(required=True)
})


@api.route('/list')
class PackagesAvailable(Resource):

    def get(self):
        """
        List available packages
        """
        return docs_information.available_docs


@api.route('/<package>/versions')
class PackageVersionsAvailable(Resource):

    def get(self, package):
        """
        List available versions of a package
        """
        return docs_information.get_versions(package)


# Lets add the ability to upload a package


@api.route('/upload')
class PackageUploadRegister(Resource):

    @api.expect(package_model, validate=True)
    def post(self):
        """
        Register a package upload
        """
        # We are going to return a redirect with an id that is encrypted based on a server secret key
        metadata = request.get_json()
        metadata = docs_information.validate_metadata(metadata)
        metadata.pop('path')
        return f"Location: {request.base_url}/{s.dumps(metadata)}", 200


@api.route('/upload/<upload_id>')
class PackageUpload(Resource):

    @api.expect(upload_parser, validate=True)
    def put(self, upload_id):
        package_metadata = s.loads(upload_id)
        print(package_metadata)
        print(sorted(list(package_metadata.keys())))
        if sorted(list(package_metadata.keys())) == ['customer', 'language', 'package', 'repository', 'version']:
            args = upload_parser.parse_args()
            uploaded_docs = args['documentation']  # This is FileStorage instance
            if os.path.splitext(uploaded_docs.filename)[-1] == '.zip':
                with TemporaryDirectory() as td:
                    filename = os.path.join(td, f'{uuid.uuid4()}.zip')
                    print(filename)
                    with open(filename, 'wb') as f:
                        uploaded_docs.save(f)
                        f.close()
                    url = docs_information.save_documentation(filename, package_metadata)
                return url, 201
        return 400
