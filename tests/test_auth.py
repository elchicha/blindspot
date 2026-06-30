from pathlib import Path

import pytest
import json
import os
from unittest.mock import MagicMock, AsyncMock, patch
from blinkpy.auth import BlinkTwoFARequiredError
from blinkpy.blinkpy import Blink


class TestSessionManager:

    @pytest.fixture
    def mock_auth(self):
        auth = MagicMock()
        auth.startup = AsyncMock()

        auth.login_attributes = {
            "username": "test@test.com",
            "token": "fake_token",
            "refresh_token": "fake_refresh",
            "password": "should_not_be_saved",
        }
        return auth
    
    @pytest.fixture
    def mock_blink(self):
        blink = MagicMock()
        blink.setup_post_verify = AsyncMock()
        return blink

    async def test_fresh_login_saves_credentials(self, tmp_path: Path, mock_auth, mock_blink):
        """No creds file exists - should authenticate and save credentials."""
        creds_file = tmp_path / "blink_creds.json"

        with patch.dict(
            os.environ,
            {"BLINK_USERNAME": "test@test.com", "BLINK_PASSWORD": "fake_password"},
        ):

            with patch("blindspot.auth.Auth", return_value=mock_auth):
                with patch("blindspot.auth.Blink", return_value=mock_blink):
                    from blindspot.auth import SessionManager

                    manager = SessionManager(creds_file=str(creds_file))
                    result = await manager.login()

            assert creds_file.exists()
            saved = json.loads(creds_file.read_text())
            assert saved["token"] == "fake_token"
            assert result == mock_blink

    async def test_loads_existing_credentials(self, tmp_path: Path, mock_auth, mock_blink):
        """Creds file exists - should load it and skip startup."""
        creds_file = tmp_path / "blink_creds.json"

        creds_file.write_text(
            json.dumps(
                {
                    "username": "test@test.com",
                    "token": "saved_token",
                    "refresh_token": "saved_refresh",
                }
            )
        )

        with patch("blindspot.auth.Auth") as mock_auth_class:
            with patch("blindspot.auth.Blink", return_value=mock_blink):
                mock_auth_class.return_value = mock_auth
                from blindspot.auth import SessionManager

                manager = SessionManager(creds_file=str(creds_file))
                await manager.login()

        mock_auth.startup.assert_called_once()
        mock_auth_class.assert_called_once_with(
            {
                "username": "test@test.com",
                "token": "saved_token",
                "refresh_token": "saved_refresh",
            },
            no_prompt=True,
        )

    async def test_2fa_required_prompts_for_pin(self, tmp_path: Path, mock_auth, mock_blink):
        """startup() raises 2FA error: should prompt for PIN and complete login."""
        creds_file = tmp_path / "blink_creds.json"

        with patch.dict(
            os.environ,
            {"BLINK_USERNAME": "test@test.com", "BLINK_PASSWORD": "fake_password"},
        ):
            with patch("builtins.input", return_value="123456"):
                with patch("blindspot.auth.Auth", return_value=mock_auth):
                    with patch("blindspot.auth.Blink", return_value=mock_blink):
                        from blindspot.auth import SessionManager

                        manager = SessionManager(creds_file=str(creds_file))
                        await manager.login()

    async def test_raises_error_when_env_vars_missing(self, tmp_path: Path, mock_blink):
        """No env vars set -> should raise OSError."""
        creds_file = tmp_path / "blink_creds.json"

        # patch env vars to be empty - no username or password
        with patch.dict(os.environ, {}, clear=True):
            with patch("blindspot.auth.Auth"):
                with patch("blindspot.auth.Blink", return_value=mock_blink):
                    from blindspot.auth import SessionManager

                    manager = SessionManager(creds_file=str(creds_file))

                    with pytest.raises(OSError):
                        await manager.login()

    async def test_password_not_saved_to_file(self, tmp_path: Path, mock_auth, mock_blink):
        """Password should never be written to the credentials file."""
        creds_file = tmp_path / "blink_creds.json"

        with patch.dict(
            os.environ,
            {"BLINK_USERNAME": "test@test.com", "BLINK_PASSWORD": "fake_password"},
        ):
            with patch("blindspot.auth.Auth", return_value=mock_auth):
                with patch("blindspot.auth.Blink", return_value=mock_blink):
                    from blindspot.auth import SessionManager

                    manager = SessionManager(creds_file=str(creds_file))
                    await manager.login()

            saved = json.loads(creds_file.read_text())
            assert "password" not in saved
