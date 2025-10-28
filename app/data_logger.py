import asyncio
import logging
import csv
import os
import json
from datetime import datetime, timezone, timedelta

class DataLogger:
    """Gestiona el registro de operaciones cerradas en un archivo CSV."""
    # El constructor solo espera 2 argumentos para que coincida con main.py
    def __init__(self, bybit_client, event_queue: asyncio.Queue):
        self.bybit_client = bybit_client
        self.event_queue = event_queue
    
    async def run(self):
        """Bucle principal para procesar eventos de la cola."""
        while True:
            try:
                event = await self.event_queue.get()

                if event['topic'] in ['wallet', 'position']:
                    logging.info("Evento recibido en el logger. Exportando operaciones cerradas...")
                    self._export_closed_positions_to_csv()
                
                self.event_queue.task_done()
            except Exception as e:
                logging.error(f"Error en el registrador de datos: {e}")
                logging.exception(e)
            
            await asyncio.sleep(1)

    def _export_closed_positions_to_csv(self):
        """
        Consulta las operaciones cerradas y las imprime en la consola.
        """
        try:
            response = self.bybit_client.get_closed_pnl()

            if not response or 'result' not in response or 'list' not in response['result']:
                logging.info("No hay nuevas operaciones cerradas para registrar.")
                return
            
            closed_positions = sorted(response['result']['list'], key=lambda x: int(x['createdTime']))
            if not closed_positions:
                logging.info("No hay nuevas operaciones cerradas para registrar.")
                return
            
            logging.info("-" * 80)
            logging.info("Operaciones Cerradas (Salida Temporal a Consola)")
            logging.info("-" * 80)
            
            headers = ['Contracts', 'Closing Direction', 'Qty', 'Entry Value', 'Exit Value', 'Entry Price', 'Take Profit Price', 'Stop Loss Price', 'Exit Price', 'Closed PnL', 'Filled Type', 'Open Time / UTC Time', 'Close Time / UTC Time']
            logging.info(",".join(headers))
            
            for pnl_record in closed_positions:
                symbol = pnl_record['symbol']
                closed_size = float(pnl_record.get('closedSize', 0) or 0)
                avg_entry_price = float(pnl_record.get('avgEntryPrice', 0) or 0)
                avg_exit_price = float(pnl_record.get('avgExitPrice', 0) or 0)
                closed_pnl = float(pnl_record.get('closedPnl', 0) or 0)
                exec_type = pnl_record.get('execType', '')
                created_time_ms = int(pnl_record.get('createdTime', 0))
                
                close_time_utc = datetime.fromtimestamp(created_time_ms / 1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                
                entry_value = avg_entry_price * closed_size
                exit_value = avg_exit_price * closed_size
                
                take_profit_value = str(pnl_record.get('takeProfit', 0))
                stop_loss_value = str(pnl_record.get('stopLoss', 0))

                take_profit_str = take_profit_value if float(take_profit_value) > 0 else 'N/A'
                stop_loss_str = stop_loss_value if float(stop_loss_value) > 0 else 'N/A'

                row = [
                    symbol,
                    'Unknown', 
                    str(closed_size),
                    f'{entry_value:.2f}',
                    f'{exit_value:.2f}',
                    str(avg_entry_price),
                    take_profit_str,
                    stop_loss_str,
                    str(avg_exit_price),
                    str(closed_pnl),
                    exec_type,
                    'Unknown', 
                    close_time_utc
                ]
                logging.info(",".join(row))
            
            self.bybit_client.last_closed_pnl_time_ms = int(closed_positions[-1]['createdTime']) + 1
            logging.info("-" * 80)

        except Exception as e:
            logging.error(f"Error al exportar operaciones cerradas: {e}")