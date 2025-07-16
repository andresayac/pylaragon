class ApacheManager:
    def __init__(self, base_path, port_http=80, port_https=443):
        self.base_path = base_path
        self.apache_path = base_path / "apache"
        self.port_http = port_http
        self.port_https = port_https
        self.process = None
        
    def generate_httpd_conf(self):
        """Genera configuración de Apache dinámicamente"""
        config = f"""
ServerRoot "{self.apache_path}"
Listen {self.port_http}
Listen {self.port_https} ssl

LoadModule rewrite_module modules/mod_rewrite.so
LoadModule ssl_module modules/mod_ssl.so
LoadModule php_module modules/libphp.so

DocumentRoot "{self.base_path}/www"
DirectoryIndex index.php index.html

<Directory "{self.base_path}/www">
    AllowOverride All
    Require all granted
</Directory>

# SSL Configuration
<VirtualHost *:{self.port_https}>
    SSLEngine on
    SSLCertificateFile "{self.base_path}/ssl/server.crt"
    SSLCertificateKeyFile "{self.base_path}/ssl/server.key"
</VirtualHost>
"""
        return config
        
    def start(self):
        """Inicia Apache"""
        conf_content = self.generate_httpd_conf()
        with open(self.apache_path / "conf/httpd.conf", "w") as f:
            f.write(conf_content)
            
        cmd = [str(self.apache_path / "bin/httpd"), "-D", "FOREGROUND"]
        self.process = subprocess.Popen(cmd)
        
    def stop(self):
        """Detiene Apache"""
        if self.process:
            self.process.terminate()
