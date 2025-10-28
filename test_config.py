#!/usr/bin/env python3
"""
Script de verificación de configuración para el bot de trailing stop.
Verifica que las credenciales y configuración sean válidas antes de iniciar el bot.
"""

import os
from dotenv import load_dotenv
from pybit.unified_trading import HTTP

def test_configuration():
    """Prueba la configuración del bot."""
    print("=" * 60)
    print("VERIFICACIÓN DE CONFIGURACIÓN - Bybit Trailing Stop Bot")
    print("=" * 60)
    
    # Cargar variables de entorno
    load_dotenv(dotenv_path='.env.dev')
    
    # 1. Verificar variables de entorno requeridas
    print("\n1. Verificando variables de entorno...")
    
    required_vars = {
        'BYBIT_API_KEY': os.getenv('BYBIT_API_KEY'),
        'BYBIT_API_SECRET': os.getenv('BYBIT_API_SECRET'),
        'BYBIT_TESTNET': os.getenv('BYBIT_TESTNET', 'true'),
        'TRAILING_ACTIVATION_PERCENT': os.getenv('TRAILING_ACTIVATION_PERCENT', '0.30'),
        'TRAILING_INCREMENT_PERCENT': os.getenv('TRAILING_INCREMENT_PERCENT', '0.50')
    }
    
    missing_vars = []
    for var_name, var_value in required_vars.items():
        if var_name in ['BYBIT_API_KEY', 'BYBIT_API_SECRET'] and not var_value:
            print(f"   ❌ {var_name}: NO CONFIGURADA")
            missing_vars.append(var_name)
        else:
            masked_value = var_value
            if var_name in ['BYBIT_API_KEY', 'BYBIT_API_SECRET'] and var_value:
                masked_value = var_value[:4] + "..." + var_value[-4:] if len(var_value) > 8 else "***"
            print(f"   ✅ {var_name}: {masked_value}")
    
    if missing_vars:
        print(f"\n❌ ERROR: Variables faltantes: {', '.join(missing_vars)}")
        print("   Por favor configura el archivo .env.dev")
        return False
    
    # 2. Verificar conexión a Bybit
    print("\n2. Verificando conexión a Bybit API...")
    
    try:
        api_key = required_vars['BYBIT_API_KEY']
        api_secret = required_vars['BYBIT_API_SECRET']
        testnet = required_vars['BYBIT_TESTNET'].lower() == 'true'
        
        session = HTTP(
            testnet=testnet,
            api_key=api_key,
            api_secret=api_secret
        )
        
        mode = "TESTNET" if testnet else "PRODUCCIÓN"
        print(f"   ℹ️  Modo: {mode}")
        
        # Probar obteniendo el balance
        response = session.get_wallet_balance(accountType="UNIFIED")
        
        if response.get('retCode') == 0:
            print("   ✅ Conexión exitosa a Bybit API")
            
            # Mostrar balance
            if 'result' in response and 'list' in response['result']:
                accounts = response['result']['list']
                for account in accounts:
                    if account.get('accountType') == 'UNIFIED':
                        coins = account.get('coin', [])
                        for coin in coins:
                            if coin['coin'] == 'USDT':
                                balance = float(coin.get('walletBalance', 0))
                                equity = float(coin.get('equity', 0))
                                print(f"   💰 Balance USDT: {balance:.2f} (Equity: {equity:.2f})")
        else:
            print(f"   ❌ Error en la respuesta de Bybit: {response}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error al conectar con Bybit: {e}")
        return False
    
    # 3. Verificar posiciones abiertas
    print("\n3. Verificando posiciones abiertas...")
    
    try:
        response = session.get_positions(category="linear")
        
        if response.get('retCode') == 0:
            positions = response['result'].get('list', [])
            open_positions = [p for p in positions if float(p.get('size', 0)) > 0]
            
            if open_positions:
                print(f"   ✅ {len(open_positions)} posición(es) abierta(s) detectada(s)")
                for pos in open_positions:
                    symbol = pos['symbol']
                    side = pos['side']
                    size = pos['size']
                    entry = pos['avgPrice']
                    unrealized_pnl = float(pos.get('unrealisedPnl', 0))
                    print(f"      • {symbol} {side} - Size: {size}, Entry: {entry}, PnL: {unrealized_pnl:.2f} USD")
            else:
                print("   ℹ️  No hay posiciones abiertas actualmente")
                print("   El bot estará listo para monitorear cuando abras posiciones")
        else:
            print(f"   ⚠️  No se pudieron obtener posiciones: {response}")
            
    except Exception as e:
        print(f"   ⚠️  Error al obtener posiciones: {e}")
    
    # 4. Verificar configuración de trailing stop
    print("\n4. Verificando configuración de trailing stop...")
    
    try:
        activation = float(required_vars['TRAILING_ACTIVATION_PERCENT'])
        increment = float(required_vars['TRAILING_INCREMENT_PERCENT'])
        
        print(f"   ✅ Umbral de activación: {activation}%")
        print(f"   ✅ Incremento de trailing: {increment}%")
        
        # Ejemplo práctico
        print(f"\n   📚 Ejemplo práctico:")
        example_entry = 50000
        print(f"      - Entrada en BTCUSDT: ${example_entry:,.2f}")
        
        activation_price = example_entry * (1 + activation / 100)
        print(f"      - Trailing se activa en: ${activation_price:,.2f} (+{activation}%)")
        
        first_sl_update = activation_price * (1 + increment / 100)
        print(f"      - Primer update de SL cuando precio llegue a: ${first_sl_update:,.2f}")
        
        new_sl = activation_price
        print(f"      - Nuevo SL se colocará en: ${new_sl:,.2f}")
        
    except ValueError as e:
        print(f"   ❌ Error en configuración de porcentajes: {e}")
        return False
    
    # Resumen final
    print("\n" + "=" * 60)
    print("✅ VERIFICACIÓN COMPLETADA")
    print("=" * 60)
    print("\n🚀 Todo está configurado correctamente!")
    print("   Puedes iniciar el bot con:")
    print("   • Docker: docker-compose up -d")
    print("   • Local:  python app/main.py")
    print("\n📊 El bot:")
    print("   • Monitoreará posiciones en tiempo real vía WebSocket")
    print("   • Activará trailing stops cuando alcancen el umbral")
    print("   • Actualizará SL automáticamente para proteger ganancias")
    print("\n" + "=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        success = test_configuration()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Verificación cancelada por el usuario")
        exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

