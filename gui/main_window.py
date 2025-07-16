import tkinter as tk
from tkinter import ttk, messagebox, Menu
import threading

class LaragonCloneGUI:
    def __init__(self, service_manager):
        self.root = tk.Tk()
        self.root.title("PyLaragon - Entorno de Desarrollo")
        self.root.geometry("600x400")
        
        self.service_manager = service_manager
        self.service_manager.set_status_callback(self.update_service_status_from_thread)

        self.service_buttons = {}
        self.status_labels = {}
        
        self.setup_ui()
        self.update_all_statuses()

    def setup_ui(self):
        # Crear menú
        menubar = Menu(self.root)
        self.root.config(menu=menubar)

        # Menú PHP
        php_menu = Menu(menubar, tearoff=0)
        self.php_version_var = tk.StringVar(value=self.service_manager.config.get('php_version'))
        
        php_versions = self.service_manager.find_php_versions()
        if not php_versions:
             php_menu.add_command(label="No se encontraron versiones de PHP", enabled=False)
        else:
            for version in php_versions:
                php_menu.add_radiobutton(
                    label=version, 
                    variable=self.php_version_var, 
                    value=version,
                    command=self.on_php_version_change
                )
        menubar.add_cascade(label="PHP", menu=php_menu)

        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        services_frame = ttk.LabelFrame(main_frame, text="Servicios", padding="10")
        services_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # Renderizar servicios dinámicamente
        services = ['apache', 'mysql']
        for i, service_name in enumerate(services):
            ttk.Label(services_frame, text=f"{service_name.capitalize()}:").grid(row=i, column=0, sticky=tk.W)
            
            status_label = ttk.Label(services_frame, text="Detenido", foreground="red")
            status_label.grid(row=i, column=1, sticky=tk.W, padx=10)
            self.status_labels[service_name] = status_label
            
            button = ttk.Button(services_frame, text="Iniciar", 
                              command=lambda s=service_name: self.toggle_service(s))
            button.grid(row=i, column=2, padx=5)
            self.service_buttons[service_name] = button

        config_frame = ttk.LabelFrame(main_frame, text="Configuración", padding="10")
        config_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(config_frame, text="Generar Certificado SSL", 
                  command=self.setup_ssl).grid(row=0, column=0, padx=5)
        ttk.Button(config_frame, text="Gestionar Hosts Virtuales", 
                  command=self.manage_vhosts).grid(row=0, column=1, padx=5)

    def on_php_version_change(self):
        new_version = self.php_version_var.get()
        threading.Thread(target=self.service_manager.switch_php_version, args=(new_version,), daemon=True).start()

    def toggle_service(self, service_name):
        """Alterna el estado de un servicio en un hilo separado."""
        if self.service_manager.get_service_status(service_name):
            threading.Thread(target=self.service_manager.stop_service, args=(service_name,), daemon=True).start()
        else:
            threading.Thread(target=self.service_manager.start_service, args=(service_name,), daemon=True).start()

    def update_service_status(self, service_name, is_running):
        """Actualiza la GUI para un servicio específico."""
        status_label = self.status_labels[service_name]
        button = self.service_buttons[service_name]
        
        if is_running:
            status_label.config(text="Corriendo", foreground="green")
            button.config(text="Detener")
        else:
            status_label.config(text="Detenido", foreground="red")
            button.config(text="Iniciar")

    def update_all_statuses(self):
        """Actualiza el estado de todos los servicios al iniciar."""
        for service_name in self.service_buttons.keys():
            is_running = self.service_manager.get_service_status(service_name)
            self.update_service_status(service_name, is_running)

    def update_service_status_from_thread(self, service_name, is_running):
        """Método seguro para ser llamado desde otros hilos."""
        self.root.after(0, self.update_service_status, service_name, is_running)

    def setup_ssl(self):
        """Genera un certificado SSL."""
        # Esta función podría abrir una nueva ventana para pedir un dominio
        domain = "localhost" # Por ahora, lo dejamos fijo
        success = self.service_manager.ssl_manager.generate_self_signed_cert(domain)
        if success:
            messagebox.showinfo("SSL", f"Certificado SSL generado para '{domain}'.\nReinicia Apache para aplicarlo.")
        else:
            messagebox.showerror("Error SSL", "No se pudo generar el certificado SSL.")
            
    def manage_vhosts(self):
        """Abre ventana de gestión de hosts virtuales."""
        messagebox.showinfo("En desarrollo", "La gestión de Virtual Hosts aún está en desarrollo.")

    def on_closing(self):
        """Asegura que todos los servicios se detengan al cerrar."""
        if messagebox.askokcancel("Salir", "¿Quieres detener todos los servicios y salir?"):
            print("🛑 Deteniendo todos los servicios antes de salir...")
            for service_name in self.service_buttons.keys():
                self.service_manager.stop_service(service_name)
            self.root.destroy()

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()