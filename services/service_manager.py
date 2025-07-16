import subprocess
import os
import threading
import json
import time
from pathlib import Path
from .apache_manager import ApacheManager
from .mysql_manager import MySQLManager
from .php_manager import PHPManager
from .ssl_manager import SSLManager

class ServiceManager:
    def __init__(self, base_path=None):
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.config_path = self.base_path / "config" / "services.json"
        
        # Inicializar gestores de servicios
        self.apache_manager = ApacheManager(self.base_path)
        self.mysql_manager = MySQLManager(self.base_path)
        self.php_manager = PHPManager(self.base_path)
        self.ssl_manager = SSLManager(self.base_path)
        
        # Estado de servicios
        self.services_status = {
            'apache': False,
            'mysql': False,
            'php': False
        }
        
        # Cargar configuración
        self.load_config()
        
    def load_config(self):
        """Carga la configuración desde archivo JSON"""
        try:
            if self.config_path.exists() and self.config_path.stat().st_size > 0:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:  # Verificar que no esté vacío
                        config = json.loads(content)
                        # Aplicar configuración cargada
                        self.apache_manager.port_http = config.get('apache_http_port', 80)
                        self.apache_manager.port_https = config.get('apache_https_port', 443)
                        self.mysql_manager.port = config.get('mysql_port', 3306)
                        print("✅ Configuración cargada correctamente")
                    else:
                        print("⚠️  Archivo de configuración vacío, creando configuración por defecto")
                        self.save_config()
            else:
                print("📝 Creando archivo de configuración por defecto")
                self.save_config()
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"⚠️  Error cargando configuración: {e}")
            print("📝 Creando configuración por defecto")
            self.save_config()
        except Exception as e:
            print(f"❌ Error inesperado cargando configuración: {e}")
            self.save_config()
    
    def save_config(self):
        """Guarda la configuración actual"""
        try:
            config = {
                'apache_http_port': getattr(self.apache_manager, 'port_http', 80),
                'apache_https_port': getattr(self.apache_manager, 'port_https', 443),
                'mysql_port': getattr(self.mysql_manager, 'port', 3306),
                'php_version': getattr(self.php_manager, 'version', '8.1')
            }
            
            # Crear directorio config si no existe
            self.config_path.parent.mkdir(exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            print("✅ Configuración guardada correctamente")
            
        except Exception as e:
            print(f"❌ Error guardando configuración: {e}")
    
    def start_service(self, service_name):
        """Inicia un servicio específico"""
        try:
            if service_name == 'apache':
                self.apache_manager.start()
                self.services_status['apache'] = True
                print("✅ Apache iniciado correctamente")
                
            elif service_name == 'mysql':
                self.mysql_manager.start()
                self.services_status['mysql'] = True
                print("✅ MySQL iniciado correctamente")
                
            elif service_name == 'php':
                self.php_manager.configure()
                self.services_status['php'] = True
                print("✅ PHP configurado correctamente")
                
            else:
                raise ValueError(f"Servicio desconocido: {service_name}")
                
            return True
            
        except Exception as e:
            print(f"❌ Error iniciando {service_name}: {e}")
            return False
    
    def stop_service(self, service_name):
        """Detiene un servicio específico"""
        try:
            if service_name == 'apache':
                self.apache_manager.stop()
                self.services_status['apache'] = False
                print("🛑 Apache detenido")
                
            elif service_name == 'mysql':
                self.mysql_manager.stop()
                self.services_status['mysql'] = False
                print("🛑 MySQL detenido")
                
            elif service_name == 'php':
                # PHP no necesita ser "detenido" como tal
                self.services_status['php'] = False
                print("🛑 PHP desactivado")
                
            return True
            
        except Exception as e:
            print(f"❌ Error deteniendo {service_name}: {e}")
            return False
    
    def restart_service(self, service_name):
        """Reinicia un servicio"""
        print(f"🔄 Reiniciando {service_name}...")
        self.stop_service(service_name)
        time.sleep(2)  # Esperar un poco
        return self.start_service(service_name)
    
    def start_all_services(self):
        """Inicia todos los servicios"""
        print("🚀 Iniciando todos los servicios...")
        
        # Iniciar en orden específico
        services_order = ['mysql', 'php', 'apache']
        
        for service in services_order:
            if not self.start_service(service):
                print(f"❌ Falló al iniciar {service}, deteniendo proceso")
                return False
                
        print("✅ Todos los servicios iniciados correctamente")
        return True
    
    def stop_all_services(self):
        """Detiene todos los servicios"""
        print("🛑 Deteniendo todos los servicios...")
        
        # Detener en orden inverso
        services_order = ['apache', 'mysql', 'php']
        
        for service in services_order:
            self.stop_service(service)
            
        print("✅ Todos los servicios detenidos")
    
    def get_service_status(self, service_name):
        """Obtiene el estado de un servicio"""
        return self.services_status.get(service_name, False)
    
    def get_all_status(self):
        """Obtiene el estado de todos los servicios"""
        return self.services_status.copy()
    
    def is_port_available(self, port):
        """Verifica si un puerto está disponible"""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return True
        except OSError:
            return False
    
    def check_dependencies(self):
        """Verifica que todas las dependencias estén disponibles"""
        dependencies = {
            'apache': self.apache_manager.apache_path / "bin" / "httpd.exe",  # Windows
            'mysql': self.mysql_manager.mysql_path / "bin" / "mysqld.exe",   # Windows
            'php': self.php_manager.php_path / "php.exe"                     # Windows
        }
        
        # Si no es Windows, probar sin .exe
        if os.name != 'nt':
            dependencies = {
                'apache': self.apache_manager.apache_path / "bin" / "httpd",
                'mysql': self.mysql_manager.mysql_path / "bin" / "mysqld",
                'php': self.php_manager.php_path / "php"
            }
        
        missing = []
        for service, path in dependencies.items():
            if not path.exists():
                missing.append(service)
        
        return missing
    
    def setup_ssl(self, domain="localhost"):
        """Configura SSL para el dominio especificado"""
        try:
            self.ssl_manager.generate_self_signed_cert(domain)
            print(f"✅ Certificado SSL generado para {domain}")
            return True
        except Exception as e:
            print(f"❌ Error generando SSL: {e}")
            return False
