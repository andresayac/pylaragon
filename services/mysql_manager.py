import os
import subprocess
from pathlib import Path

class MySQLManager:
    def __init__(self, bin_path, config):
        self.mysql_path = bin_path / "mysql"
        self.config = config

    def get_start_command(self):
        executable = "mysqld"
        if os.name == 'nt':
            executable += ".exe"

        # Inicializa la base de datos si es necesario
        self.initialize_database()

        return [
            str(self.mysql_path / "bin" / executable),
            f"--defaults-file={self.mysql_path / 'my.ini'}"
        ]

    def generate_my_ini(self):
        """Genera el archivo de configuración de MySQL."""
        # Rutas compatibles con la configuración de MySQL
        basedir = self.mysql_path.as_posix()
        datadir = (self.mysql_path / "data").as_posix()
        
        config = f"""
[mysqld]
port = {self.config['mysql_port']}
basedir = "{basedir}"
datadir = "{datadir}"
"""
        return config

    def initialize_database(self):
        """Inicializa el directorio de datos de MySQL si no existe."""
        data_dir = self.mysql_path / "data"
        if not data_dir.exists():
            print("🚀 Inicializando la base de datos de MySQL por primera vez...")
            executable = "mysqld"
            if os.name == 'nt':
                executable += ".exe"
            
            cmd = [
                str(self.mysql_path / "bin" / executable),
                "--initialize-insecure",
                f"--basedir={self.mysql_path.as_posix()}",
                f"--datadir={data_dir.as_posix()}"
            ]
            try:
                subprocess.run(cmd, check=True, capture_output=True, text=True)
                print("✅ Base de datos inicializada correctamente.")
            except subprocess.CalledProcessError as e:
                print(f"❌ Error al inicializar la base de datos:\n{e.stderr}")
                raise

    def configure(self):
        """Escribe el archivo de configuración de MySQL."""
        ini_content = self.generate_my_ini()
        ini_path = self.mysql_path / "my.ini"
        with open(ini_path, "w", encoding='utf-8') as f:
            f.write(ini_content)