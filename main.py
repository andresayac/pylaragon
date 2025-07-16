#!/usr/bin/env python3
import sys
from pathlib import Path

# Agregar el directorio actual al path para importar módulos
sys.path.append(str(Path.cwd()))

from services.service_manager import ServiceManager
from gui.main_window import LaragonCloneGUI

def main():
    # Verificar que estamos en el directorio correcto
    base_path = Path.cwd()
    
    # Crear directorios necesarios
    directories = ["www", "ssl", "config", "apache", "mysql", "php-8.1"]
    for directory in directories:
        (base_path / directory).mkdir(exist_ok=True)
    
    # Crear archivo index.php por defecto
    index_php = base_path / "www" / "index.php"
    if not index_php.exists():
        with open(index_php, "w") as f:
            f.write("""<?php
echo "<h1>¡PyLaragon funcionando!</h1>";
echo "<p>PHP Version: " . phpversion() . "</p>";
echo "<p>Server: " . $_SERVER['SERVER_SOFTWARE'] . "</p>";
phpinfo();
?>""")
    
    # Inicializar el gestor de servicios
    service_manager = ServiceManager(base_path)
    
    # Verificar dependencias
    missing_deps = service_manager.check_dependencies()
    if missing_deps:
        print(f"⚠️  Dependencias faltantes: {', '.join(missing_deps)}")
        print("Por favor, instala los servicios requeridos en sus respectivos directorios")
    
    # Iniciar GUI pasando el service_manager
    print(service_manager)
    app = LaragonCloneGUI(service_manager)
    app.root.mainloop()

if __name__ == "__main__":
    main()
