
import os
import sys
import shutil
import zipfile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.filedialog import askdirectory, askopenfilename
import subprocess

class SetupWizard:
    def __init__(self, root):
        self.root = root
        self.root.title("Instalação - Indicador Real")
        self.root.geometry("500x450")
        self.root.configure(bg="#f0f0f0")
        
        # Center
        self.center_window()
        
        # Style
        style = ttk.Style()
        style.configure("TLabel", background="#f0f0f0", font=("Arial", 10))
        style.configure("TButton", font=("Arial", 10))
        
        # Title
        tk.Label(root, text="Configuração Inicial", font=("Arial", 16, "bold"), bg="#f0f0f0").pack(pady=20)
        
        # Main Frame
        main_frame = tk.Frame(root, bg="#f0f0f0", padx=20)
        main_frame.pack(fill="both", expand=True)
        
        # Generic Input helper
        def create_entry(label_text, default_val):
            frame = tk.Frame(main_frame, bg="#f0f0f0")
            frame.pack(fill="x", pady=5)
            tk.Label(frame, text=label_text, bg="#f0f0f0", width=15, anchor="w").pack(side="left")
            entry = ttk.Entry(frame)
            if default_val:
                entry.insert(0, default_val)
            entry.pack(side="right", fill="x", expand=True)
            return entry

        # Load Defaults
        current_name = os.getenv("CARTORIO_NAME", "Cartório de Notas")
        current_cns = os.getenv("CNS_CODIGO", "")

        self.entry_name = create_entry("Nome do Cartório:", current_name)
        self.entry_cns = create_entry("Código CNS:", current_cns)
        
        # Database Section
        db_frame = tk.LabelFrame(main_frame, text="Banco de Dados Inteligente (IAGO)", bg="#f0f0f0", font=("Arial", 10, "bold"))
        db_frame.pack(fill="x", pady=10)
        
        self.use_cloud_var = tk.BooleanVar(value=True) # Default True
        ttk.Checkbutton(db_frame, text="Usar Nuvem ONR (Recomendado)", variable=self.use_cloud_var).pack(anchor="w", padx=5, pady=5)

        # OCR Dependencies Section
        ocr_frame = tk.LabelFrame(main_frame, text="Dependências de Leitura (OCR)", bg="#f0f0f0", font=("Arial", 10, "bold"))
        ocr_frame.pack(fill="x", pady=10)

        # Tesseract
        t_frame = tk.Frame(ocr_frame, bg="#f0f0f0")
        t_frame.pack(fill="x", pady=2)
        tk.Label(t_frame, text="Tesseract (exe):", width=15, anchor="w", bg="#f0f0f0").pack(side="left")
        self.tesseract_path_var = tk.StringVar(value=os.getenv("TESSERACT_CMD", r"C:\Program Files\Tesseract-OCR\tesseract.exe"))
        ttk.Entry(t_frame, textvariable=self.tesseract_path_var).pack(side="left", fill="x", expand=True)
        ttk.Button(t_frame, text="...", width=3, command=self.browse_tesseract).pack(side="right")

        # Poppler
        p_frame = tk.Frame(ocr_frame, bg="#f0f0f0")
        p_frame.pack(fill="x", pady=2)
        tk.Label(p_frame, text="Poppler (bin):", width=15, anchor="w", bg="#f0f0f0").pack(side="left")
        self.poppler_path_var = tk.StringVar(value=os.getenv("POPPLER_PATH", r"C:\Program Files\Poppler\Library\bin"))
        ttk.Entry(p_frame, textvariable=self.poppler_path_var).pack(side="left", fill="x", expand=True)
        ttk.Button(p_frame, text="...", width=3, command=self.browse_poppler).pack(side="right")
        
        # Backup Section
        tk.Label(main_frame, text="Restaurar Backup (Opcional)", font=("Arial", 10, "bold"), bg="#f0f0f0").pack(pady=(10, 5), anchor="w")
        
        self.backup_path_var = tk.StringVar()
        backup_frame = tk.Frame(main_frame, bg="#f0f0f0")
        backup_frame.pack(fill="x")
        
        ttk.Entry(backup_frame, textvariable=self.backup_path_var, state="readonly").pack(side="left", fill="x", expand=True)
        ttk.Button(backup_frame, text="Selecionar Arquivo", command=self.browse_backup).pack(side="right", padx=(5, 0))
        
        # Buttons
        btn_frame = tk.Frame(root, bg="#f0f0f0")
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="Salvar e Instalar", command=self.save_and_install).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="Cancelar", command=root.destroy).pack(side="left", padx=10)

    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry('{}x{}+{}+{}'.format(width, height, x, y))

    def browse_tesseract(self):
        f = askopenfilename(filetypes=[("Executables", "*.exe"), ("All", "*.*")])
        if f: self.tesseract_path_var.set(f)

    def browse_poppler(self):
        d = askdirectory()
        if d: self.poppler_path_var.set(d)

    def browse_backup(self):
        file_path = filedialog.askopenfilename(
            title="Selecione o Backup",
            filetypes=[("Backup Files", "*.db *.zip *.sql"), ("All Files", "*.*")]
        )
        if file_path:
            self.backup_path_var.set(file_path)

    def save_and_install(self):
        name = self.entry_name.get().strip()
        cns = self.entry_cns.get().strip()
        backup_path = self.backup_path_var.get()
        use_cloud = self.use_cloud_var.get()
        
        tesseract_cmd = self.tesseract_path_var.get().strip()
        poppler_path = self.poppler_path_var.get().strip()
        
        if not name or not cns:
            messagebox.showerror("Erro", "Nome e CNS são obrigatórios!")
            return
            
        # 1. Restore Backup if selected
        if backup_path:
            try:
                base = self.get_base_path()
                target_db = os.path.join(base, "imoveis.db")
                
                if backup_path.endswith('.db'):
                    shutil.copy(backup_path, target_db)
                elif backup_path.endswith('.zip'):
                    with zipfile.ZipFile(backup_path, 'r') as zip_ref:
                        db_files = [f for f in zip_ref.namelist() if f.endswith('.db')]
                        if db_files:
                            source = zip_ref.open(db_files[0])
                            with open(target_db, "wb") as target:
                                shutil.copyfileobj(source, target)
                        else:
                            messagebox.showwarning("Aviso", "Nenhum arquivo .db encontrado no ZIP. Backup ignorado.")
                else:
                    # just copy
                     shutil.copy(backup_path, target_db)
                     
            except Exception as e:
                messagebox.showerror("Erro no Backup", f"Falha ao restaurar: {e}")
                return

        # 2. Save Config
        config = {
            "CARTORIO_NAME": name,
            "CNS_CODIGO": cns,
            "IAGO_DB_TYPE": "postgres" if use_cloud else "sqlite",
            "TESSERACT_CMD": tesseract_cmd,
            "POPPLER_PATH": poppler_path
        }
        
        if use_cloud:
            # Preset for Project ONR
            config["IAGO_DB_URL"] = "postgresql://postgres:Manacapuru@indicador-onr-db.cr6ek2eqs8ci.sa-east-1.rds.amazonaws.com:5432"
        
        self.save_env_file(config)
        self.save_env_file(config)
        
        messagebox.showinfo("Sucesso", "Instalação concluída com sucesso!")
        self.root.destroy()

    def get_base_path(self):
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        return os.getcwd()

    def save_env_file(self, config):
        base = self.get_base_path()
        env_path = os.path.join(base, ".env")
        existing_lines = []
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                existing_lines = f.readlines()
                
        def key_exists(key, lines):
            for i, line in enumerate(lines):
                if line.strip().startswith(f"{key}="):
                    return i
            return -1
            
        for key, value in config.items():
            idx = key_exists(key, existing_lines)
            new_line = f"{key}={value}\n"
            if idx >= 0:
                existing_lines[idx] = new_line
            else:
                if existing_lines and not existing_lines[-1].endswith("\n"):
                    existing_lines.append("\n")
                existing_lines.append(new_line)
        
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(existing_lines)

if __name__ == "__main__":
    root = tk.Tk()
    app = SetupWizard(root)
    root.mainloop()
