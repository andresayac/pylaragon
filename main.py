import os
from pathlib import Path
from services.service_manager import ServiceManager
from gui.main_window import LaragonCloneGUI

def create_default_files():
    """Crea los directorios y archivos por defecto si no existen."""
    www_path = Path("www")
    www_path.mkdir(exist_ok=True)
    
    index_file = www_path / "index.php"
    if not index_file.exists():
        index_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Welcome to PyLaragon</title>
    <style>
        body { font-family: sans-serif; background-color: #f4f4f9; color: #333; text-align: center; margin-top: 50px; }
        h1 { color: #4CAF50; }
        div { background: white; padding: 20px; border-radius: 8px; display: inline-block; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    </style>
</head>
<body>
    <div>
        <h1>Welcome to PyLaragon!</h1>
        <p>Your PHP environment is working.</p>
        <?php phpinfo(); ?>
    </div>
</body>
</html>
"""
        with open(index_file, "w", encoding='utf-8') as f:
            f.write(index_content)

def main():
    """Punto de entrada principal de la aplicación."""
    create_default_files()
    
    service_manager = ServiceManager()
    
    # Iniciar la GUI
    gui = LaragonCloneGUI(service_manager)
    gui.run()


if __name__ == "__main__":
    main()