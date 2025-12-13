import json
import threading
import queue
import os
import sqlite3
import sys
import subprocess
from datetime import datetime
from pathlib import Path

import pytesseract
from PIL import Image
import pandas as pd

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ------------------------------
# CONFIGURAÇÕES
# ------------------------------

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
CNS_CODIGO = "004879"   # ← CNS informado

DB_DEFAULT = "imoveis.db"

# ------------------------------
# TABELAS DE CÓDIGO ONR
# ------------------------------

REGISTRO_TIPO_OPCOES = {
    1: "Matrícula",
    2: "Matrícula Mãe",
    4: "Transcrição",
}

LOCALIZACAO_OPCOES = {
    0: "URBANO",
    1: "RURAL",
}

TIPO_IMOVEL_OPCOES = {
    1: "Casa",
    2: "Apartamento",
    3: "Loja",
    4: "Sala/Conjunto",
    5: "Terreno/Fração",
    6: "Galpão",
    7: "Prédio comercial",
    8: "Prédio residencial",
    9: "Fazenda/Sítio/Chácara",
    10: "Vaga",
    11: "Depósito",
    12: "Públicos",
    13: "Outros",
}

UF_OPCOES = {
    11:"RO",12:"AC",13:"AM",14:"RR",15:"PA",16:"AP",17:"TO",
    21:"MA",22:"PI",23:"CE",24:"RN",25:"PB",26:"PE",27:"AL",28:"SE",29:"BA",
    31:"MG",32:"ES",33:"RJ",35:"SP",
    41:"PR",42:"SC",43:"RS",
    50:"MS",51:"MT",52:"GO",53:"DF"
}

# mapa SIGLA -> código UF
UF_SIGLA_TO_COD = {sigla: cod for cod, sigla in UF_OPCOES.items()}

TIPO_LOGRADOURO_OPCOES = {
    1:"Acampamento",2:"Acesso",3:"Açude",4:"Adro",
    10:"Alameda",21:"Artéria",22:"Assentamento",25:"Autódromo",
    26:"Avenida",28:"Bairro",35:"Balneário",42:"Beco",
    59:"Caminho",61:"Canal",71:"Chácara",81:"Condomínio",
    82:"Conjunto",97:"Edifício",117:"Estrada",
    146:"Jardim",153:"Largo",162:"Loteamento",
    191:"Parque",215:"Praça",223:"Quadra",
    247:"Rodovia",250:"Rua",260:"Servidão",
    262:"Setor",273:"Travessa",276:"Trecho",
    297:"Viela",298:"Vila"
}

# ------------------------------
# HELPERS
# ------------------------------

def make_combo_values(options_dict: dict) -> list[str]:
    return [f"{k} - {v}" for k, v in sorted(options_dict.items())]

def combo_to_codigo(combo_value: str | None) -> int | None:
    if not combo_value:
        return None
    codigo = combo_value.split(" - ", 1)[0]
    try:
        return int(codigo)
    except:
        return None

def codigo_to_combo(codigo: int | None, mapping: dict) -> str:
    if codigo is None:
        return ""
    nome = mapping.get(codigo)
    if nome:
        return f"{codigo} - {nome}"
    return str(codigo)

# ------------------------------
# ARQUIVOS / SISTEMA
# ------------------------------

def abrir_arquivo_no_sistema(file_path: str):
    try:
        file_path = os.path.normpath(file_path)
        if not os.path.exists(file_path):
            messagebox.showerror("Erro", f"Arquivo não encontrado:\n{file_path}")
            return

        if os.name == "nt":
            os.startfile(file_path)
        elif sys.platform == "darwin":
            subprocess.call(["open", file_path])
        else:
            subprocess.call(["xdg-open", file_path])
    except Exception as e:
        messagebox.showerror("Erro ao abrir arquivo", str(e))

# ------------------------------
# BANCO
# ------------------------------

