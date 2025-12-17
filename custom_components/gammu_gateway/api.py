"""API Client per SMS Gammu Gateway."""
import logging
import aiohttp
import async_timeout

_LOGGER = logging.getLogger(__name__)

class GammuGatewayApiClient:
    """Client API per comunicare con il gateway."""

    def __init__(self, host, port, username, password, session):
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._session = session
        self._base_url = f"http://{host}:{port}"

    async def get_signal(self):
        """Ottiene il livello del segnale."""
        return await self._api_wrapper("GET", f"{self._base_url}/signal")

    async def get_network(self):
        """Ottiene le informazioni sulla rete."""
        return await self._api_wrapper("GET", f"{self._base_url}/network")

    async def get_last_sms(self):
        """Ottiene l'ultimo SMS ricevuto e lo rimuove dalla coda del gateway."""
        # Endpoint indicato da te per la lettura (e cancellazione) dell'ultimo SMS
        return await self._api_wrapper("GET", f"{self._base_url}/getsms")

    async def send_sms(self, number, message):
        """Invia un SMS."""
        payload = {"number": number, "text": message}
        return await self._api_wrapper("POST", f"{self._base_url}/sms", json_data=payload)

    async def reset_modem(self):
        """Invia il comando di reset al modem."""
        return await self._api_wrapper("GET", f"{self._base_url}/reset")

    async def _api_wrapper(self, method, url, json_data=None):
        """Esegue la chiamata HTTP gestendo l'autenticazione Basic."""
        auth = aiohttp.BasicAuth(self._username, self._password)
        
        try:
            async with async_timeout.timeout(10):
                if method == "GET":
                    response = await self._session.get(url, auth=auth)
                else:
                    response = await self._session.post(url, auth=auth, json=json_data)
                
                if response.status == 401:
                    raise Exception("Errore di autenticazione: Username o Password errati")
                
                # Per il reset o getsms potremmo ricevere risposte diverse, ma 200 è lo standard
                if response.status != 200:
                    text = await response.text()
                    raise Exception(f"Errore API ({response.status}): {text}")

                try:
                    return await response.json()
                except:
                    # Se la risposta non è JSON (es. un OK testuale), torniamo un dizionario vuoto o lo stato
                    return {"status": "ok", "raw": await response.text()}

        except aiohttp.ClientError as err:
            _LOGGER.error("Errore di connessione al Gammu Gateway: %s", err)
            raise Exception(f"Errore di connessione: {err}")
        except Exception as err:
            _LOGGER.error("Errore generico API: %s", err)
            raise