# Optimizaciones para PythonAnywhere

## 1. En tu dashboard de PythonAnywhere:

### Configuración de la aplicación web:
- Ve a "Web" en tu dashboard
- En "Code", asegúrate de que el "Source code" apunte a tu directorio
- En "WSGI configuration file", usa el archivo wsgi.py que creamos

### Configuraciones recomendadas:
- Worker processes: Usa el máximo permitido por tu plan
- Timeout: Configúralo a 300 segundos (5 minutos)

## 2. Variables de entorno en PythonAnywhere:

Crea un archivo .env en tu directorio con:
```
FLASK_ENV=production
MYSQL_HOST=tu_host_mysql
MYSQL_USER=tu_usuario
MYSQL_PASSWORD=tu_contraseña
MYSQL_DB=tu_base_datos
MYSQL_PORT=3306
SECRET_KEY=tu_clave_secreta_muy_larga_y_compleja
```

## 3. Optimización de consultas:

- Revisa las consultas más lentas en tus routes
- Agrega índices a las columnas más consultadas
- Usa LIMIT en consultas que puedan devolver muchos resultados

## 4. Configuración de MySQL:

Si tienes acceso, optimiza estas configuraciones:
```sql
SET GLOBAL max_connections = 200;
SET GLOBAL connect_timeout = 10;
SET GLOBAL wait_timeout = 600;
SET GLOBAL interactive_timeout = 600;
```

## 5. Monitoreo:

- Revisa los logs en "Files" > "error.log"
- Usa el monitor.py para verificar el estado de tu app
- Configura alertas para errores 504

## 6. Buenas prácticas:

- Restart tu aplicación cada 24 horas (cron job)
- Mantén las dependencias actualizadas
- Usa cache para consultas repetitivas
- Implementa paginación en listados largos

## 7. Si el problema persiste:

- Contacta al soporte de PythonAnywhere
- Considera upgrader tu plan para más recursos
- Revisa si hay picos de tráfico coincidentes con los errores
