"""Inizializzazione del componente SMS Gammu Gateway."""
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_USERNAME, CONF_PASSWORD

from .const import (
    DOMAIN, 
    CONF_SCAN_INTERVAL_SIGNAL, 
    CONF_SCAN_INTERVAL_SMS, 
    EVENT_GAMMU_RECEIVED,
    DEFAULT_SCAN_INTERVAL_SMS
)
from .api import GammuGatewayApiClient

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "button"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up dell'integrazione da config entry."""
    
    session = async_get_clientsession(hass)
    client = GammuGatewayApiClient(
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        session
    )

    # --- 1. Gestione Sensori (Segnale e Rete) ---
    async def async_update_data():
        """Recupera dati segnale e rete."""
        try:
            signal_data = await client.get_signal()
            network_data = await client.get_network()
            return {"signal": signal_data, "network": network_data}
        except Exception as err:
            raise UpdateFailed(f"Errore aggiornamento dati: {err}")

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="gammu_coordinator",
        update_method=async_update_data,
        update_interval=timedelta(seconds=entry.data.get(CONF_SCAN_INTERVAL_SIGNAL, 30)),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    # Salviamo anche il listener per poterlo rimuovere all'unload
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "client": client,
        "sms_listener": None 
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # --- 2. Servizio Invio SMS ---
    async def send_sms_service(call: ServiceCall):
        number = call.data.get("number")
        message = call.data.get("message")
        try:
            await client.send_sms(number, message)
            _LOGGER.info(f"SMS inviato a {number}")
        except Exception as e:
            _LOGGER.error(f"Impossibile inviare SMS: {e}")
            raise e

    hass.services.async_register(DOMAIN, "send_sms", send_sms_service)

    # --- 3. Polling Ricezione SMS (/getsms) ---
    async def check_sms_messages(now):
        """Controlla periodicamente se ci sono nuovi SMS."""
        try:
            sms_data = await client.get_last_sms()
            
            # Analizziamo la risposta. Ci aspettiamo chiavi come 'Text' e 'Number' o 'Sender'
            # Se 'Text' è vuoto o None, non c'è messaggio.
            text = sms_data.get("Text")
            
            if text:
                sender = sms_data.get("Number") or sms_data.get("Sender") or "Unknown"
                date = sms_data.get("Date") or sms_data.get("DateTime")
                state = sms_data.get("State")
                
                _LOGGER.info(f"Nuovo SMS ricevuto da {sender}: {text}")
                
                # Scateniamo l'evento
                hass.bus.async_fire(EVENT_GAMMU_RECEIVED, {
                    "sender": sender,
                    "text": text,
                    "date": date,
                    "state": state
                })
            else:
                _LOGGER.debug("Nessun nuovo SMS.")

        except Exception as e:
            # Non facciamo crashare tutto se una chiamata fallisce, solo log
            _LOGGER.warning(f"Errore durante controllo SMS: {e}")

    # Impostiamo l'intervallo
    sms_interval = entry.data.get(CONF_SCAN_INTERVAL_SMS, DEFAULT_SCAN_INTERVAL_SMS)
    
    # Avviamo il timer periodico
    remove_listener = async_track_time_interval(
        hass, 
        check_sms_messages, 
        timedelta(seconds=sms_interval)
    )
    
    # Salviamo il riferimento per cancellarlo quando scarichiamo l'integrazione
    hass.data[DOMAIN][entry.entry_id]["sms_listener"] = remove_listener

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Rimuove l'integrazione."""
    # Cancelliamo il timer degli SMS
    listener = hass.data[DOMAIN][entry.entry_id].get("sms_listener")
    if listener:
        listener()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok