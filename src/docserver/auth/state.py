from enum import Enum
import json
import logging
from typing import List, Union
import uuid

from pydantic import BaseModel, UrlStr
from starlette.authentication import AuthCredentials, SimpleUser, UnauthenticatedUser

from docserver.auth.abac import get_permissions
from docserver.db import models as db_models

logger = logging.getLogger(__name__)


SESSION_STORE_KEY = 'auth'


class AuthenticationOptions(Enum):
    unauthenticated = 0
    not_allowed = -1
    authenticated = 1


class User(BaseModel):

    name: str
    email: str
    username: str
    roles: List[str] = []
    groups: List[str] = []

    @property
    def permissions(self):
        mapped_permissions = get_permissions(self)
        db_user = db_models.User.read_unique(params=dict(username=self.username))
        if db_user:
            print(db_user.permissions)
            mapped_permissions += [str(u) for u in db_user.permissions if str(u) not in mapped_permissions]
        return mapped_permissions


class APIUser(BaseModel):
    permissions: List[str] = []


class AuthState(BaseModel):

    session_state: str = str(uuid.uuid4())
    redirect: Union[None, str] = None
    state: AuthenticationOptions = AuthenticationOptions.unauthenticated
    user: Union[User, APIUser] = None

    def check_session_state(self, session_state):
        if session_state != self.session_state:
            raise ValueError("Session states do not match")
        return True

    def store(self, serializer):
        # JSON and client secret to encode
        print(self)
        return serializer.dumps(self.json())

    @classmethod
    def load(cls, serializer, encoded_state=None, url=None):
        if encoded_state:
            state = json.loads(serializer.loads(encoded_state))

            if url and (not state['redirect'] or state['redirect'].endswith('/login')) and not str(url).endswith('/login'):
                logger.critical(f'Setting redirect to {url}')
                state['redirect'] = str(url)
            return cls(**state)
        else:
            return cls()

    @classmethod
    def logout(cls, serializer, session):
        state = cls.load_from_session(serializer, session)
        state.user = None
        state.state = AuthenticationOptions.unauthenticated
        session[SESSION_STORE_KEY] = state.store(serializer)

    @classmethod
    def load_from_session(cls, serializer, session, url=None):
        return cls.load(serializer, session.get(SESSION_STORE_KEY, None), url=url)

    def save_to_session(self, serializer, session):
        session[SESSION_STORE_KEY] = self.store(serializer)
        return session

    def is_authenticated(self):
        return self.user is not None and self.state == AuthenticationOptions.authenticated

    @property
    def authenticated_user(self):
        if self.is_authenticated():
            if isinstance(self.user, User):
                return SimpleUser(self.user.email)
            else:
                return SimpleUser('APIUser')
        else:
            return UnauthenticatedUser()

    @property
    def credentials(self):
        if self.user and self.is_authenticated():
            return AuthCredentials(['authenticated'] + self.user.permissions)
        else:
            return AuthCredentials()
