import os
import subprocess
from pathlib import Path

class ApacheManager:
    def __init__(self, bin_path, php_manager, config, ssl_manager):
        self.apache_path = bin_path / "apache"
        self.php_manager = php_manager
        self.config = config
        self.ssl_manager = ssl_manager
        self.www_path = Path.cwd() / "www"

    def update_php_manager(self, php_manager):
        self.php_manager = php_manager

    def get_start_command(self):
        """Devuelve el comando para iniciar Apache en modo consola/foreground."""
        executable = "httpd.exe" if os.name == 'nt' else "httpd"
        return [str(self.apache_path / "bin" / executable), "-D", "FOREGROUND"]

    def generate_httpd_conf(self):
        php_module_path = self.php_manager.get_php_module_path()
        if not php_module_path or not php_module_path.exists():
            error_message = (
                f"❌ No se pudo encontrar el módulo de Apache para la versión de PHP '{self.php_manager.version}'.\n\n"
                f" Ruta de búsqueda: {self.php_manager.php_path}\n\n"
                " 👉 **Solución:** Asegúrate de que el archivo correcto exista en ese directorio:\n"
                "    - En Windows: Busca un archivo como 'php8apache2_4.dll'.\n"
                "    - En Linux/macOS: Busca un archivo como 'libphp.so'.\n"
            )
            raise FileNotFoundError(error_message)

        server_root = self.apache_path.as_posix()
        document_root = self.www_path.as_posix()

        # --- MÓDULO FINAL AÑADIDO ---
        config = f"""
ServerRoot "{server_root}"
Listen {self.config['apache_http_port']}

# Cargar módulos esenciales para el funcionamiento básico
LoadModule mime_module modules/mod_mime.so
LoadModule dir_module modules/mod_dir.so
LoadModule authz_core_module modules/mod_authz_core.so
LoadModule rewrite_module modules/mod_rewrite.so

# Configuración PHP
LoadModule php_module "{php_module_path.as_posix()}"
<IfModule php_module>
    PHPINIDir "{self.php_manager.php_path.as_posix()}"
    AddHandler application/x-httpd-php .php
    AddType application/x-httpd-php .php .html
</IfModule>

# Configuración del servidor
DocumentRoot "{document_root}"
<Directory "{document_root}">
    Options Indexes FollowSymLinks
    AllowOverride All
    Require all granted
</Directory>

DirectoryIndex index.php index.html
"""
        if self.ssl_manager.certs_exist():
            ssl_cert = self.ssl_manager.cert_path.as_posix()
            ssl_key = self.ssl_manager.key_path.as_posix()
            config += f"""

# Configuración SSL
Listen {self.config['apache_https_port']}
LoadModule ssl_module modules/mod_ssl.so

<IfModule ssl_module>
    SSLEngine on
    SSLCertificateFile "{ssl_cert}"
    SSLCertificateKeyFile "{ssl_key}"
</IfModule>
"""
        return config

    def configure(self):
        conf_content = self.generate_httpd_conf()
        conf_path = self.apache_path / "conf" / "httpd.conf"
        conf_path.parent.mkdir(exist_ok=True)
        with open(conf_path, "w", encoding='utf-8') as f:
            f.write(conf_content)
        print("✅ Configuración de Apache actualizada correctamente.")