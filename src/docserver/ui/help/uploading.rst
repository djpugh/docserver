Uploading Documentation
***********************


API
---

See `Openapi docs </api/docs>`_ for the detailed API interface. There is a module available on pypi :pypi:`docsclient` which provides a client for accessing the documentation server.
Alternatively, the REST api can be used directly.

Expected Format
---------------

The expected format is a zip file containing the prebuilt HTML information directly (e.g. it should contain an ``index.html`` file).

Authentication
--------------

If authentication is enabled, accessing the API will require an authentication token.