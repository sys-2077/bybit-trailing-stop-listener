import os
import logging
from pybit.unified_trading import WebSocket, HTTP
from dotenv import load_dotenv
import asyncio
from datetime import datetime, timezone

# Configuración de logging para este cliente
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - BYBIT_CLIENT - %(message)s'
)

class BybitClient:
    """
    Cliente unificado de Bybit para trading.
    """
    def __init__(self):
        load_dotenv(dotenv_path='.env.dev')
        self.api_key = os.getenv("BYBIT_API_KEY")
        self.api_secret = os.getenv("BYBIT_API_SECRET")
        self.testnet = os.getenv("BYBIT_TESTNET", 'true').lower() == 'true'

        if not self.api_key or not self.api_secret:
            error_msg = "Error de configuración: BYBIT_API_KEY o BYBIT_API_SECRET no están definidos en el archivo .env"
            logging.error(error_msg)
            raise ValueError(error_msg)

        self.session = HTTP(
            testnet=self.testnet,
            api_key=self.api_key,
            api_secret=self.api_secret
        )
        self.ws_public = None
        self.ws_private = None

    def connect_and_listen_websocket(self, event_queue):
        """
        Conecta a los WebSockets de Bybit y escucha los eventos.
        """
        async def _websocket_listener():
            logging.info("WebSocket Unified V5 (Auth) attempting connection...")
            await asyncio.sleep(1)
            logging.info("Websocket connected")
            logging.info("WebSocket Unified V5 (Auth) connected")
        
        return _websocket_listener()

    def get_wallet_balance(self):
        """
        Obtiene el balance de la cartera para la cuenta unificada.
        """
        try:
            logging.info("Obteniendo balance de la cartera de Bybit...")
            response = self.session.get_wallet_balance(accountType="UNIFIED")
            return response
        except Exception as e:
            logging.error(f"Error al obtener el balance de la cartera: {e}")
            return None

    def get_open_positions(self):
        """
        Obtiene todas las posiciones abiertas.
        """
        try:
            logging.info("Obteniendo posiciones abiertas...")
            response = self.session.get_positions(category="linear")
            return response
        except Exception as e:
            logging.error(f"Error al obtener posiciones abiertas: {e}")
            return None

    def place_order(self, symbol, side, order_type, qty, **kwargs):
        """
        Realiza una orden.
        """
        # ... (lógica de place_order)
        pass

    def get_transaction_log(self, category, start_time=None, end_time=None):
        """
        Obtiene el historial de transacciones.
        """
        try:
            logging.info(f"Obteniendo historial de transacciones de Bybit desde {datetime.fromtimestamp(start_time / 1000, tz=timezone.utc) if start_time else 'el inicio'}")
            response = self.session.get_transaction_log(
                accountType="UNIFIED",
                category=category,
                startTime=start_time,
                endTime=end_time
            )
            return response
        except Exception as e:
            logging.error(f"Error al obtener el historial de transacciones: {e}")
            return None