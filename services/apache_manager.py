import os
import subprocess
from pathlib import Path

class ApacheManager:
    def __init__(self, bin_path, php_manager, config):
        self.apache_path = bin_path / "apache"
        self.php_manager = php_manager
        self.config = config
        self.www_path = Path.cwd() / "www"
        self.ssl_path = Path.cwd() / "ssl"

    def update_php_manager(self, php_manager):
        self.php_manager = php_manager

    def get_start_command(self):
        """Devuelve el comando para iniciar Apache según el SO."""
        executable = "httpd.exe" if os.name == 'nt' else "httpd"
        return [str(self.apache_path / "bin" / executable), "-D", "FOREGROUND"]

    def generate_httpd_conf(self):
        """Genera la configuración de Apache dinámicamente."""
        php_module_path = self.php_manager.get_php_module_path()
        
        # --- LÓGICA DE ERROR MEJORADA ---
        if not php_module_path or not php_module_path.exists():
            self.php_manager.configure()  # Intenta crear php.ini para ayudar a depurar
            error_message = (
                f"❌ No se pudo encontrar el módulo de Apache para la versión de PHP '{self.php_manager.version}'.\n\n"
                f" Ruta de búsqueda: {self.php_manager.php_path}\n\n"
                " 👉 **Solución:** Asegúrate de que el archivo correcto exista en ese directorio:\n"
                "    - En Windows: Busca un archivo como 'php8apache2_4.dll'.\n"
                "    - En Linux/macOS: Busca un archivo como 'libphp.so'.\n"
            )
            raise FileNotFoundError(error_message)

        # Usar barras diagonales normales ('/') es compatible con Apache en todos los SO
        server_root = self.apache_path.as_posix()
        document_root = self.www_path.as_posix()
        ssl_cert = (self.ssl_path / "server.crt").as_posix()
        ssl_key = (self.ssl_path / "server.key").as_posix()

        # Cargar el módulo de PHP con su nombre lógico 'php_module' y la ruta al archivo
        config = f"""
ServerRoot "{server_root}"
Listen {self.config['apache_http_port']}

# Configuración PHP
LoadModule php_module "{php_module_path.as_posix()}"
PHPINIDir "{self.php_manager.php_path.as_posix()}"
AddHandler application/x-httpd-php .php
AddType application/x-httpd-php .php .html

# Configuración del servidor
DocumentRoot "{document_root}"
<Directory "{document_root}">
    Options Indexes FollowSymLinks
    AllowOverride All
    Require all granted
</Directory>

DirectoryIndex index.php index.html

# Configuración SSL (Opcional, se puede mejorar después)
<IfModule ssl_module>
    Listen {self.config['apache_https_port']}
    SSLEngine on
    SSLCertificateFile "{ssl_cert}"
    SSLCertificateKeyFile "{ssl_key}"
</IfModule>
"""
        return config

    def configure(self):
        """Escribe el archivo de configuración de Apache."""
        conf_content = self.generate_httpd_conf()
        conf_path = self.apache_path / "conf" / "httpd.conf"
        conf_path.parent.mkdir(exist_ok=True)
        with open(conf_path, "w", encoding='utf-8') as f:
            f.write(conf_content)
        print("✅ Configuración de Apache actualizada correctamente.")