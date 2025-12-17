"""Piattaforma Button per Gammu Gateway."""
from homeassistant.components.button import ButtonEntity
from homeassistant.const import CONF_HOST

from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Configura il pulsante di reset."""
    client = hass.data[DOMAIN][entry.entry_id]["client"]
    host = entry.data[CONF_HOST]
    async_add_entities([GammuResetButton(client, entry.entry_id, host)], True)

class GammuResetButton(ButtonEntity):
    """Rappresentazione del pulsante di reset del modem."""

    def __init__(self, client, entry_id, host):
        self._client = client
        self._entry_id = entry_id
        self._host = host
        
        # --- MODIFICA QUI ---
        # Non usiamo più _attr_name fisso.
        # Usiamo una chiave per la traduzione:
        self._attr_translation_key = "reset_modem"
        self._attr_has_entity_name = True
        
        self._attr_unique_id = f"{entry_id}_reset_button"
        self._attr_icon = "mdi:restart"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": f"Gammu Gateway ({self._host})",
            "manufacturer": "Gammu",
            "model": "SMS Gateway",
            "configuration_url": f"http://{self._host}:5000",
        }

    async def async_press(self):
        await self._client.reset_modem()