from __future__ import annotations

from typing import Any
from homeassistant.components.notify import BaseNotificationService

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .coordinator import SmsGammuCoordinator


async def async_get_service(hass: HomeAssistant, config: ConfigType, discovery_info=None):
    """Return notification service."""
    for entry_id, data in hass.data[DOMAIN].items():
        return SmsGammuNotificationService(data["coordinator"])
    return None


class SmsGammuNotificationService(BaseNotificationService):
    """SMS sending service."""

    def __init__(self, coordinator: SmsGammuCoordinator):
        self.coordinator = coordinator

    async def async_send_message(self, message: str = "", **kwargs: Any) -> None:
        targets = kwargs.get("target") or kwargs.get("targets")
        smsc = kwargs.get("smsc")

        if isinstance(targets, str):
            targets = [targets]

        if not targets:
            return

        for number in targets:
            await self.coordinator.send_sms(number=number, text=message, smsc=smsc)
