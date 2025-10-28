# Bybit Trailing Stop Bot

Bot automatizado de trading para Bybit que implementa un sistema inteligente de trailing stops basado en umbrales de PnL.

## 🎯 Funcionalidad Principal

El bot monitorea en tiempo real las posiciones abiertas en Bybit y gestiona automáticamente trailing stops cuando las posiciones alcanzan ciertos umbrales de ganancia.

### Sistema de Dos Pools

1. **Pool de Monitoreo** (`monitoring_pool`): 
   - Posiciones que aún no han alcanzado el umbral de activación
   - Se monitorea continuamente el PnL de cada posición
   - Cuando una posición alcanza el umbral configurado (ej: +0.30%), se mueve al pool activo

2. **Pool de Trailing Activo** (`active_trailing_pool`):
   - Posiciones con trailing stop activado
   - El Stop Loss se actualiza automáticamente cuando el precio se mueve favorablemente
   - Incrementos configurables (ej: +0.50% por cada movimiento)

## 🔧 Configuración

### Variables de Entorno

Crea un archivo `.env.dev` con las siguientes variables:

```bash
# Credenciales de Bybit
BYBIT_API_KEY=tu_api_key_aqui
BYBIT_API_SECRET=tu_api_secret_aqui
BYBIT_TESTNET=true

# Configuración del Trailing Stop
TRAILING_ACTIVATION_PERCENT=0.30  # Umbral para activar trailing stop (%)
TRAILING_INCREMENT_PERCENT=0.50   # Incremento del SL cuando el precio se mueve (%)
```

### Parámetros Explicados

- **TRAILING_ACTIVATION_PERCENT**: Porcentaje de ganancia que debe alcanzar una posición para activar el trailing stop
  - Ejemplo: 0.30 = cuando la posición tenga +0.30% de ganancia, se activa el trailing stop

- **TRAILING_INCREMENT_PERCENT**: Porcentaje de movimiento necesario para actualizar el Stop Loss
  - Ejemplo: 0.50 = cada vez que el precio se mueva 0.50% a favor, el SL se actualiza 0.50%

## 🚀 Instalación y Ejecución

```bash
# Construir las imágenes
docker-compose build

# Iniciar el bot
docker-compose up -d

# Ver logs en tiempo real
docker-compose logs -f bot_principal

# Detener el bot
docker-compose down
```


## 📊 Flujo de Trabajo

1. **Inicio**: El bot se conecta al WebSocket privado de Bybit
2. **Carga Inicial**: Carga todas las posiciones abiertas y las clasifica
3. **Monitoreo Continuo**: 
   - Recibe actualizaciones en tiempo real de precios y posiciones
   - Calcula PnL constantemente
4. **Activación**: Cuando una posición alcanza el umbral:
   - Se mueve del pool de monitoreo al pool activo
   - Se establece un Stop Loss inicial (breakeven o cerca)
5. **Trailing**: Para posiciones en el pool activo:
   - Si el precio se mueve favorablemente, el SL se actualiza
   - El SL siempre se mueve en dirección a proteger ganancias
6. **Cierre**: Cuando una posición se cierra:
   - Se elimina de todos los pools
   - Se registra en los logs

## 📝 Logs

El bot proporciona logs detallados de todas las operaciones:

```
✓ BTCUSDT agregado al pool de monitoreo (PnL: 0.15%)
🎯 ETHUSDT alcanzó umbral de activación (0.32% >= 0.30%)
🔒 Trailing Stop ACTIVADO para ETHUSDT - SL inicial: 2850.5
📈 Actualizando trailing stop para ETHUSDT: 2850.5 → 2865.2
❌ BTCUSDT cerrado y removido del pool de monitoreo
📊 Pools actuales - Monitoreo: 2, Trailing: 1
```

## 🏗️ Arquitectura

```
app/
├── main.py              # Punto de entrada principal
├── bybit_client.py      # Cliente WebSocket y API de Bybit
├── strategy_manager.py  # Lógica de trailing stops y gestión de pools
└── data_logger.py       # Registro de operaciones cerradas
```

### Componentes Principales

- **BybitClient**: Maneja la conexión WebSocket y las llamadas a la API REST
- **StrategyManager**: Implementa la lógica de los dos pools y trailing stops
- **DataLogger**: Registra las operaciones cerradas para análisis

## ⚠️ Consideraciones de Seguridad

1. **Testnet**: Por defecto usa testnet. Para producción, cambia `BYBIT_TESTNET=false`
2. **Permisos API requeridos**:
   - Read (Lectura de posiciones y balance)
   - Trade (Modificación de Stop Loss)

## 🔍 Monitoreo

Para verificar el estado del bot:

```bash
# Ver logs en tiempo real
docker-compose logs -f bot_principal

# Ver estado de los contenedores
docker-compose ps

# Reiniciar el bot
docker-compose restart bot_principal
```


## 📈 Ejemplo de Uso

### Escenario: Posición Long en BTCUSDT

1. Abres una posición LONG en BTCUSDT a $50,000
2. El bot detecta la posición y la agrega al pool de monitoreo
3. El precio sube a $50,150 (PnL: +0.30%)
4. ✅ Se activa el trailing stop, SL se establece en $50,075 (breakeven aproximado)
5. El precio sube a $50,400 (PnL: +0.80%)
6. 📈 El SL se actualiza a $50,150 (protegiendo +0.30%)
7. El precio sigue subiendo a $50,650
8. 📈 El SL se actualiza nuevamente a $50,400
9. Si el precio cae a $50,400, la posición se cierra con ganancia protegida

## 🛠️ Desarrollo

### Estructura del Código

- Arquitectura asíncrona con `asyncio`
- WebSocket en tiempo real para actualizaciones instantáneas
- Sistema de colas para comunicación entre componentes
- Manejo robusto de errores y reconexión automática

### Makefile

```bash
make build   # Construir imágenes Docker
make start   # Iniciar servicios
make stop    # Detener servicios
make run     # Ejecutar localmente sin Docker
```

