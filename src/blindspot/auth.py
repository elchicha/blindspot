import json
import os

from blinkpy.auth import Auth, BlinkTwoFARequiredError
from blinkpy.blinkpy import Blink

import logging

_LOGGER = logging.getLogger(__name__)


class SessionManager:
    USERNAME_ENV_VAR = "BLINK_USERNAME"
    PASSWORD_ENV_VAR = "BLINK_PASSWORD"
    EXCLUDED_CREDENTIAL_FIELDS = {"password"}
    CREDENTIALS_ENCODING = "utf-8"

    def __init__(self, creds_file):
        self.creds_file = creds_file

    async def login(self):
        auth = self._create_auth()
        await self._startup_auth(auth)
        self._save_credentials(auth)
        return await self._create_blink_client(auth)

    def _create_auth(self):
        if os.path.exists(self.creds_file):
            return Auth(self._load_cached_credentials(), no_prompt=True)

        return Auth(self._load_environment_credentials(), no_prompt=True)

    def _load_cached_credentials(self):
        _LOGGER.info("Loading cached credentials at %s", self.creds_file)
        with open(self.creds_file, "r") as credentials_file:
            return json.load(credentials_file)

    def _load_environment_credentials(self):
        _LOGGER.info("Using environment stored credentials.")
        username = os.environ.get(self.USERNAME_ENV_VAR)
        password = os.environ.get(self.PASSWORD_ENV_VAR)

        if not username or not password:
            _LOGGER.error("Environment credentials missing.")
            raise OSError("BLINK_USERNAME and BLINK_PASSWORD must be set")

        return {
            "username": username,
            "password": password,
        }

    @staticmethod
    async def _startup_auth(auth):
        try:
            _LOGGER.info("Starting Authorization request through blinkpy")
            await auth.startup()
        except BlinkTwoFARequiredError:
            _LOGGER.debug("Blink two-factor-authentication code requested")
            login_pin = input("Enter your 2FA PIN: ")
            await auth.complete_2fa_login(login_pin)

    def _save_credentials(self, auth):
        credentials_to_save = {
            key: value
            for key, value in auth.login_attributes.items()
            if key not in self.EXCLUDED_CREDENTIAL_FIELDS
        }

        with open(
            self.creds_file, "w", encoding=self.CREDENTIALS_ENCODING
        ) as credentials_file:
            json.dump(credentials_to_save, credentials_file, indent=2)

    @staticmethod
    async def _create_blink_client(auth):
        blink = Blink(session=auth.session)
        blink.auth = auth
        blink.setup_urls()
        await blink.setup_post_verify()
        return blink
