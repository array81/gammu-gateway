from __future__ import annotations
import asyncio
import logging
from typing import Any, Dict, Optional

from aiohttp import BasicAuth, ClientError
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import API_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class SmsGammuCoordinator(DataUpdateCoordinator):
    """Communication handler for SMS Gammu API."""

    def __init__(
        self,
        hass: HomeAssistant,
        session,
        host: str,
        port: int,
        username: str,
        password: str,
        update_interval: int,
    ) -> None:

        super().__init__(
            hass,
            _LOGGER,
            name="sms_gammu_coordinator",
            update_interval=None,
        )

        self.session = session
        self.host = host
        self.port = port
        self.auth = BasicAuth(username, password)
        self._update_interval = int(update_interval)

        self.base_url = f"http://{self.host}:{self.port}"

        self.data = {
            "signal": None,
            "network": None,
            "sms_list": [],
            "last_sms": None,
        }

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from the SMS Gammu gateway."""
        try:
            signal = await self._get_json("/signal")
            network = await self._get_json("/network")
            sms_list = await self._get_json("/sms")

            self.data["signal"] = signal or {}
            self.data["network"] = network or {}
            self.data["sms_list"] = sms_list or []

            if self.data["sms_list"]:
                try:
                    self.data["last_sms"] = sorted(
                        self.data["sms_list"],
                        key=lambda x: x.get("Date", ""),
                        reverse=True,
                    )[0]
                except Exception:
                    self.data["last_sms"] = self.data["sms_list"][0]
            else:
                self.data["last_sms"] = None

            return self.data

        except Exception as err:
            raise UpdateFailed(f"Error updating SMS Gammu data: {err}")

    async def _get_json(self, path: str) -> Optional[dict]:
        """Perform authenticated GET request."""
        url = f"{self.base_url}{path}"
        try:
            async with self.session.get(url, auth=self.auth, timeout=API_TIMEOUT) as resp:
                if resp.status == 200:
                    return await resp.json()
                _LOGGER.warning("Gateway returned non-200 status for %s: %s", url, resp.status)
                return None
        except ClientError as err:
            _LOGGER.error("Connection error calling %s: %s", url, err)
            return None

    async def async_config_entry_first_refresh(self):
        """Initial refresh and start background polling."""
        await self._async_do_refresh_once()
        self.hass.loop.create_task(self._background_loop())

    async def _async_do_refresh_once(self):
        try:
            data = await self._async_update_data()
            self.async_set_updated_data(data)
        except Exception as e:
            _LOGGER.error("Initial fetch failed: %s", e)

    async def _background_loop(self):
        """Repeated background updates."""
        while True:
            try:
                data = await self._async_update_data()
                self.async_set_updated_data(data)
            except Exception as err:
                _LOGGER.error("Error in SMS Gammu update loop: %s", err)
            await asyncio.sleep(self._update_interval)

    async def send_sms(self, number: str, text: str, smsc: str | None = None) -> dict:
        """Send SMS via POST request using BasicAuth."""
        url = f"{self.base_url}/sms"
        payload = {"number": number, "text": text}
        if smsc:
            payload["smsc"] = smsc

        try:
            async with self.session.post(url, json=payload, auth=self.auth, timeout=API_TIMEOUT) as resp:
                try:
                    data = await resp.json()
                except Exception:
                    data = await resp.text()
                return {"status": resp.status, "response": data}
        except ClientError as err:
            _LOGGER.error("Failed sending SMS: %s", err)
            return {"status": "error", "error": str(err)}
