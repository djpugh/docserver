import os
import uuid

from pydantic import BaseModel, Schema, SecretStr


class ProviderConfig(BaseModel):
    session_secret: SecretStr = Schema(SecretStr(os.getenv('DOCSERVER_SESSION_SECRET', str(uuid.uuid4()))))
