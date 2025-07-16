import os
import subprocess
from pathlib import Path

class SSLManager:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.ssl_path = self.base_path / "ssl"
        self.cert_path = self.ssl_path / "server.crt"
        self.key_path = self.ssl_path / "server.key"

    def certs_exist(self):
        return self.cert_path.exists() and self.key_path.exists()

    def find_openssl_config(self):
        """Busca el archivo de configuración de OpenSSL en ubicaciones comunes en Windows."""
        # La ubicación más común es con Git para Windows
        git_path = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git"
        if git_path.is_dir():
            config_path = git_path / "usr" / "ssl" / "openssl.cnf"
            if config_path.exists():
                print(f"✅ Encontrado openssl.cnf en: {config_path}")
                return config_path
        
        # Si no, devuelve None
        return None

    def generate_self_signed_cert(self, domain="localhost"):
        if self.certs_exist():
            print(f"✅ Los certificados SSL ya existen en {self.ssl_path}")
            return True
            
        self.ssl_path.mkdir(exist_ok=True)
        
        openssl_command = [
            "openssl", "req", "-x509", "-newkey", "rsa:2048",
            "-keyout", str(self.key_path),
            "-out", str(self.cert_path),
            "-days", "365",
            "-nodes",
            "-subj", f"/C=CO/ST=Bogota/L=Bogota/O=PyLaragon/OU=Development/CN={domain}"
        ]
        
        try:
            print("🔑 Generando clave y certificado SSL...")
            
            # --- SOLUCIÓN PARA EL ERROR DE OPENSSL ---
            # Crear un entorno para el subproceso y añadir la ruta de config si la encontramos
            env = os.environ.copy()
            config_file = self.find_openssl_config()
            if config_file:
                env["OPENSSL_CONF"] = str(config_file)
            
            # Ejecutar el comando con el entorno modificado
            result = subprocess.run(openssl_command, check=True, capture_output=True, text=True, env=env)
            
            print("✅ Certificado y clave SSL generados correctamente.")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print("❌ Error al generar el certificado SSL.")
            if isinstance(e, FileNotFoundError):
                 print("   Asegúrate de que OpenSSL esté instalado y en el PATH del sistema.")
            else:
                 print(f"   Error de OpenSSL: {e.stderr}")
            return False