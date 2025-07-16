import subprocess
import os
import threading
import json
import time
import psutil
from pathlib import Path
from .apache_manager import ApacheManager
from .mysql_manager import MySQLManager
from .php_manager import PHPManager
from .ssl_manager import SSLManager

class ServiceManager:
    def __init__(self, base_path=None):
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.bin_path = self.base_path / "bin"
        self.config_path = self.base_path / "config" / "services.json"
        
        # Estado de servicios y procesos
        self.processes = {'apache': None, 'mysql': None}
        self.service_status_callback = None

        # Cargar configuración o crear una por defecto
        self.config = self.load_config()

        # Inicializar gestores de servicios
        self.php_manager = PHPManager(self.bin_path, self.config.get('php_version', '8.1'))
        self.apache_manager = ApacheManager(self.bin_path, self.php_manager, self.config)
        self.mysql_manager = MySQLManager(self.bin_path, self.config)
        self.ssl_manager = SSLManager(self.base_path)

    def load_config(self):
        """Carga la configuración desde archivo JSON o crea una por defecto."""
        try:
            if self.config_path.exists() and self.config_path.stat().st_size > 0:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    print("✅ Configuración cargada correctamente.")
                    return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"⚠️  Error cargando configuración: {e}. Creando una por defecto.")
        
        # Configuración por defecto
        default_config = {
            'apache_http_port': 80,
            'apache_https_port': 443,
            'mysql_port': 3306,
            'php_version': self.find_php_versions()[0] if self.find_php_versions() else '8.1'
        }
        self.save_config(default_config)
        return default_config

    def save_config(self, config_data=None):
        """Guarda la configuración actual."""
        if config_data is None:
            config_data = self.config
        
        self.config_path.parent.mkdir(exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        print("✅ Configuración guardada.")

    def find_php_versions(self):
        """Encuentra las versiones de PHP disponibles en el directorio bin/php."""
        php_dir = self.bin_path / "php"
        if not php_dir.is_dir():
            return []
        return sorted([d.name for d in php_dir.iterdir() if d.is_dir()])

    def switch_php_version(self, version):
        """Cambia la versión de PHP y reinicia Apache si está activo."""
        print(f"🔄 Cambiando a PHP versión {version}...")
        self.php_manager.set_version(version)
        self.apache_manager.update_php_manager(self.php_manager)
        self.config['php_version'] = version
        self.save_config()
        
        if self.get_service_status('apache'):
            self.restart_service('apache')
        print(f"✅ Versión de PHP cambiada a {version}.")

    def _run_service(self, service_name, cmd):
        """Inicia un proceso de servicio y lo monitorea."""
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.processes[service_name] = process
            
            # Hilo para monitorear la salida del proceso
            threading.Thread(target=self._monitor_output, args=(process, service_name), daemon=True).start()
            
            # Hilo para monitorear el estado del proceso
            threading.Thread(target=self._monitor_process, args=(process, service_name), daemon=True).start()
            
            print(f"✅ {service_name.capitalize()} iniciado (PID: {process.pid}).")
            if self.service_status_callback:
                self.service_status_callback(service_name, True)
        except Exception as e:
            print(f"❌ Error al iniciar {service_name}: {e}")
            if self.service_status_callback:
                self.service_status_callback(service_name, False)

    def _monitor_output(self, process, service_name):
        """Lee la salida de un proceso para depuración."""
        if process.stdout:
            for line in iter(process.stdout.readline, ''):
                print(f"[{service_name}]: {line.strip()}")

    def _monitor_process(self, process, service_name):
        """Monitorea si el proceso sigue vivo."""
        process.wait()
        print(f"🛑 {service_name.capitalize()} se ha detenido.")
        self.processes[service_name] = None
        if self.service_status_callback:
            self.service_status_callback(service_name, False)

    def start_service(self, service_name):
        """Inicia un servicio específico."""
        if self.get_service_status(service_name):
            print(f"⚠️ {service_name.capitalize()} ya está en ejecución.")
            return

        print(f"🚀 Iniciando {service_name.capitalize()}...")
        if service_name == 'apache':
            self.apache_manager.configure()
            cmd = self.apache_manager.get_start_command()
        elif service_name == 'mysql':
            self.mysql_manager.configure()
            cmd = self.mysql_manager.get_start_command()
        else:
            raise ValueError(f"Servicio desconocido: {service_name}")
            
        threading.Thread(target=self._run_service, args=(service_name, cmd), daemon=True).start()

    def stop_service(self, service_name):
        """Detiene un servicio específico por su PID."""
        print(f"🛑 Deteniendo {service_name.capitalize()}...")
        process = self.processes.get(service_name)
        if process and process.poll() is None:
            try:
                parent = psutil.Process(process.pid)
                for child in parent.children(recursive=True):
                    child.terminate()
                parent.terminate()
                process.wait(timeout=5)
            except (psutil.NoSuchProcess, psutil.TimeoutExpired) as e:
                print(f"⚠️ No se pudo detener {service_name} de forma elegante: {e}. Forzando terminación.")
                process.kill()
            self.processes[service_name] = None
        else:
            print(f"⚠️ {service_name.capitalize()} no estaba en ejecución.")

    def restart_service(self, service_name):
        """Reinicia un servicio."""
        if self.get_service_status(service_name):
            self.stop_service(service_name)
            time.sleep(3) # Dar tiempo para que los puertos se liberen
        self.start_service(service_name)

    def get_service_status(self, service_name):
        """Verifica si el proceso del servicio está activo."""
        process = self.processes.get(service_name)
        return process and process.poll() is None
        
    def set_status_callback(self, callback):
        """Establece una función de callback para actualizar la GUI."""
        self.service_status_callback = callback