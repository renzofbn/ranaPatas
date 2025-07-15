#!/usr/bin/env python3
"""
Script de monitoreo para detectar problemas de rendimiento
"""

import requests
import time
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monitor.log'),
        logging.StreamHandler()
    ]
)

def check_app_health(url):
    """
    Verificar el estado de la aplicación
    """
    try:
        start_time = time.time()
        response = requests.get(url, timeout=30)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            logging.info(f"✅ App OK - Tiempo de respuesta: {response_time:.2f}s")
            if response_time > 10:
                logging.warning(f"⚠️  Respuesta lenta: {response_time:.2f}s")
        else:
            logging.error(f"❌ Error HTTP {response.status_code}")
            
        return response.status_code, response_time
        
    except requests.exceptions.Timeout:
        logging.error("❌ Timeout - La aplicación no responde")
        return 504, 30
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Error de conexión: {e}")
        return 500, 0

def main():
    # Cambiar por tu URL de PythonAnywhere
    app_url = "https://tuusuario.pythonanywhere.com"
    
    logging.info("🚀 Iniciando monitoreo de la aplicación")
    
    consecutive_errors = 0
    
    while True:
        status_code, response_time = check_app_health(app_url)
        
        if status_code != 200:
            consecutive_errors += 1
            if consecutive_errors >= 3:
                logging.critical(f"🚨 ALERTA: {consecutive_errors} errores consecutivos")
        else:
            consecutive_errors = 0
        
        # Esperar 5 minutos antes de la siguiente verificación
        time.sleep(300)

if __name__ == "__main__":
    main()