def init_db(db_path=DB_DEFAULT):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS imoveis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_registro TEXT,
        varios_enderecos TEXT,
        registro_tipo INTEGER,
        tipo_de_imovel INTEGER,
        localizacao INTEGER,
        tipo_logradouro INTEGER,
        nome_logradouro TEXT,
        numero_logradouro TEXT,
        uf INTEGER,
        cidade INTEGER,
        bairro TEXT,
        cep TEXT,
        complemento TEXT,
        quadra TEXT,
        conjunto TEXT,
        setor TEXT,
        lote TEXT,
        loteamento TEXT,
        contribuinte TEXT,
        rural_car TEXT,
        rural_nirf TEXT,
        rural_ccir TEXT,
        rural_numero_incra TEXT,
        rural_sigef TEXT,
        rural_denominacaorural TEXT,
        rural_acidentegeografico TEXT,
        condominio_nome TEXT,
        condominio_bloco TEXT,
        condominio_conjunto TEXT,
        condominio_torre TEXT,
        condominio_apto TEXT,
        condominio_vaga TEXT,
        arquivo_tiff TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    """)
    conn.commit()
    conn.close()

# OCR + PARSE
def ocr_tiff_to_text(tiff_path):
    img = Image.open(tiff_path)
    return pytesseract.image_to_string(img)

def parse_text_to_dict(text):
    """
    Extrai dados do OCR.
    - tenta identificar cidade & UF no texto
    - se não encontrar, usa padrão:
        CIDADE = 1302504 (Manacapuru)
        UF = 13 (Amazonas)
    """
    import re

    def find(pattern, default=""):
        m = re.search(pattern, text, flags=re.IGNORECASE)
        return m.group(1).strip() if m else default

    upper_text = text.upper()

    # 1) PADRÕES (caso não ache nada)
    cidade_codigo = 1302504  # Manacapuru
    uf_codigo = 13           # Amazonas

    # 2) Tenta achar cidade pelo nome
    for nome, cod in CIDADE_NOME_TO_IBGE.items():
        if nome in upper_text:
            cidade_codigo = cod
            uf_codigo = cod // 100000  # primeiros 2 dígitos = UF
            break

    # 3) Tenta achar UF explícita: "/AM", "/PA", etc.
    m = re.search(r"/([A-Z]{2})", upper_text)
    if m:
        sigla = m.group(1)
        if sigla in UF_SIGLA_TO_COD:
            uf_codigo = UF_SIGLA_TO_COD[sigla]

    data = {
        "NUMERO_REGISTRO": find(r"REGISTRO[:\s]+(\S+)", ""),

        "VARIOS_ENDERECOS": find(r"VARIOS\s*ENDERECOS[:\s]+([SN])", "N"),
        "REGISTRO_TIPO": int(find(r"REGISTRO\s*TIPO[:\s]+(\d+)", "1") or 1),
        "TIPO_DE_IMOVEL": int(find(r"TIPO\s*DE\s*IMOVEL[:\s]+(\d+)", "1") or 1),
        "LOCALIZACAO": int(find(r"LOCALIZACAO[:\s]+(\d+)", "0") or 0),
        "TIPO_LOGRADOURO": int(find(r"TIPO\s*LOGRADOURO[:\s]+(\d+)", "250") or 250),

        "NOME_LOGRADOURO": find(r"NOME\s*LOGRADOURO[:\s]+(.+)", ""),
        "NUMERO_LOGRADOURO": find(r"NUMERO\s*LOGRADOURO[:\s]+(\S+)", ""),

        "UF": uf_codigo,
        "CIDADE": cidade_codigo,

        "BAIRRO": find(r"BAIRRO[:\s]+(.+)", ""),
        "CEP": find(r"CEP[:\s]+(\S+)", ""),
        "COMPLEMENTO": find(r"COMPLEMENTO[:\s]+(.+)", ""),
        "QUADRA": find(r"QUADRA[:\s]+(.+)", ""),
        "CONJUNTO": find(r"CONJUNTO[:\s]+(.+)", ""),
        "SETOR": find(r"SETOR[:\s]+(.+)", ""),
        "LOTE": find(r"LOTE[:\s]+(.+)", ""),
        "LOTEAMENTO": find(r"LOTEAMENTO[:\s]+(.+)", ""),

        "CONTRIBUINTE": [find(r"CONTRIBUINTE[:\s]+(\S+)", "")]
    }

    return data



def row_to_indicador_item(row, tipoenvio):
    base = row_to_json(row)

    return {
        "TIPOENVIO": tipoenvio,
        "NUMERO_REGISTRO": base["numero_registro"],
        "VARIOS_ENDERECOS": base["varios_enderecos"],
        "REGISTRO_TIPO": base["registro_tipo"],
        "TIPO_DE_IMOVEL": base["tipo_de_imovel"],
        "LOCALIZACAO": base["localizacao"],
        "TIPO_LOGRADOURO": base["tipo_logradouro"],
        "NOME_LOGRADOURO": base["nome_logradouro"],
        "NUMERO_LOGRADOURO": base["numero_logradouro"],
        "UF": base["uf"],
        "CIDADE": base["cidade"],
        "BAIRRO": base["bairro"],
        "CEP": base["cep"].replace("-", ""),
        "COMPLEMENTO": base["complemento"],
        "QUADRA": base["quadra"],
        "CONJUNTO": base["conjunto"],
        "SETOR": base["setor"],
        "LOTE": base["lote"],
        "LOTEAMENTO": base["loteamento"],
        "CONTRIBUINTE": base["contribuinte"],
        "RURAL": base["RURAL"],
        "CONDOMINIO": base["CONDOMINIO"]
    }

def export_to_json(db_path, output_path, since=None, tipoenvio=0):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    if since:
        cur.execute("SELECT * FROM imoveis WHERE updated_at >= ? ORDER BY id", (since,))
    else:
        cur.execute("SELECT * FROM imoveis ORDER BY id")

    rows = cur.fetchall()
    conn.close()

    real_list = [row_to_indicador_item(r, tipoenvio) for r in rows]

    payload = {
        "INDICADOR_REAL": {
            "CNS": CNS_CODIGO,
            "REAL": real_list
        }
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

def export_to_excel(db_path, output_path, since=None):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    if since:
        cur.execute("SELECT * FROM imoveis WHERE updated_at >= ? ORDER BY id", (since,))
    else:
        cur.execute("SELECT * FROM imoveis ORDER BY id")

    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    conn.close()

    pd.DataFrame(rows, columns=cols).to_excel(output_path, index=False)
# ----------------------------------------------------------
# INTERFACE
# ----------------------------------------------------------

class ImoveisApp(tk.Tk):
    def __init__(self, db_path=DB_DEFAULT):
        super().__init__()
        self.title("Indicador Real - Cadastro de Matrículas")
        self.geometry("1180x680")

        self.db_path = db_path
        self.selected_id = None
        self.import_queue = queue.Queue()
        self.import_running = False

        self.create_widgets()
        self.load_registros()


    def create_widgets(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=5)

        ttk.Button(top, text="Importar TIFF", command=self.importar_tiffs).pack(side="left", padx=5)
        ttk.Button(top, text="Visualizar TIFF", command=self.visualizar_tiff).pack(side="left", padx=5)

        ttk.Label(top, text="Últimas alterações desde (ISO):").pack(side="left", padx=5)
        self.entry_since = ttk.Entry(top, width=25)
        self.entry_since.insert(0, "2025-01-01T00:00:00")
        self.entry_since.pack(side="left", padx=5)

        ttk.Button(top, text="Exportar JSON (Completo)", command=self.exportar_json_completo).pack(side="left", padx=5)
        ttk.Button(top, text="Exportar JSON (Alterações)", command=self.exportar_json_alteracoes).pack(side="left", padx=5)
        ttk.Button(top, text="Exportar Excel", command=self.exportar_excel).pack(side="left", padx=5)

        main = ttk.Frame(self)
        main.pack(fill="both", expand=True, padx=10, pady=10)

        left = ttk.Frame(main)
        left.pack(side="left", fill="y")

        ttk.Label(left, text="Registros:").pack()

        self.tree = ttk.Treeview(
            left,
            columns=("ID","NUM","LOGR","BAIRRO"),
            show="headings",
            height=25
        )
        for col, txt, w in [
            ("ID","ID",40),
            ("NUM","Matrícula",120),
            ("LOGR","Logradouro",200),
            ("BAIRRO","Bairro",150)
        ]:
            self.tree.heading(col, text=txt)
            self.tree.column(col, width=w)

        self.tree.pack(fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        right = ttk.Frame(main)
        right.pack(side="left", fill="both", expand=True, padx=10)

        self.entries = {}
        self.combos = {}

        def add_entry(row, label, key):
            ttk.Label(right, text=label+":").grid(row=row, column=0, sticky="e", padx=5, pady=2)
            ent = ttk.Entry(right, width=40)
            ent.grid(row=row, column=1, sticky="w")
            self.entries[key] = ent

        def add_combo(row, label, key, options):
            ttk.Label(right, text=label+":").grid(row=row, column=0, sticky="e", padx=5, pady=2)
            cb = ttk.Combobox(right, width=37, values=options, state="readonly")
            cb.grid(row=row, column=1, sticky="w")
            self.combos[key] = cb

        row = 0

        add_entry(row, "Matrícula", "NUMERO_REGISTRO"); row+=1
        add_combo(row, "Tipo Registro", "REGISTRO_TIPO", make_combo_values(REGISTRO_TIPO_OPCOES)); row+=1
        add_combo(row, "Localização", "LOCALIZACAO", make_combo_values(LOCALIZACAO_OPCOES)); row+=1
        add_combo(row, "Tipo Imóvel", "TIPO_DE_IMOVEL", make_combo_values(TIPO_IMOVEL_OPCOES)); row+=1
        add_combo(row, "Tipo Logradouro", "TIPO_LOGRADOURO", make_combo_values(TIPO_LOGRADOURO_OPCOES)); row+=1

        add_entry(row, "Nome Logradouro", "NOME_LOGRADOURO"); row+=1
        add_entry(row, "Número Logradouro", "NUMERO_LOGRADOURO"); row+=1
        add_combo(row, "UF", "UF", make_combo_values(UF_OPCOES)); row+=1
        add_entry(row, "Cidade (IBGE)", "CIDADE"); row+=1

        add_entry(row, "Bairro", "BAIRRO"); row+=1
        add_entry(row, "CEP", "CEP"); row+=1
        add_entry(row, "Complemento", "COMPLEMENTO"); row+=1
        add_entry(row, "Quadra", "QUADRA"); row+=1
        add_entry(row, "Conjunto", "CONJUNTO"); row+=1
        add_entry(row, "Setor", "SETOR"); row+=1
        add_entry(row, "Lote", "LOTE"); row+=1
        add_entry(row, "Loteamento", "LOTEAMENTO"); row+=1
        add_entry(row, "Vários Endereços (S/N)", "VARIOS_ENDERECOS"); row+=1
        add_entry(row, "Contribuinte(s)", "CONTRIBUINTE"); row+=1

        ttk.Button(right, text="Salvar Alterações", command=self.salvar_alteracoes).grid(
            row=row, column=0, columnspan=2, pady=10
        )

        bottom = ttk.Frame(self)
        bottom.pack(fill="x", padx=10)

        self.progress = ttk.Progressbar(bottom, length=400, mode="determinate")
        self.progress.pack(side="left", padx=5)

        self.progress_label = ttk.Label(bottom, text="Pronto.")
        self.progress_label.pack(side="left", padx=5)

    # ---------------------------------------------
    # LISTA
    # ---------------------------------------------

    def load_registros(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT id, numero_registro, nome_logradouro, bairro FROM imoveis ORDER BY id")
        for rid, mat, logr, bairro in cur.fetchall():
            self.tree.insert("", "end", values=(rid, mat or "", logr or "", bairro or ""))
        conn.close()

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        rid = self.tree.item(sel[0])["values"][0]
        self.selected_id = int(rid)
        self.carregar_registro()

    def carregar_registro(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT * FROM imoveis WHERE id=?", (self.selected_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return

        data = row_to_json(row)

        def set_entry(k, val):
            w = self.entries.get(k)
            if w:
                w.delete(0, tk.END)
                w.insert(0, val if val is not None else "")

        def set_combo(k, codigo, mapping):
            cb = self.combos.get(k)
            if cb:
                cb.set(codigo_to_combo(codigo, mapping))

        # Entradas
        set_entry("NUMERO_REGISTRO", data["numero_registro"])
        set_entry("NOME_LOGRADOURO", data["nome_logradouro"])
        set_entry("NUMERO_LOGRADOURO", data["numero_logradouro"])
        set_entry("CIDADE", data["cidade"])
        set_entry("BAIRRO", data["bairro"])
        set_entry("CEP", data["cep"])
        set_entry("COMPLEMENTO", data["complemento"])
        set_entry("QUADRA", data["quadra"])
        set_entry("CONJUNTO", data["conjunto"])
        set_entry("SETOR", data["setor"])
        set_entry("LOTE", data["lote"])
        set_entry("LOTEAMENTO", data["loteamento"])
        set_entry("VARIOS_ENDERECOS", data["varios_enderecos"])
        set_entry("CONTRIBUINTE", ", ".join(data["contribuinte"]))

        # Combos
        set_combo("REGISTRO_TIPO", data["registro_tipo"], REGISTRO_TIPO_OPCOES)
        set_combo("LOCALIZACAO", data["localizacao"], LOCALIZACAO_OPCOES)
        set_combo("TIPO_DE_IMOVEL", data["tipo_de_imovel"], TIPO_IMOVEL_OPCOES)
        set_combo("TIPO_LOGRADOURO", data["tipo_logradouro"], TIPO_LOGRADOURO_OPCOES)
        set_combo("UF", data["uf"], UF_OPCOES)

    # ----------------------------------------------------------
    # IMPORTAÇÃO TIFF
    # ----------------------------------------------------------

    def importar_tiffs(self):
        """Abre o diálogo e inicia a importação em uma thread separada."""
        if self.import_running:
            messagebox.showinfo("Importação", "Uma importação já está em andamento.")
            return

        files = filedialog.askopenfilenames(
            title="Selecione TIFFs",
            filetypes=[("Arquivos TIFF", "*.tif *.tiff")]
        )
        if not files:
            return

        self.import_running = True
        self.progress["maximum"] = len(files)
        self.progress["value"] = 0
        self.progress_label.config(text=f"0/{len(files)} importadas")
        self.update_idletasks()

        # limpa a fila
        with self.import_queue.mutex:
            self.import_queue.queue.clear()

        # inicia thread de trabalho
        t = threading.Thread(
            target=self._worker_importar_tiffs,
            args=(files,),
            daemon=True
        )
        t.start()

        # começa a checar a fila periodicamente
        self.after(100, self._check_import_queue)

    def _worker_importar_tiffs(self, files):
        """Roda em background: faz OCR e grava no banco."""
        total = len(files)
        ok = 0
        erros = []

        for i, fp in enumerate(files, start=1):
            try:
                txt = ocr_tiff_to_text(fp)
                data = parse_text_to_dict(txt)
                save_dict_to_db(data, tiff_path=fp)
                ok += 1
            except Exception as e:
                erros.append(f"{os.path.basename(fp)}: {e}")

            # envia atualização de progresso para a thread principal
            self.import_queue.put({"type": "progress", "i": i, "total": total})

        # sinaliza conclusão
        self.import_queue.put({
            "type": "done",
            "ok": ok,
            "total": total,
            "erros": erros,
        })

    def _check_import_queue(self):
        """Lê mensagens da fila e atualiza a interface (roda na thread principal)."""
        try:
            while True:
                msg = self.import_queue.get_nowait()

                if msg["type"] == "progress":
                    i = msg["i"]
                    total = msg["total"]
                    self.progress["value"] = i
                    self.progress_label.config(text=f"{i}/{total} importadas")

                elif msg["type"] == "done":
                    self.import_running = False
                    ok = msg["ok"]
                    total = msg["total"]
                    erros = msg["erros"]

                    self.load_registros()

                    resumo = f"{ok}/{total} matrículas importadas."
                    if erros:
                        resumo += "\n\nErros:\n" + "\n".join(erros)

                    self.progress_label.config(text="Importação concluída.")
                    messagebox.showinfo("Importação", resumo)

        except queue.Empty:
            pass

        # se ainda estiver importando, agenda nova checagem
        if self.import_running:
            self.after(100, self._check_import_queue)
        else:
            self.progress["value"] = 0

    # ----------------------------------------------------------
    # VISUALIZAR TIFF
    # ----------------------------------------------------------

    def visualizar_tiff(self):
        if not self.selected_id:
            messagebox.showwarning("Aviso", "Selecione um registro.")
            return

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT arquivo_tiff FROM imoveis WHERE id=?", (self.selected_id,))
        row = cur.fetchone()
        conn.close()

        if not row or not row[0]:
            messagebox.showwarning("Aviso", "Nenhum TIFF ligado ao registro.")
            return

        abrir_arquivo_no_sistema(row[0])

    # ----------------------------------------------------------
    # SALVAR ALTERAÇÕES
    # ----------------------------------------------------------

    def salvar_alteracoes(self):
        if not self.selected_id:
            return messagebox.showwarning("Aviso", "Nenhum registro selecionado.")

        try:
            campos = {}

            campos["numero_registro"] = self.entries["NUMERO_REGISTRO"].get().strip()
            campos["nome_logradouro"] = self.entries["NOME_LOGRADOURO"].get().strip()
            campos["numero_logradouro"] = self.entries["NUMERO_LOGRADOURO"].get().strip()

            cidade_raw = self.entries["CIDADE"].get().strip()
            campos["cidade"] = int(cidade_raw) if cidade_raw else 0

            campos["bairro"] = self.entries["BAIRRO"].get().strip()
            campos["cep"] = self.entries["CEP"].get().strip()
            campos["complemento"] = self.entries["COMPLEMENTO"].get().strip()
            campos["quadra"] = self.entries["QUADRA"].get().strip()
            campos["conjunto"] = self.entries["CONJUNTO"].get().strip()
            campos["setor"] = self.entries["SETOR"].get().strip()
            campos["lote"] = self.entries["LOTE"].get().strip()
            campos["loteamento"] = self.entries["LOTEAMENTO"].get().strip()
            campos["varios_enderecos"] = self.entries["VARIOS_ENDERECOS"].get().strip().upper()

            contrib_raw = self.entries["CONTRIBUINTE"].get().strip()
            campos["contribuinte"] = [c.strip() for c in contrib_raw.split(",") if c.strip()]

            campos["registro_tipo"] = combo_to_codigo(self.combos["REGISTRO_TIPO"].get())
            campos["localizacao"] = combo_to_codigo(self.combos["LOCALIZACAO"].get())
            campos["tipo_de_imovel"] = combo_to_codigo(self.combos["TIPO_DE_IMOVEL"].get())
            campos["tipo_logradouro"] = combo_to_codigo(self.combos["TIPO_LOGRADOURO"].get())
            campos["uf"] = combo_to_codigo(self.combos["UF"].get())

            update_imovel(self.selected_id, campos)
            messagebox.showinfo("OK", "Registro atualizado.")
            self.load_registros()

        except Exception as e:
            messagebox.showerror("Erro", str(e))

    # ----------------------------------------------------------
    # EXPORTAÇÕES
    # ----------------------------------------------------------

    def get_since(self):
        t = self.entry_since.get().strip()
        return t if t else None

    def exportar_json_completo(self):
        arq = filedialog.asksaveasfilename(defaultextension=".json")
        if not arq:
            return
        export_to_json(self.db_path, arq, since=None, tipoenvio=0)
        messagebox.showinfo("OK", "JSON completo gerado.")

    def exportar_json_alteracoes(self):
        arq = filedialog.asksaveasfilename(defaultextension=".json")
        if not arq:
            return
        export_to_json(self.db_path, arq, since=self.get_since(), tipoenvio=1)
        messagebox.showinfo("OK", "JSON de alterações gerado.")

    def exportar_excel(self):
        arq = filedialog.asksaveasfilename(defaultextension=".xlsx")
        if not arq:
            return
        export_to_excel(self.db_path, arq, since=self.get_since())
        messagebox.showinfo("OK", "Excel gerado.")


def main():
    init_db()
    app = ImoveisApp()
    app.mainloop()

if __name__ == "__main__":
    main()
