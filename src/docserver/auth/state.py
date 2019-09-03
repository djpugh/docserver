from enum import Enum
import logging
from typing import List
import uuid

from pydantic import BaseModel, UrlStr
from starlette.authentication import SimpleUser, AuthCredentials


logger = logging.getLogger(__name__)


SESSION_STORE_KEY = 'auth'


class AuthenticationOptions(Enum):
    unauthenticated = 0
    not_allowed = -1
    authenticated = 1


class User(BaseModel):

    name: str
    email: str
    roles: List[str]

    @property
    def permissions(self):
        return []


class AuthState(BaseModel):

    session_state: str = str(uuid.uuid4())
    redirect: UrlStr = '/'
    state: AuthenticationOptions = AuthenticationOptions.unauthenticated
    user: User = None

    def check_session_state(self, session_state):
        if session_state != self.session_state:
            raise ValueError("Session states do not match")
        return True

    def store(self, serializer):
        # JSON and client secret to encode
        return serializer.dumps(self.json())

    @classmethod
    def load(cls, serializer, encoded_state=None):
        if encoded_state:
            return cls(**serializer.loads(encoded_state))
        else:
            return cls()

    @classmethod
    def logout(cls, serializer, session):
        state = cls.load_from_session(serializer, session)
        state.user = None
        state.state = AuthenticationOptions.unauthenticated
        session[SESSION_STORE_KEY] = state.store(serializer)

    @classmethod
    def load_from_session(cls, serializer, session):
        return cls.load(serializer, session.get(SESSION_STORE_KEY, None))

    def is_authenticated(self):
        return self.user is not None and self.state == AuthenticationOptions.authenticated

    @property
    def authenticated_user(self):
        return SimpleUser(self.user.email)

    @property
    def credentials(self):
        return AuthCredentials(self.user.permissions)
