import asyncio
import logging
import os
from datetime import datetime, timezone

class StrategyManager:
    """Gestiona la estrategia de trailing stop basada en umbrales de PnL."""
    
    def __init__(self, bybit_client):
        self.bybit_client = bybit_client
        
        # Configuración desde variables de entorno
        self.trailing_activation_percent = float(os.getenv('TRAILING_ACTIVATION_PERCENT', '0.30'))
        self.trailing_increment_percent = float(os.getenv('TRAILING_INCREMENT_PERCENT', '0.50'))
        
        # Pool de monitoreo: posiciones que aún no han alcanzado el umbral
        self.monitoring_pool = {}
        
        # Pool de trailing activo: posiciones con trailing stop activado
        self.active_trailing_pool = {}
        
        logging.info(f"StrategyManager iniciado - Activación: {self.trailing_activation_percent}%, Incremento: {self.trailing_increment_percent}%")

    async def run_position_manager(self):
        """
        Bucle principal que procesa eventos de WebSocket y gestiona los trailing stops.
        """
        logging.info("Iniciando gestor de posiciones con trailing stop...")
        
        # Cargar posiciones iniciales
        await self._load_initial_positions()
        
        while True:
            try:
                # Procesar eventos de la cola del WebSocket
                event = await self.bybit_client.event_queue.get()
                
                if event['topic'] == 'position':
                    await self._process_position_event(event['data'])
                elif event['topic'] == 'wallet':
                    logging.debug(f"Evento de wallet recibido (ignorado por ahora)")
                
                self.bybit_client.event_queue.task_done()
                
            except Exception as e:
                logging.error(f"Error en el gestor de posiciones: {e}")
                logging.exception(e)
            
            await asyncio.sleep(0.1)

    async def _load_initial_positions(self):
        """
        Carga las posiciones abiertas al iniciar el bot y las agrega al monitoring_pool.
        """
        logging.info("Cargando posiciones abiertas iniciales...")
        
        try:
            response = self.bybit_client.get_open_positions()
            
            if not response or 'result' not in response:
                logging.warning("No se pudieron cargar posiciones iniciales")
                return
            
            positions = response['result'].get('list', [])
            
            for pos in positions:
                size = float(pos.get('size', 0))
                
                # Solo procesar posiciones con tamaño > 0
                if size > 0:
                    symbol = pos['symbol']
                    side = pos['side']
                    entry_price = float(pos['avgPrice'])
                    unrealized_pnl = float(pos.get('unrealisedPnl', 0))
                    mark_price = float(pos.get('markPrice', entry_price))
                    
                    # Calcular PnL en porcentaje
                    pnl_percent = self._calculate_pnl_percent(entry_price, mark_price, side)
                    
                    logging.info(f"Posición inicial encontrada: {symbol} {side} - Size: {size}, Entry: {entry_price}, PnL: {unrealized_pnl:.2f} USD ({pnl_percent:.2f}%)")
                    
                    # Verificar si ya alcanzó el umbral
                    if pnl_percent >= self.trailing_activation_percent:
                        # Agregar directamente al pool activo
                        await self._activate_trailing_stop({
                            'symbol': symbol,
                            'side': side,
                            'size': size,
                            'entry_price': entry_price,
                            'current_price': mark_price,
                            'unrealized_pnl': unrealized_pnl
                        })
                    else:
                        # Agregar al pool de monitoreo
                        self.monitoring_pool[symbol] = {
                            'size': size,
                            'side': side,
                            'entry_price': entry_price,
                            'initial_pnl_usd': unrealized_pnl,
                            'initial_pnl_percent': pnl_percent
                        }
                        logging.info(f"✓ {symbol} agregado al pool de monitoreo (PnL: {pnl_percent:.2f}%)")
            
            logging.info(f"Carga completada - Monitoreo: {len(self.monitoring_pool)}, Trailing activo: {len(self.active_trailing_pool)}")
            
        except Exception as e:
            logging.error(f"Error cargando posiciones iniciales: {e}")
            logging.exception(e)

    async def _process_position_event(self, event_data):
        """
        Procesa eventos de actualización de posiciones desde el WebSocket.
        """
        try:
            # El formato de pybit WebSocket puede variar, necesitamos extraer los datos
            if 'data' in event_data:
                positions = event_data['data']
            else:
                positions = [event_data]
            
            for pos_data in positions:
                symbol = pos_data.get('symbol')
                size = float(pos_data.get('size', 0))
                
                if not symbol:
                    continue
                
                # Si la posición está cerrada (size = 0)
                if size == 0:
                    await self._remove_position_from_pools(symbol)
                    continue
                
                # Extraer datos de la posición
                side = pos_data.get('side')
                entry_price = float(pos_data.get('avgPrice', 0))
                mark_price = float(pos_data.get('markPrice', entry_price))
                unrealized_pnl = float(pos_data.get('unrealisedPnl', 0))
                
                # Calcular PnL en porcentaje
                pnl_percent = self._calculate_pnl_percent(entry_price, mark_price, side)
                
                logging.debug(f"Update: {symbol} - Price: {mark_price}, PnL: {unrealized_pnl:.2f} USD ({pnl_percent:.2f}%)")
                
                # Determinar en qué pool está la posición
                if symbol in self.active_trailing_pool:
                    # Ya tiene trailing stop activo, actualizar
                    await self._update_trailing_stop(symbol, mark_price, side)
                    
                elif symbol in self.monitoring_pool:
                    # Está en monitoreo, verificar si alcanzó el umbral
                    if pnl_percent >= self.trailing_activation_percent:
                        logging.info(f"🎯 {symbol} alcanzó umbral de activación ({pnl_percent:.2f}% >= {self.trailing_activation_percent}%)")
                        await self._activate_trailing_stop({
                            'symbol': symbol,
                            'side': side,
                            'size': size,
                            'entry_price': entry_price,
                            'current_price': mark_price,
                            'unrealized_pnl': unrealized_pnl
                        })
                    else:
                        # Actualizar datos en monitoring pool
                        self.monitoring_pool[symbol].update({
                            'initial_pnl_usd': unrealized_pnl,
                            'initial_pnl_percent': pnl_percent
                        })
                else:
                    # Nueva posición detectada
                    logging.info(f"🆕 Nueva posición detectada: {symbol} {side} - Size: {size}, Entry: {entry_price}")
                    
                    if pnl_percent >= self.trailing_activation_percent:
                        await self._activate_trailing_stop({
                            'symbol': symbol,
                            'side': side,
                            'size': size,
                            'entry_price': entry_price,
                            'current_price': mark_price,
                            'unrealized_pnl': unrealized_pnl
                        })
                    else:
                        self.monitoring_pool[symbol] = {
                            'size': size,
                            'side': side,
                            'entry_price': entry_price,
                            'initial_pnl_usd': unrealized_pnl,
                            'initial_pnl_percent': pnl_percent
                        }
                        logging.info(f"✓ {symbol} agregado al pool de monitoreo")
        
        except Exception as e:
            logging.error(f"Error procesando evento de posición: {e}")
            logging.exception(e)

    async def _activate_trailing_stop(self, position_data):
        """
        Activa el trailing stop para una posición que alcanzó el umbral.
        Mueve la posición del monitoring_pool al active_trailing_pool.
        """
        symbol = position_data['symbol']
        side = position_data['side']
        current_price = position_data['current_price']
        entry_price = position_data['entry_price']
        
        # Remover del pool de monitoreo si existe
        if symbol in self.monitoring_pool:
            del self.monitoring_pool[symbol]
        
        # Calcular el Stop Loss inicial basado en el porcentaje de activación
        initial_sl = self._calculate_initial_sl(entry_price, side)
        
        # Agregar al pool de trailing activo
        self.active_trailing_pool[symbol] = {
            'size': position_data['size'],
            'side': side,
            'entry_price': entry_price,
            'current_price': current_price,
            'current_sl': initial_sl,
            'highest_price': current_price if side == 'Buy' else None,
            'lowest_price': current_price if side == 'Sell' else None,
            'last_sl_update': datetime.now(timezone.utc)
        }
        
        # Establecer el Stop Loss en Bybit
        self.bybit_client.set_trading_stop(symbol, initial_sl)
        
        logging.info(f"🔒 Trailing Stop ACTIVADO para {symbol} - SL inicial: {initial_sl}, Precio actual: {current_price}")
        logging.info(f"📊 Pools actuales - Monitoreo: {len(self.monitoring_pool)}, Trailing: {len(self.active_trailing_pool)}")

    async def _update_trailing_stop(self, symbol, current_price, side):
        """
        Actualiza el trailing stop de una posición activa si el precio se movió favorablemente.
        """
        if symbol not in self.active_trailing_pool:
            return
        
        position = self.active_trailing_pool[symbol]
        
        # Actualizar precio actual
        position['current_price'] = current_price
        
        should_update_sl = False
        new_sl = None
        
        if side == 'Buy':  # Posición LONG
            # Actualizar highest_price si es necesario
            if position['highest_price'] is None or current_price > position['highest_price']:
                position['highest_price'] = current_price
            
            # Verificar si el precio subió suficiente para mover el SL
            price_increase_percent = ((current_price - position['entry_price']) / position['entry_price']) * 100
            
            # El SL debe moverse cuando el precio suba un increment adicional
            threshold_for_sl_update = position['entry_price'] * (1 + (price_increase_percent / 100))
            current_sl_threshold = position['current_sl'] * (1 + (self.trailing_increment_percent / 100))
            
            if current_price >= current_sl_threshold:
                should_update_sl = True
                # Nuevo SL: precio actual menos el porcentaje de incremento
                new_sl = current_price * (1 - (self.trailing_increment_percent / 100))
        
        elif side == 'Sell':  # Posición SHORT
            # Actualizar lowest_price si es necesario
            if position['lowest_price'] is None or current_price < position['lowest_price']:
                position['lowest_price'] = current_price
            
            # Verificar si el precio bajó suficiente para mover el SL
            price_decrease_percent = ((position['entry_price'] - current_price) / position['entry_price']) * 100
            
            current_sl_threshold = position['current_sl'] * (1 - (self.trailing_increment_percent / 100))
            
            if current_price <= current_sl_threshold:
                should_update_sl = True
                # Nuevo SL: precio actual más el porcentaje de incremento
                new_sl = current_price * (1 + (self.trailing_increment_percent / 100))
        
        # Actualizar el SL si es necesario
        if should_update_sl and new_sl:
            # Asegurar que el nuevo SL es mejor que el anterior
            if (side == 'Buy' and new_sl > position['current_sl']) or \
               (side == 'Sell' and new_sl < position['current_sl']):
                
                logging.info(f"📈 Actualizando trailing stop para {symbol}: {position['current_sl']:.2f} → {new_sl:.2f} (Precio: {current_price})")
                
                # Actualizar en Bybit
                self.bybit_client.set_trading_stop(symbol, new_sl)
                
                # Actualizar localmente
                position['current_sl'] = new_sl
                position['last_sl_update'] = datetime.now(timezone.utc)

    async def _remove_position_from_pools(self, symbol):
        """
        Elimina una posición cerrada de todos los pools.
        """
        removed_from = None
        
        if symbol in self.monitoring_pool:
            del self.monitoring_pool[symbol]
            removed_from = "monitoreo"
        
        if symbol in self.active_trailing_pool:
            del self.active_trailing_pool[symbol]
            removed_from = "trailing activo"
        
        if removed_from:
            logging.info(f"❌ {symbol} cerrado y removido del pool de {removed_from}")
            logging.info(f"📊 Pools actuales - Monitoreo: {len(self.monitoring_pool)}, Trailing: {len(self.active_trailing_pool)}")

    def _calculate_pnl_percent(self, entry_price, current_price, side):
        """
        Calcula el PnL en porcentaje basado en el precio de entrada y actual.
        """
        if entry_price == 0:
            return 0.0
        
        if side == 'Buy':  # LONG
            return ((current_price - entry_price) / entry_price) * 100
        else:  # SHORT
            return ((entry_price - current_price) / entry_price) * 100

    def _calculate_initial_sl(self, entry_price, side):
        """
        Calcula el Stop Loss inicial cuando se activa el trailing stop.
        El SL inicial se coloca en el punto de entrada (breakeven).
        """
        if side == 'Buy':  # LONG
            # SL debajo del precio de entrada
            return entry_price * (1 - (self.trailing_activation_percent / 200))  # Dividido por 200 para más conservador
        else:  # SHORT
            # SL encima del precio de entrada
            return entry_price * (1 + (self.trailing_activation_percent / 200))
