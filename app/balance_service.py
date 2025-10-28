import os
from flask import Flask, jsonify
import logging
from bybit_client import BybitClient
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

# Cargar variables de entorno
load_dotenv(dotenv_path='.env.dev')

# Configuración de logging para este servicio
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - BALANCE_SERVICE - %(message)s'
)

app = Flask(__name__)
bybit_client = BybitClient()

# Nueva variable de entorno para controlar el logging detallado
LOG_CALCULATION_BREAKDOWN = os.getenv('LOG_CALCULATION_BREAKDOWN', 'false').lower() == 'true'

def get_historical_balance():
    """
    Calcula el balance de la cuenta a las 00:00 UTC del día actual
    usando el balance actual y las transacciones de hoy.
    """
    now = datetime.now(timezone.utc)
    midnight_utc_today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Paso 1: Obtener el balance actual de la cartera (balance realizado)
    balance_info = bybit_client.get_wallet_balance()
    if not balance_info or 'result' not in balance_info or 'list' not in balance_info['result']:
        logging.error("No se pudo obtener el balance actual de la cuenta.")
        return None

    usdt_account = next((acc for acc in balance_info['result']['list'] if acc['accountType'] == 'UNIFIED'), None)
    if not usdt_account:
        logging.error("No se encontró la cuenta unificada en el balance.")
        return None
    
    current_balance = next((float(coin.get('walletBalance')) for coin in usdt_account.get('coin', []) if coin['coin'] == 'USDT'), None)
    if current_balance is None:
        logging.error("No se pudo encontrar el balance de USDT en la cuenta.")
        return None
    
    if LOG_CALCULATION_BREAKDOWN:
        logging.info(f"Paso 1: Balance actual de la cartera (realizado): {current_balance:.2f} USDT")

    # Paso 2: Obtener el historial de transacciones desde las 00:00 UTC
    start_time_ms = int(midnight_utc_today.timestamp() * 1000)
    
    transactions = bybit_client.get_transaction_log(category="linear", start_time=start_time_ms)
    
    if not transactions or 'result' not in transactions or 'list' not in transactions['result']:
        if LOG_CALCULATION_BREAKDOWN:
            logging.warning("No se encontraron transacciones con PnL realizado desde las 00:00 UTC. Usando el balance actual como balance inicial.")
        return current_balance

    # Paso 3: Sumar el cambio de balance por PnL de operaciones cerradas
    realized_pnl_change = 0.0
    if LOG_CALCULATION_BREAKDOWN:
        logging.info("Paso 2: Sumando PnL de transacciones cerradas desde las 00:00 UTC...")
    for tx in transactions['result']['list']:
        if tx.get('coin') == 'USDT' and tx.get('type') == 'REALIZED_PNL':
            amount = float(tx.get('amount', 0))
            realized_pnl_change += amount
            if LOG_CALCULATION_BREAKDOWN:
                logging.info(f" - Encontrada transacción de PnL realizado: {amount:+.2f} USDT. Total acumulado: {realized_pnl_change:+.2f} USDT")

    if LOG_CALCULATION_BREAKDOWN:
        logging.info(f"Paso 3: Total del PnL realizado del día: {realized_pnl_change:+.2f} USDT")

    # Paso 4: Calcular el balance histórico
    historical_balance = current_balance - realized_pnl_change
    
    if LOG_CALCULATION_BREAKDOWN:
        logging.info(f"Paso 4: Balance inicial de las 00:00 UTC = {current_balance:.2f} - ({realized_pnl_change:+.2f}) = {historical_balance:.2f} USDT")
    
    return historical_balance


@app.route('/balance', methods=['GET'])
def get_daily_initial_balance():
    logging.info("Solicitud recibida para obtener el balance inicial del día (00:00 UTC).")
    
    try:
        initial_balance = get_historical_balance()
        if initial_balance is not None:
            logging.info(f"Balance inicial del día calculado y establecido: {initial_balance:.2f} USDT")
            return jsonify({'initial_balance': initial_balance, 'status': 'success'})
        else:
            logging.error("No se pudo calcular el balance histórico.")
            return jsonify({'initial_balance': None, 'status': 'error'}), 500
    except Exception as e:
        logging.error(f"Error al calcular el balance histórico: {e}")
        logging.exception(e)
        return jsonify({'initial_balance': None, 'status': 'error'}), 500


if __name__ == '__main__':
    port = int(os.environ.get('BALANCE_SERVICE_PORT', 5000))
    app.run(host='0.0.0.0', port=port)