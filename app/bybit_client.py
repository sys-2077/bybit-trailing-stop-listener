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
        self.ws_private = None
        self.event_queue = None
        self.last_closed_pnl_time_ms = None

    def connect_and_listen_websocket(self, event_queue):
        """
        Conecta al WebSocket privado de Bybit y escucha actualizaciones de posiciones en tiempo real.
        """
        self.event_queue = event_queue
        
        async def _websocket_listener():
            logging.info("WebSocket Unified V5 (Private) intentando conexión...")
            
            # Crear WebSocket privado con autenticación
            self.ws_private = WebSocket(
                testnet=self.testnet,
                channel_type="private",
                api_key=self.api_key,
                api_secret=self.api_secret
            )
            
            # Callback para manejar mensajes de posiciones
            def handle_position(message):
                try:
                    logging.debug(f"Mensaje de posición recibido: {message}")
                    asyncio.create_task(self.event_queue.put({
                        'topic': 'position',
                        'data': message
                    }))
                except Exception as e:
                    logging.error(f"Error procesando mensaje de posición: {e}")
            
            # Callback para manejar mensajes de wallet
            def handle_wallet(message):
                try:
                    logging.debug(f"Mensaje de wallet recibido: {message}")
                    asyncio.create_task(self.event_queue.put({
                        'topic': 'wallet',
                        'data': message
                    }))
                except Exception as e:
                    logging.error(f"Error procesando mensaje de wallet: {e}")
            
            # Suscribirse a los canales
            self.ws_private.position_stream(callback=handle_position)
            self.ws_private.wallet_stream(callback=handle_wallet)
            
            logging.info("WebSocket Unified V5 (Private) conectado exitosamente")
            logging.info("Suscrito a canales: position, wallet")
            
            # Mantener la conexión activa
            while True:
                await asyncio.sleep(1)
        
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

    def set_trading_stop(self, symbol, stop_loss, side=None):
        """
        Modifica el Stop Loss de una posición existente.
        
        Args:
            symbol: Símbolo de la posición (ej: 'BTCUSDT')
            stop_loss: Nuevo precio de Stop Loss
            side: 'Buy' o 'Sell' (opcional, pybit lo detecta automáticamente)
        """
        try:
            params = {
                "category": "linear",
                "symbol": symbol,
                "stopLoss": str(stop_loss),
                "positionIdx": 0  # 0 para modo one-way
            }
            
            logging.info(f"Modificando Stop Loss para {symbol} a {stop_loss}")
            response = self.session.set_trading_stop(**params)
            
            if response.get('retCode') == 0:
                logging.info(f"Stop Loss actualizado exitosamente para {symbol}")
            else:
                logging.error(f"Error al actualizar Stop Loss: {response}")
            
            return response
        except Exception as e:
            logging.error(f"Error al modificar Stop Loss para {symbol}: {e}")
            return None

    def get_closed_pnl(self, symbol=None, start_time=None, limit=50):
        """
        Obtiene el historial de PnL cerrado (operaciones cerradas).
        
        Args:
            symbol: Símbolo específico (opcional)
            start_time: Timestamp en milisegundos (opcional)
            limit: Límite de registros (default 50)
        """
        try:
            params = {
                "category": "linear",
                "limit": limit
            }
            
            if symbol:
                params["symbol"] = symbol
            
            if start_time:
                params["startTime"] = start_time
            elif self.last_closed_pnl_time_ms:
                params["startTime"] = self.last_closed_pnl_time_ms
            
            logging.info(f"Obteniendo historial de PnL cerrado...")
            response = self.session.get_closed_pnl(**params)
            return response
        except Exception as e:
            logging.error(f"Error al obtener PnL cerrado: {e}")
            return None

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