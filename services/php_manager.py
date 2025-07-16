import os
from pathlib import Path

class PHPManager:
    def __init__(self, bin_path, version):
        self.bin_path = bin_path
        self.set_version(version)

    def set_version(self, version):
        """Establece la versión de PHP a utilizar."""
        self.version = version
        self.php_path = self.bin_path / "php" / self.version

    def get_php_module_path(self):
        """
        Obtiene la ruta al módulo de PHP para Apache, buscando el archivo correcto
        según el sistema operativo.
        """
        if not self.php_path.is_dir():
            return None

        # --- LÓGICA CORREGIDA ---
        # En Windows, buscar el archivo .dll (ej. php8apache2_4.dll)
        if os.name == 'nt':
            # Busca de forma flexible cualquier dll que contenga "apache"
            for file in self.php_path.glob("php*apache*.dll"):
                print(f"✅ Módulo de Apache encontrado en Windows: {file}")
                return file  # Devuelve la primera coincidencia
        
        # En Linux/macOS, buscar el archivo .so
        else:
            for file in self.php_path.glob("libphp*.so"):
                print(f"✅ Módulo de Apache encontrado en Linux/macOS: {file}")
                return file

        # Si no se encuentra nada
        print(f"⚠️ ¡Atención! No se encontró un módulo de Apache compatible en: {self.php_path}")
        return None

    def generate_php_ini(self):
        """Genera la configuración de PHP."""
        ext_dir = (self.php_path / "ext").as_posix()
        config = f"""
extension_dir = "{ext_dir}"
upload_max_filesize = 128M
post_max_size = 128M
memory_limit = 256M
max_execution_time = 300

; Habilita las extensiones que necesites (asegúrate de que los archivos .dll o .so existan)
extension=mysqli
extension=pdo_mysql
extension=openssl
extension=curl
extension=gd
extension=mbstring
extension=xml
"""
        return config

    def configure(self):
        """Escribe el archivo php.ini si no existe."""
        ini_path = self.php_path / "php.ini"
        if not ini_path.exists():
            print(f"🔧 Generando archivo de configuración php.ini para la versión {self.version}...")
            ini_content = self.generate_php_ini()
            ini_path.parent.mkdir(parents=True, exist_ok=True)
            with open(ini_path, "w", encoding='utf-8') as f:
                f.write(ini_content)