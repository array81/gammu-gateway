"""Costanti per l'integrazione SMS Gammu Gateway."""

DOMAIN = "gammu_gateway"

CONF_HOST = "host"
CONF_PORT = "port"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"

# Intervallo per aggiornare i sensori (segnale, rete)
CONF_SCAN_INTERVAL_SIGNAL = "scan_interval_signal"

# NUOVO: Intervallo per controllare nuovi SMS
CONF_SCAN_INTERVAL_SMS = "scan_interval_sms"

DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "password"
DEFAULT_PORT = 5000

DEFAULT_SCAN_INTERVAL_SIGNAL = 30
DEFAULT_SCAN_INTERVAL_SMS = 20 # Default come suggerito dal tuo esempio

# Evento lanciato quando arriva un SMS
EVENT_GAMMU_RECEIVED = "gammu_gateway_sms_received"