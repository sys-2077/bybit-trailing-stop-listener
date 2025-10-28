# 🚀 Guía Rápida - Bybit Trailing Stop Bot

## Configuración en 5 Minutos

### Paso 1: Obtener API Keys de Bybit

1. Ve a [Bybit Testnet](https://testnet.bybit.com) o [Bybit](https://www.bybit.com)
2. Inicia sesión y ve a **API Management**
3. Crea una nueva API Key con permisos:
   - ✅ **Read-Write** (para modificar Stop Loss)
   - ✅ **Contract** (para trading de futuros)
4. Guarda tu API Key y Secret en un lugar seguro

### Paso 2: Configurar el Bot

Crea un archivo `.env.dev` en la raíz del proyecto:

```bash
# Credenciales de Bybit
BYBIT_API_KEY=tu_api_key_aqui
BYBIT_API_SECRET=tu_api_secret_aqui
BYBIT_TESTNET=true

# Configuración del Trailing Stop
TRAILING_ACTIVATION_PERCENT=0.30
TRAILING_INCREMENT_PERCENT=0.50
```

### Paso 3: Verificar Configuración

Ejecuta el script de verificación:

```bash
python test_config.py
```

Si todo está correcto, verás un ✅ en todas las verificaciones.

### Paso 4: Iniciar el Bot

#### Opción A: Con Docker (Recomendado)

```bash
# Construir la imagen
docker-compose build

# Iniciar el bot
docker-compose up -d

# Ver logs en tiempo real
docker-compose logs -f bot_principal
```

#### Opción B: Sin Docker

```bash
# Instalar dependencias
pip install -r requirements.bot_principal.txt

# Ejecutar el bot
python app/main.py
```

### Paso 5: Verificar que Funciona

En los logs deberías ver:

```
✅ WebSocket Unified V5 (Private) conectado exitosamente
✅ Suscrito a canales: position, wallet
✅ Cargando posiciones abiertas iniciales...
✅ StrategyManager iniciado - Activación: 0.3%, Incremento: 0.5%
```

## 📊 Cómo Funciona

### Ejemplo Práctico

Imagina que abres una posición LONG en BTCUSDT:

1. **Entrada**: Compras BTCUSDT a $50,000
   - El bot detecta la posición
   - La agrega al **Pool de Monitoreo**
   - Log: `✓ BTCUSDT agregado al pool de monitoreo`

2. **El precio sube**: BTCUSDT ahora está en $50,150
   - PnL: +0.30%
   - Alcanza el umbral de activación
   - Log: `🎯 BTCUSDT alcanzó umbral de activación (0.30%)`

3. **Trailing Stop Activado**: 
   - El bot mueve BTCUSDT al **Pool de Trailing Activo**
   - Establece un Stop Loss inicial en $50,075
   - Log: `🔒 Trailing Stop ACTIVADO para BTCUSDT - SL inicial: 50075.0`

4. **El precio sigue subiendo**: BTCUSDT llega a $50,400
   - PnL ahora: +0.80%
   - El precio se movió +0.50% desde la última actualización
   - El bot actualiza el SL a $50,150
   - Log: `📈 Actualizando trailing stop para BTCUSDT: 50075.0 → 50150.0`

5. **Protección de Ganancias**:
   - Si el precio cae a $50,150, la posición se cierra
   - Ganancia protegida: +$150 por BTC
   - Log: `❌ BTCUSDT cerrado y removido del pool de trailing activo`

## ⚙️ Configuración Personalizada

### Ajustar el Umbral de Activación

Si quieres que el trailing se active más rápido o más lento:

```bash
# Activación más agresiva (0.15%)
TRAILING_ACTIVATION_PERCENT=0.15

# Activación más conservadora (0.50%)
TRAILING_ACTIVATION_PERCENT=0.50
```

### Ajustar el Incremento del Trailing

Si quieres trailing stops más cerrados o más sueltos:

```bash
# Trailing más cerrado (protege más, pero puede salirse antes)
TRAILING_INCREMENT_PERCENT=0.25

# Trailing más suelto (deja correr más, pero protege menos)
TRAILING_INCREMENT_PERCENT=1.00
```

## 🎯 Estrategias Recomendadas

### Scalping (Operaciones Rápidas)
```bash
TRAILING_ACTIVATION_PERCENT=0.15
TRAILING_INCREMENT_PERCENT=0.25
```
- Se activa rápido
- Protege ganancias pequeñas
- Ideal para volatilidad alta

### Swing Trading (Operaciones Medias)
```bash
TRAILING_ACTIVATION_PERCENT=0.30
TRAILING_INCREMENT_PERCENT=0.50
```
- Balance entre protección y espacio
- Configuración por defecto
- Ideal para la mayoría de casos

### Position Trading (Operaciones Largas)
```bash
TRAILING_ACTIVATION_PERCENT=1.00
TRAILING_INCREMENT_PERCENT=1.50
```
- Deja correr las ganancias
- Trailing más suelto
- Ideal para tendencias fuertes

## 🔍 Monitoreo

### Ver Logs en Tiempo Real

```bash
# Con Docker
docker-compose logs -f bot_principal

# Sin Docker
# Los logs aparecen en la consola donde ejecutaste python app/main.py
```

### Logs Importantes a Observar

- `✓` Posición agregada al monitoreo
- `🎯` Umbral alcanzado, activando trailing
- `🔒` Trailing stop activado
- `📈` Stop Loss actualizado
- `❌` Posición cerrada

### Verificar Estado

```bash
# Estado de contenedores
docker-compose ps

# Reiniciar el bot
docker-compose restart bot_principal

# Detener el bot
docker-compose down
```

## ⚠️ Importante

### Testnet vs Producción

Por defecto, el bot usa **testnet**. Para usar en producción:

1. Cambia en `.env.dev`:
   ```bash
   BYBIT_TESTNET=false
   ```

2. Usa API Keys de la cuenta real (no testnet)

3. **⚠️ ADVERTENCIA**: Prueba todo en testnet antes de usar dinero real

### Permisos de API

Asegúrate de que tu API Key tenga:
- ✅ Permisos de lectura (Read)
- ✅ Permisos de trading (Trade)
- ❌ NO necesita permisos de retiro (Withdraw)

### Seguridad

- 🔐 Nunca compartas tus API Keys
- 🔐 Usa IP whitelist en Bybit si es posible
- 🔐 Mantén tu `.env.dev` privado (está en .gitignore)

## 🆘 Solución de Problemas

### El bot no inicia

```bash
# Verificar configuración
python test_config.py

# Ver logs de error
docker-compose logs bot_principal
```

### El trailing stop no se activa

1. Verifica que tienes posiciones abiertas con ganancia
2. Revisa que `TRAILING_ACTIVATION_PERCENT` no sea muy alto
3. Observa los logs para ver el PnL actual

### El WebSocket se desconecta

- Es normal que se reconecte automáticamente
- Si persiste, revisa tus API Keys
- Verifica la conexión a internet

## 📚 Recursos Adicionales

- [README.md](README.md) - Documentación completa
- [CHANGELOG.md](CHANGELOG.md) - Historial de cambios
- [Documentación de Bybit API](https://bybit-exchange.github.io/docs/)

## 💡 Tips Finales

1. **Empieza con testnet** - Familiarízate con el bot sin riesgo
2. **Observa los logs** - Aprende cómo reacciona el bot
3. **Ajusta los parámetros** - Cada estrategia es diferente
4. **Monitorea regularmente** - Aunque el bot es automático, supervísalo
5. **Ten un plan B** - Siempre ten acceso manual a tus posiciones

---

¿Listo para empezar? 🚀

```bash
docker-compose up -d && docker-compose logs -f bot_principal
```

