import json
import os

from blinkpy.auth import Auth, BlinkTwoFARequiredError
from blinkpy.blinkpy import Blink

import logging
_LOGGER = logging.getLogger(__name__)


class SessionManager:

    def __init__(self, creds_file):
        self.creds_file = creds_file

    async def login(self):
        if os.path.exists(self.creds_file):
            with open(self.creds_file, "r") as f:
                creds_loaded = json.load(f)
            auth = Auth(creds_loaded, no_prompt=True)
        else:
            username = os.environ.get("BLINK_USERNAME")
            password = os.environ.get("BLINK_PASSWORD")

            if not username or not password:
                raise OSError("BLINK_USERNAME and BLINK_PASSWORD must be set")
            auth = Auth(
                {
                    "username": os.environ["BLINK_USERNAME"],
                    "password": os.environ["BLINK_PASSWORD"],
                },
                no_prompt=True,
            )
        try:
            await auth.startup()
        except BlinkTwoFARequiredError:
            login_pin = input("Enter your 2FA PIN: ")
            await auth.complete_2fa_login(login_pin)

        creds_to_save = {
            k: v for k, v in auth.login_attributes.items() if k not in ["password"]
        }
        with open(self.creds_file, "w") as f:
            json.dump(creds_to_save, f, indent=2)

        blink = Blink(session=auth.session)
        blink.auth = auth
        blink.setup_urls()
        await blink.setup_post_verify()
        return blink
