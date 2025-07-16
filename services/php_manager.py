class PHPManager:
    def __init__(self, base_path, version="8.1"):
        self.base_path = base_path
        self.php_path = base_path / f"php-{version}"
        self.version = version
        
    def generate_php_ini(self):
        """Genera configuración de PHP"""
        config = f"""
extension_dir = "{self.php_path}/ext"
upload_max_filesize = 64M
post_max_size = 64M
memory_limit = 256M
max_execution_time = 300

; Extensiones comunes
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
        """Configura PHP"""
        ini_content = self.generate_php_ini()
        with open(self.php_path / "php.ini", "w") as f:
            f.write(ini_content)
