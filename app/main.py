import os
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

from bybit_client import BybitClient
from strategy_manager import StrategyManager
from data_logger import DataLogger

# Configuración básica de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

async def main():
    """Función principal que inicia el bot."""
    logging.info("Iniciando Bybit Trailing Stop Bot...")

    # Cargar variables de entorno
    load_dotenv(dotenv_path='.env.dev')

    # Crear una instancia del cliente de Bybit
    bybit_client = BybitClient()

    # Crear una cola de mensajes para comunicar eventos entre tareas
    event_queue = asyncio.Queue()

    # Crear instancias de las clases de lógica separadas
    strategy_manager = StrategyManager(bybit_client)
    data_logger = DataLogger(bybit_client, event_queue)

    # Iniciar las tareas de forma concurrente
    tasks = [
        bybit_client.connect_and_listen_websocket(event_queue),
        strategy_manager.run_balance_checker(),
        strategy_manager.run_position_manager(),
        data_logger.run(),
    ]

    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        logging.info("Bot detenido por el usuario.")
    except Exception as e:
        logging.error(f"Se ha producido un error crítico: {e}")
        logging.exception(e)

if __name__ == "__main__":
    asyncio.run(main())