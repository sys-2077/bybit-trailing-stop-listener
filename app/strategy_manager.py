import asyncio
import logging
import os
import httpx
from datetime import datetime, timezone, timedelta

class StrategyManager:
    """Gestiona la lógica de la estrategia de trading (drawdown, stop loss)."""
    def __init__(self, bybit_client):
        self.bybit_client = bybit_client
        self.drawdown_percent = float(os.getenv('DRAWDOWN_PERCENT', '5'))
        self.drawdown_enabled = os.getenv('DRAWDOWN_ENABLED', 'true').lower() == 'true'
        self.initial_balance = None
        self.last_reset_day = None
        self.open_positions_metadata = {}
        self.balance_service_url = f"http://balance_service:{os.getenv('BALANCE_SERVICE_PORT', 5000)}/balance"


    async def run_balance_checker(self):
        """Bucle para obtener el balance una vez al día a medianoche UTC."""
        logging.info("Iniciando el servicio de obtención de balance diario.")
        while True:
            await self._fetch_initial_balance_from_service()
            
            now = datetime.now(timezone.utc)
            midnight_utc_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            next_midnight_utc = midnight_utc_today + timedelta(days=1)
            time_to_wait = (next_midnight_utc - now).total_seconds()
            
            logging.info(f"El balance de hoy se ha establecido. Esperando {time_to_wait:.0f} segundos hasta la próxima medianoche UTC.")
            await asyncio.sleep(time_to_wait)


    async def run_position_manager(self):
        """Bucle principal para la gestión de drawdown y posiciones."""
        while True:
            try:
                if self.drawdown_enabled and self.initial_balance is not None:
                    self._check_drawdown_violation()
                elif self.drawdown_enabled and self.initial_balance is None:
                    logging.warning("No se ha podido establecer el balance inicial. Omitiendo la verificación de drawdown.")
                
                self._manage_open_positions()

            except Exception as e:
                logging.error(f"Error en el gestor de estrategia: {e}")
                logging.exception(e)
            
            await asyncio.sleep(5)


    async def _fetch_initial_balance_from_service(self):
        """Hace la llamada al servicio local de balance con reintentos."""
        max_retries = 5
        for retry_num in range(max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(self.balance_service_url, timeout=10.0)
                    response.raise_for_status()
                    data = response.json()
                    
                    if data['status'] == 'success' and data['initial_balance'] is not None:
                        self.initial_balance = data['initial_balance']
                        self.last_reset_day = datetime.now(timezone.utc).date()
                        logging.info(f"Balance inicial del día establecido en: {self.initial_balance:.2f} USDT")
                        return
                    else:
                        logging.error(f"Intento {retry_num + 1}/{max_retries}: El servicio de balance devolvió un estado de error.")
                        await asyncio.sleep(2)
                
            except httpx.HTTPStatusError as e:
                logging.error(f"Intento {retry_num + 1}/{max_retries}: Error HTTP al obtener el balance: {e}. Reintentando...")
                await asyncio.sleep(2)
            except Exception as e:
                logging.error(f"Intento {retry_num + 1}/{max_retries}: Error al conectar con el servicio de balance: {e}. Reintentando...")
                await asyncio.sleep(2)
        
        logging.error(f"Falló la obtención del balance después de {max_retries} intentos. El valor de initial_balance seguirá siendo None.")
        self.initial_balance = None


    def _check_drawdown_violation(self):
        """Verifica si se ha superado el drawdown máximo permitido."""
        if self.initial_balance is None:
            return

        balance_info = self.bybit_client.get_wallet_balance()
        if balance_info and 'result' in balance_info and 'list' in balance_info['result']:
            usdt_account = next((acc for acc in balance_info['result']['list'] if acc['accountType'] == 'UNIFIED'), None)
            if usdt_account:
                current_equity = next((float(coin.get('equity')) for coin in usdt_account.get('coin', []) if coin['coin'] == 'USDT'), self.initial_balance)
                
                drawdown = self.initial_balance - current_equity
                max_drawdown = self.initial_balance * (self.drawdown_percent / 100)

                if drawdown > max_drawdown:
                    logging.error(f"¡ADVERTENCIA DE DRAWDOWN! Drawdown actual: {drawdown:.2f} USDT ({((drawdown/self.initial_balance)*100):.2f}%). Límite: {max_drawdown:.2f} USDT.")
                    self._close_all_positions()
                    self.initial_balance = current_equity

    def _close_all_positions(self):
        # ... (código sin cambios)
        pass

    def _manage_open_positions(self):
        # ... (código sin cambios)
        pass

    def _calculate_sl_price(self, position, pnl_level):
        # ... (código sin cambios)
        pass