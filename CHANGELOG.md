# Changelog

## [2.0.0] - Refactorización Completa del Sistema

### 🎯 Nueva Funcionalidad: Sistema de Trailing Stop Automatizado

#### Cambios Mayores

**Sistema de Dos Pools Implementado:**
- **Pool de Monitoreo**: Rastrea posiciones que aún no han alcanzado el umbral de ganancia
- **Pool de Trailing Activo**: Gestiona posiciones con trailing stop activado

**WebSocket en Tiempo Real:**
- Implementada conexión real al WebSocket privado de Bybit
- Actualizaciones instantáneas de posiciones y precios
- Suscripción a canales `position` y `wallet`

#### Características Nuevas

1. **Activación Automática de Trailing Stops**
   - Se activa cuando una posición alcanza el umbral configurado (default: 0.30%)
   - Stop Loss inicial se establece automáticamente

2. **Actualización Dinámica de Stop Loss**
   - El SL se mueve automáticamente cuando el precio avanza favorablemente
   - Incrementos configurables (default: 0.50%)
   - Protege ganancias mientras permite que las posiciones corran

3. **Configuración Flexible**
   - `TRAILING_ACTIVATION_PERCENT`: Umbral de activación
   - `TRAILING_INCREMENT_PERCENT`: Incremento del trailing stop
   - Configurables por separado para máxima flexibilidad

#### Archivos Modificados

**`app/bybit_client.py`:**
- ✅ Implementado WebSocket real con autenticación
- ✅ Agregado método `set_trading_stop()` para modificar SL
- ✅ Agregado método `get_closed_pnl()` para historial de operaciones
- ✅ Callbacks para procesar eventos en tiempo real

**`app/strategy_manager.py`:**
- ✅ Reescritura completa de la clase
- ✅ Eliminado código relacionado con drawdown
- ✅ Implementados dos pools de posiciones
- ✅ Lógica de activación de trailing stop
- ✅ Lógica de actualización automática de SL
- ✅ Cálculo de PnL para LONG y SHORT
- ✅ Gestión del ciclo de vida de posiciones

**`app/main.py`:**
- ✅ Eliminada referencia a `run_balance_checker()`
- ✅ Simplificadas las tareas asíncronas
- ✅ Tres tareas concurrentes: WebSocket, Strategy Manager, Data Logger

**`docker-compose.yml`:**
- ✅ Eliminado servicio `balance_service`
- ✅ Simplificada la arquitectura a un solo servicio

#### Archivos Eliminados

- ❌ `app/balance_service.py` - Ya no es necesario
- ❌ `Dockerfile.balance_service` - Servicio removido
- ❌ `requirements.balance_service.txt` - Dependencias no necesarias

#### Archivos Nuevos

- ✅ `README.md` - Documentación completa y actualizada
- ✅ `CHANGELOG.md` - Este archivo

### 🔧 Mejoras Técnicas

1. **Arquitectura Simplificada**
   - De microservicios (2 servicios) a monolito eficiente (1 servicio)
   - Menor complejidad operacional
   - Comunicación más rápida (sin HTTP entre servicios)

2. **Rendimiento**
   - WebSocket en tiempo real (antes: polling cada 5 segundos)
   - Actualizaciones instantáneas de posiciones
   - Menor latencia en ejecución de trailing stops

3. **Logging Mejorado**
   - Emojis para mejor visualización de eventos
   - Logs más descriptivos y estructurados
   - Estados de pools visibles en tiempo real

### 📊 Flujo de Trabajo Actualizado

```
1. Bot inicia → Conecta WebSocket
2. Carga posiciones abiertas → Clasifica en pools
3. Monitoreo continuo → Recibe updates en tiempo real
4. Posición alcanza umbral → Activa trailing stop
5. Precio se mueve a favor → Actualiza SL automáticamente
6. Posición se cierra → Remueve de pools y registra
```

### 🚀 Cómo Usar

1. Configurar `.env.dev`:
```bash
BYBIT_API_KEY=tu_api_key
BYBIT_API_SECRET=tu_api_secret
BYBIT_TESTNET=true
TRAILING_ACTIVATION_PERCENT=0.30
TRAILING_INCREMENT_PERCENT=0.50
```

2. Ejecutar con Docker:
```bash
docker-compose build
docker-compose up -d
docker-compose logs -f bot_principal
```

### ⚠️ Breaking Changes

- **Eliminado**: Sistema de drawdown completo
- **Eliminado**: Servicio de balance independiente
- **Eliminado**: Verificación de balance a medianoche UTC
- **Cambiado**: Estructura de `strategy_manager.py` completamente reescrita
- **Cambiado**: Variables de entorno requeridas

### 🐛 Notas

- El sistema está optimizado para testnet de Bybit
- Para producción, cambiar `BYBIT_TESTNET=false`
- Se recomienda probar en testnet antes de usar con dinero real
- Los porcentajes son configurables según la estrategia del trader

### 📝 Pendiente

- [ ] Probar integración completa con testnet de Bybit
- [ ] Agregar tests unitarios
- [ ] Implementar métricas y monitoreo avanzado
- [ ] Agregar soporte para múltiples símbolos con configuraciones diferentes
- [ ] Dashboard web para visualización en tiempo real (opcional)

---

## [1.0.0] - Versión Inicial (Deprecada)

### Características
- Sistema de drawdown básico
- Servicio de balance independiente
- Polling de posiciones cada 5 segundos
- WebSocket placeholder (no funcional)

