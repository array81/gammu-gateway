"""Piattaforma Sensori per Gammu Gateway."""
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import SIGNAL_STRENGTH_DECIBELS_MILLIWATT

from .const import DOMAIN, CONF_HOST

async def async_setup_entry(hass, entry, async_add_entities):
    """Configura i sensori."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    host = entry.data[CONF_HOST]

    # Definiamo i sensori da creare
    sensors = [
        GammuSignalSensor(coordinator, entry.entry_id, host),
        GammuNetworkSensor(coordinator, entry.entry_id, host, "NetworkName", "Operator", "mdi:radio-tower"),
        GammuNetworkSensor(coordinator, entry.entry_id, host, "State", "Network State", "mdi:signal-variant"),
        GammuNetworkSensor(coordinator, entry.entry_id, host, "NetworkCode", "Network Code", "mdi:numeric"),
    ]
    
    async_add_entities(sensors, True)


class GammuBaseEntity(CoordinatorEntity):
    """Classe base per definire le informazioni del dispositivo."""
    
    def __init__(self, coordinator, entry_id, host):
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._host = host

    @property
    def device_info(self):
        """Informazioni per raggruppare i sensori sotto un unico dispositivo."""
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": f"Gammu Gateway ({self._host})",
            "manufacturer": "Gammu",
            "model": "SMS Gateway",
            "configuration_url": f"http://{self._host}:5000", 
        }


class GammuSignalSensor(GammuBaseEntity, SensorEntity):
    """Sensore intensità segnale."""

    def __init__(self, coordinator, entry_id, host):
        super().__init__(coordinator, entry_id, host)
        self._attr_name = "Signal Strength"
        self._attr_unique_id = f"{entry_id}_signal_strength"
        self._attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
        self._attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS_MILLIWATT
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        """Legge il valore dal JSON 'signal'."""
        # Recupera il dizionario 'signal' dal coordinatore
        signal_data = self.coordinator.data.get("signal", {})
        # Chiave tipica Gammu: 'SignalStrength'
        return signal_data.get("SignalStrength")


class GammuNetworkSensor(GammuBaseEntity, SensorEntity):
    """Sensore generico per i dati di rete (Operatore, Stato, ecc)."""

    def __init__(self, coordinator, entry_id, host, json_key, name_suffix, icon):
        super().__init__(coordinator, entry_id, host)
        self._json_key = json_key
        self._attr_name = name_suffix
        self._attr_unique_id = f"{entry_id}_{json_key.lower()}"
        self._attr_icon = icon

    @property
    def native_value(self):
        """Legge il valore dal JSON 'network'."""
        network_data = self.coordinator.data.get("network", {})
        return network_data.get(self._json_key)