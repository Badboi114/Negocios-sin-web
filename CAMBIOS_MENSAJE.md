# Cambios Realizados en el Sistema de Prospección

## Fecha: 2026-04-26

### 1. Mensaje Actualizado ✅

Se actualizó completamente la plantilla del mensaje en `config.py` con la siguiente información:

#### Nuevos Precios de Páginas Web:
- **Página Básica**: 250 Bs
- **Página Moderada**: 450 Bs  
- **Página Premium**: 650 Bs

#### Sistema Web de Gestión (Opcional):
- **Básico**: 500 Bs
- **Intermedio**: 700 Bs
- **Avanzado**: 900 Bs

#### Características Incluidas:
- Hosting GRATIS - Sin pagos mensuales
- Diseño responsivo (móvil y computadora)
- Catálogo de productos/servicios
- Botón directo a WhatsApp
- Publicación en internet

#### Ejemplos de Trabajo:
- Portafolio: https://william-lujan-portafolio.netlify.app
- Cliente: https://hat-trick-barbers-tudio.netlify.app

### 2. Promoción del Día del Padre Eliminada ✅

Se eliminó completamente la mención a la "Promoción Especial por el Mes del Padre" y el precio promocional de 200 Bs.

### 3. Envío Todo el Año ✅

**El sistema YA permite enviar mensajes todos los días del año.** No hay restricciones de fechas en el código.

### Sobre las Limitaciones de WhatsApp

Si experimentas problemas al enviar masivos, puede deberse a:

1. **Límites de WhatsApp**: WhatsApp tiene protecciones anti-spam que pueden limitar el envío masivo temporalmente.

2. **Configuración actual del sistema**:
   - Pausa entre mensajes: 45-120 segundos
   - Pausa larga cada 5 mensajes: 1 minuto
   - Máximo por sesión: 50 mensajes
   - Pausa entre sesiones: 1 hora

3. **Recomendaciones**:
   - El sistema ya tiene pausas inteligentes para evitar bloqueos
   - Si WhatsApp detecta actividad sospechosa, puede limitar temporalmente
   - Espera unas horas entre sesiones de envío masivo
   - Mantén tu cuenta de WhatsApp en buen estado (verificada, con foto de perfil, etc.)

### Cómo Usar el Sistema

```bash
# Ejecutar el sistema de prospección
python3 main.py

# O usar el script de ejecución
./ejecutar.sh
```

El sistema:
1. Busca negocios sin web en Google Maps
2. Genera mensajes personalizados con los nuevos precios
3. Envía automáticamente por WhatsApp Web
4. Guarda el historial para no contactar dos veces al mismo negocio

### Archivos Modificados

- `config.py` - Plantilla del mensaje actualizada

### Notas Importantes

- Los precios mencionados en el mensaje son flexibles según las necesidades del cliente
- El sistema web es opcional y su costo es adicional al de la página
- El hosting gratuito es un diferenciador importante en tu oferta
