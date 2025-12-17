"""Config flow per l'integrazione SMS Gammu Gateway."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_USERNAME, CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN, 
    DEFAULT_USERNAME, 
    DEFAULT_PASSWORD, 
    DEFAULT_PORT, 
    DEFAULT_SCAN_INTERVAL_SIGNAL,
    DEFAULT_SCAN_INTERVAL_SMS,
    CONF_SCAN_INTERVAL_SIGNAL,
    CONF_SCAN_INTERVAL_SMS
)
from .api import GammuGatewayApiClient

class GammuConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gestisce il flusso di configurazione."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Gestisce il passo iniziale dell'utente."""
        errors = {}

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            client = GammuGatewayApiClient(
                user_input[CONF_HOST],
                user_input[CONF_PORT],
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
                session
            )

            try:
                await client.get_signal()
                return self.async_create_entry(title="Gammu Gateway", data=user_input)
            except Exception:
                errors["base"] = "cannot_connect"

        data_schema = vol.Schema({
            vol.Required(CONF_HOST): str,
            vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
            vol.Optional(CONF_USERNAME, default=DEFAULT_USERNAME): str,
            vol.Optional(CONF_PASSWORD, default=DEFAULT_PASSWORD): str,
            
            # Intervallo aggiornamento segnale (sensori)
            vol.Optional(CONF_SCAN_INTERVAL_SIGNAL, default=DEFAULT_SCAN_INTERVAL_SIGNAL): int,
            
            # NUOVO: Intervallo controllo SMS (minimo 10 secondi)
            vol.Optional(CONF_SCAN_INTERVAL_SMS, default=DEFAULT_SCAN_INTERVAL_SMS): vol.All(vol.Coerce(int), vol.Range(min=10)),
        })

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )