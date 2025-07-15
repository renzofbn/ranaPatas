#!/usr/bin/env python3
"""
Script de verificación rápida sin time.sleep para detectar problemas
"""

import requests
import logging
from datetime import datetime
import sys

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def quick_health_check(url):
    """
    Verificación rápida del estado de la aplicación (sin sleep)
    """
    try:
        start_time = datetime.now()
        response = requests.get(url, timeout=30)
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        
        if response.status_code == 200:
            logging.info(f"✅ App OK - Tiempo de respuesta: {response_time:.2f}s")
            if response_time > 10:
                logging.warning(f"⚠️  Respuesta lenta: {response_time:.2f}s")
                return False
        else:
            logging.error(f"❌ Error HTTP {response.status_code}")
            return False
            
        return True
        
    except requests.exceptions.Timeout:
        logging.error("❌ Timeout - La aplicación no responde en 30 segundos")
        return False
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Error de conexión: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Uso: python quick_check.py <URL_DE_TU_APP>")
        print("Ejemplo: python quick_check.py https://tuusuario.pythonanywhere.com")
        sys.exit(1)
    
    app_url = sys.argv[1]
    
    logging.info(f"🔍 Verificando estado de: {app_url}")
    
    # Realizar múltiples verificaciones rápidas
    success_count = 0
    total_checks = 3
    
    for i in range(total_checks):
        logging.info(f"Verificación {i+1}/{total_checks}")
        if quick_health_check(app_url):
            success_count += 1
    
    success_rate = (success_count / total_checks) * 100
    
    if success_rate == 100:
        logging.info(f"🎉 Todas las verificaciones exitosas ({success_rate}%)")
    elif success_rate >= 66:
        logging.warning(f"⚠️  Algunas fallas detectadas ({success_rate}% éxito)")
    else:
        logging.error(f"🚨 Múltiples fallas detectadas ({success_rate}% éxito)")
        sys.exit(1)

if __name__ == "__main__":
    main()
