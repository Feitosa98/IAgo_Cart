import tkinter as tk
from tkinter import messagebox
import threading
import sys
import os
import socket
import webbrowser
import time

# Ensure we can find the app module
sys.path.append(os.getcwd())

# Import the Flask app
from imoveis_web import app

def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

class ServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Indicador Real - Servidor")
        self.root.geometry("400x250")
        self.root.configure(bg="#f0f0f0")
        
        # Center window
        self.center_window()

        # Icon (try to load if exists)
        try:
             # If bundled, icon might be in _internal or similar. 
             # For now simple.
             pass
        except:
            pass

        # Title Label
        tk.Label(root, text="Sistema Indicador Real", font=("Helvetica", 16, "bold"), bg="#f0f0f0", fg="#333").pack(pady=20)

        # Status Label
        self.status_var = tk.StringVar()
        self.status_var.set("Iniciando servidor...")
        self.lbl_status = tk.Label(root, textvariable=self.status_var, font=("Helvetica", 10), bg="#f0f0f0", fg="blue")
        self.lbl_status.pack(pady=10)

        # URL Label
        self.url_var = tk.StringVar()
        self.lbl_url = tk.Entry(root, textvariable=self.url_var, font=("Consolas", 12), justify="center", width=30, state="readonly")
        self.lbl_url.pack(pady=5)

        # Buttons
        btn_frame = tk.Frame(root, bg="#f0f0f0")
        btn_frame.pack(pady=20)

        tk.Button(btn_frame, text="Abrir no Navegador", command=self.open_browser, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), padx=10, pady=5).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Parar e Sair", command=self.stop_server, bg="#f44336", fg="white", font=("Arial", 10, "bold"), padx=10, pady=5).pack(side=tk.LEFT, padx=10)

        # Server Thread
        self.server_thread = threading.Thread(target=self.run_server, daemon=True)
        self.server_thread.start()
        
        # Check loop
        self.root.after(1000, self.check_status)

    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry('{}x{}+{}+{}'.format(width, height, x, y))

    def run_server(self):
        try:
            # Run Flask
            # Note: app.run is blocking, so this thread stays here.
            app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
        except Exception as e:
            self.status_var.set(f"Erro: {e}")

    def check_status(self):
        # Determine IP
        ip = get_ip()
        url = f"http://{ip}:5000"
        self.url_var.set(url)
        self.status_var.set("Servidor Rodando Online")
        self.lbl_status.config(fg="green")

    def open_browser(self):
        webbrowser.open(self.url_var.get())

    def stop_server(self):
        # Flask with werkzeug server is hard to stop cleanly without signals.
        # Since we are an EXE, we can just kill the process.
        self.root.destroy()
        sys.exit(0)

if __name__ == "__main__":
    root = tk.Tk()
    app_gui = ServerGUI(root)
    root.mainloop()
