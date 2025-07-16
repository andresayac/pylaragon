class MySQLManager:
    def __init__(self, base_path, port=3306):
        self.base_path = base_path
        self.mysql_path = base_path / "mysql"
        self.port = port
        self.process = None
        
    def generate_my_cnf(self):
        """Genera configuración de MySQL"""
        config = f"""
[mysqld]
port = {self.port}
basedir = {self.mysql_path}
datadir = {self.mysql_path}/data
socket = {self.mysql_path}/mysql.sock
bind-address = 127.0.0.1

[client]
port = {self.port}
socket = {self.mysql_path}/mysql.sock
"""
        return config
        
    def initialize_database(self):
        """Inicializa la base de datos si no existe"""
        data_dir = self.mysql_path / "data"
        if not data_dir.exists():
            cmd = [
                str(self.mysql_path / "bin/mysqld"),
                "--initialize-insecure",
                f"--basedir={self.mysql_path}",
                f"--datadir={data_dir}"
            ]
            subprocess.run(cmd)
            
    def start(self):
        """Inicia MySQL"""
        self.initialize_database()
        
        conf_content = self.generate_my_cnf()
        with open(self.mysql_path / "my.cnf", "w") as f:
            f.write(conf_content)
            
        cmd = [
            str(self.mysql_path / "bin/mysqld"),
            f"--defaults-file={self.mysql_path}/my.cnf"
        ]
        self.process = subprocess.Popen(cmd)
