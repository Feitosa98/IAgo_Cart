
import os
import sys
import shutil
import subprocess
import winshell
from win32com.client import Dispatch
import pythoncom
import tkinter as tk
from tkinter import ttk, messagebox
import threading

# Configuration
APP_NAME = "Indicador Real"
INSTALL_DIR = os.path.join(os.environ['LOCALAPPDATA'], APP_NAME)
MAIN_EXE = "Indicador Server.exe"

class MasterInstaller:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Instalador - {APP_NAME}")
        self.root.geometry("600x400")
        self.center_window()
        
        self.assets_dir = self.get_resource_path("installer_assets")
        self.dist_dir = self.get_resource_path("dist_bundle") # We will rename dist to this inside
        
        # Styles
        style = ttk.Style()
        style.configure("TLabel", font=("Arial", 11))
        style.configure("Header.TLabel", font=("Arial", 16, "bold"))

        # UI
        tk.Label(root, text=f"Instalação do {APP_NAME}", font=("Arial", 18, "bold")).pack(pady=20)
        
        self.status_label = ttk.Label(root, text="Pronto para instalar.", wraplength=500)
        self.status_label.pack(pady=10)
        
        self.progress = ttk.Progressbar(root, mode='determinate', length=400)
        self.progress.pack(pady=20)
        
        self.log_text = tk.Text(root, height=8, width=70, state='disabled')
        self.log_text.pack(pady=10)
        
        self.btn_install = ttk.Button(root, text="INICIAR INSTALAÇÃO", command=self.start_thread)
        self.btn_install.pack(pady=10)

    def center_window(self):
        self.root.update_idletasks()
        w, h = 600, 400
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f'{w}x{h}+{x}+{y}')

    def get_resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def log(self, msg):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        self.root.update()

    def start_thread(self):
        self.btn_install.config(state='disabled')
        threading.Thread(target=self.run_install, daemon=True).start()

    def run_install(self):
        try:
            pythoncom.CoInitialize() # Initialize COM for this thread
            self.log(f"Iniciando instalação em: {INSTALL_DIR}")
            self.progress['value'] = 10
            
            # 1. Create Directory
            if not os.path.exists(INSTALL_DIR):
                os.makedirs(INSTALL_DIR)
                self.log("Diretório criado.")
            
            # 2. Copy App Files (from bundled dist)
            # We assume the builder included 'dist' contents into 'dist_bundle'
            self.log("Copiando arquivos do sistema...")
            if os.path.exists(self.dist_dir):
                self.copy_tree(self.dist_dir, INSTALL_DIR)
                self.log("Arquivos do sistema copiados.")
            else:
                self.log("[ERRO] Arquivos do sistema não encontrados no pacote.")
            
            self.progress['value'] = 40
            
            # 3. Install Dependencies (Git, Tesseract)
            self.install_dependencies()
            self.progress['value'] = 70
            
            # 4. Copy Poppler
            poppler_src = os.path.join(self.assets_dir, "poppler")
            poppler_dst = os.path.join(INSTALL_DIR, "poppler")
            if os.path.exists(poppler_src):
                self.log("Instalando Poppler...")
                if os.path.exists(poppler_dst):
                    shutil.rmtree(poppler_dst)
                shutil.copytree(poppler_src, poppler_dst)
                self.log("Poppler instalado.")
            
            # 5. Create Shortcuts
            self.create_shortcuts()
            self.progress['value'] = 100
            
            self.log("Instalação Concluída!")
            messagebox.showinfo("Sucesso", "Sistema instalado com sucesso!")
            
            # Launch?
            if messagebox.askyesno("Abrir", "Deseja abrir o Assistente de Configuração agora?"):
                subprocess.Popen([os.path.join(INSTALL_DIR, "Setup Wizard.exe")])
            
            self.root.quit()
            
        except Exception as e:
            self.log(f"[ERRO CRÍTICO] {e}")
            messagebox.showerror("Erro", f"Falha na instalação: {e}")
            self.btn_install.config(state='normal')

    def copy_tree(self, src, dst):
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            if os.path.isdir(s):
                if os.path.exists(d):
                    shutil.rmtree(d)
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)

    def install_dependencies(self):
        # Look for installers in installer_assets
        # Git
        # Check if installed
        if shutil.which("git"):
            self.log("Git já instalado (Detectado no PATH). Pulando...")
        else:
            git_installer = self.find_file_by_pattern(self.assets_dir, "Git*.exe")
            if git_installer:
                self.log(f"Instalando Git ({os.path.basename(git_installer)})...")
                subprocess.run([git_installer, "/VERYSILENT", "/NORESTART"], shell=True)
                self.log("Git instalado.")
            else:
                self.log("Instalador do Git não encontrado (pular).")

        # Tesseract
        # Check if installed (PATH or Common Dirs)
        tess_in_path = shutil.which("tesseract")
        tess_common = [r"C:\Program Files\Tesseract-OCR\tesseract.exe", r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"]
        tess_found = tess_in_path
        if not tess_found:
            for p in tess_common:
                if os.path.exists(p):
                    tess_found = True
                    break
        
        if tess_found:
            self.log("Tesseract já instalado. Pulando...")
        else:
            tess_installer = self.find_file_by_pattern(self.assets_dir, "tesseract*.exe")
            if tess_installer:
                self.log(f"Instalando Tesseract ({os.path.basename(tess_installer)})...")
                subprocess.run([tess_installer, "/S"], shell=True)
                self.log("Tesseract instalado.")
            else:
                self.log("Instalador do Tesseract não encontrado (pular).")

    def find_file_by_pattern(self, directory, pattern):
        if not os.path.exists(directory): return None
        import glob
        matches = glob.glob(os.path.join(directory, pattern))
        return matches[0] if matches else None

    def create_shortcuts(self):
        self.log("Criando atalhos...")
        desktop = winshell.desktop()
        path = os.path.join(desktop, f"{APP_NAME}.lnk")
        target = os.path.join(INSTALL_DIR, MAIN_EXE)
        wDir = INSTALL_DIR
        icon = target
        
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = target
        shortcut.WorkingDirectory = wDir
        shortcut.IconLocation = icon
        shortcut.save()
        self.log("Atalho criado na Área de Trabalho.")

if __name__ == "__main__":
    if not os.path.exists("installer_assets") and not getattr(sys, 'frozen', False):
        print("Creating dummy assets folder for dev...")
        os.makedirs("installer_assets", exist_ok=True)
        
    root = tk.Tk()
    app = MasterInstaller(root)
    root.mainloop()

