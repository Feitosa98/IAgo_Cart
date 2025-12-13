import json
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

# Caminho do Tesseract no seu computador
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

DB_DEFAULT = "imoveis.db"


# =====================================================================
# FUNÇÕES AUXILIARES DO SISTEMA
# =====================================================================

def abrir_arquivo_no_sistema(file_path: str):
    """Abre o arquivo no visualizador padrão do Windows, corrigindo caminhos UNC."""
    try:
        # Normalizar barras
        file_path = file_path.replace("/", "\\")
        
        # Garantir que caminho UNC tenha duas barras no início
        if file_path.startswith("\\\\") is False and file_path.startswith("\\"):
            file_path = "\\" + file_path
        if file_path.startswith("\\\\") is False and file_path.startswith("//"):
            file_path = "\\" + file_path[1:]

        # Verificar existência do arquivo
        if not os.path.exists(file_path):
            messagebox.showerror("Erro", f"Arquivo não encontrado:\n{file_path}")
            return

        os.startfile(file_path)

    except Exception as e:
        messagebox.showerror("Erro ao abrir arquivo", str(e))


# =====================================================================
# BANCO DE DADOS
# =====================================================================

def init_db(db_path: str = DB_DEFAULT):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
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
        """
    )
    conn.commit()
    conn.close()


# =====================================================================
# OCR / PARSE
# =====================================================================

def ocr_tiff_to_text(tiff_path: str) -> str:
    image = Image.open(tiff_path)
    # Sem lang="por" para evitar erro se idioma português não estiver instalado.
    return pytesseract.image_to_string(image)


def parse_text_to_dict(text: str) -> dict:
    """
    MODELO de extração.
    Ajuste os padrões conforme o layout real do documento.
    """
    import re

    def search(pattern, default=""):
        m = re.search(pattern, text, flags=re.IGNORECASE)
        return m.group(1).strip() if m else default

    data = {
        "NUMERO_REGISTRO": search(r"NUMERO\s*REGISTRO[:\s]+(\S+)"),
        "VARIOS_ENDERECOS": search(r"VARIOS\s*ENDERECOS[:\s]+([SN])", "N"),
        "REGISTRO_TIPO": int(search(r"REGISTRO\s*TIPO[:\s]+(\d+)", "1") or 1),
        "TIPO_DE_IMOVEL": int(search(r"TIPO\s*DE\s*IMOVEL[:\s]+(\d+)", "1") or 1),
        "LOCALIZACAO": int(search(r"LOCALIZACAO[:\s]+(\d+)", "0") or 0),
        "TIPO_LOGRADOURO": int(search(r"TIPO\s*LOGRADOURO[:\s]+(\d+)", "0") or 0),
        "NOME_LOGRADOURO": search(r"NOME\s*LOGRADOURO[:\s]+(.+)"),
        "NUMERO_LOGRADOURO": search(r"N[ÚU]MERO\s*LOGRADOURO[:\s]+(\S+)"),
        "UF": int(search(r"UF[:\s]+(\d+)", "0") or 0),
        "CIDADE": int(search(r"CIDADE[:\s]+(\d+)", "0") or 0),
        "BAIRRO": search(r"BAIRRO[:\s]+(.+)"),
        "CEP": search(r"CEP[:\s]+([\d\-]+)"),
        "COMPLEMENTO": search(r"COMPLEMENTO[:\s]+(.+)"),
        "QUADRA": search(r"QUADRA[:\s]+(.+)"),
        "CONJUNTO": search(r"CONJUNTO[:\s]+(.+)"),
        "SETOR": search(r"SETOR[:\s]+(.+)"),
        "LOTE": search(r"LOTE[:\s]+(.+)"),
        "LOTEAMENTO": search(r"LOTEAMENTO[:\s]+(.+)"),
        "CONTRIBUINTE": [search(r"CONTRIBUINTE[:\s]+(\S+)", "")],
        "RURAL": {
            "CAR": search(r"CAR[:\s]+(\S*)"),
            "NIRF": search(r"NIRF[:\s]+(\S*)"),
            "CCIR": search(r"CCIR[:\s]+(\S*)"),
            "NUMERO_INCRA": search(r"NUMERO\s*INCRA[:\s]+(\S*)"),
            "SIGEF": search(r"SIGEF[:\s]+(\S*)"),
            "DENOMINACAORURAL": search(r"DENOMINACAO\s*RURAL[:\s]+(.+)"),
            "ACIDENTEGEOGRAFICO": search(r"ACIDENTE\s*GEOGRAFICO[:\s]+(.+)"),
        },
        "CONDOMINIO": {
            "NOME_CONDOMINIO": search(r"NOME\s*CONDOMINIO[:\s]+(.+)"),
            "BLOCO": search(r"BLOCO[:\s]+(.+)"),
            "CONJUNTO": search(r"CONJUNTO\s*COND[:\s]+(.+)"),
            "TORRE": search(r"TORRE[:\s]+(.+)"),
            "APTO": search(r"APTO[:\s]+(.+)"),
            "VAGA": search(r"VAGA[:\s]+(.+)"),
        },
    }

    return data


# =====================================================================
# CRUD NO BANCO
# =====================================================================

def save_dict_to_db(data: dict, tiff_path: str | None = None, db_path: str = DB_DEFAULT) -> int:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()

    rural = data.get("RURAL", {})
    cond = data.get("CONDOMINIO", {})

    cur.execute(
        """
        INSERT INTO imoveis (
            numero_registro, varios_enderecos, registro_tipo, tipo_de_imovel,
            localizacao, tipo_logradouro, nome_logradouro, numero_logradouro,
            uf, cidade, bairro, cep, complemento, quadra, conjunto,
            setor, lote, loteamento, contribuinte,
            rural_car, rural_nirf, rural_ccir, rural_numero_incra,
            rural_sigef, rural_denominacaorural, rural_acidentegeografico,
            condominio_nome, condominio_bloco, condominio_conjunto,
            condominio_torre, condominio_apto, condominio_vaga,
            arquivo_tiff, created_at, updated_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            data.get("NUMERO_REGISTRO"),
            data.get("VARIOS_ENDERECOS"),
            data.get("REGISTRO_TIPO"),
            data.get("TIPO_DE_IMOVEL"),
            data.get("LOCALIZACAO"),
            data.get("TIPO_LOGRADOURO"),
            data.get("NOME_LOGRADOURO"),
            data.get("NUMERO_LOGRADOURO"),
            data.get("UF"),
            data.get("CIDADE"),
            data.get("BAIRRO"),
            data.get("CEP"),
            data.get("COMPLEMENTO"),
            data.get("QUADRA"),
            data.get("CONJUNTO"),
            data.get("SETOR"),
            data.get("LOTE"),
            data.get("LOTEAMENTO"),
            json.dumps(data.get("CONTRIBUINTE", [])),
            rural.get("CAR"),
            rural.get("NIRF"),
            rural.get("CCIR"),
            rural.get("NUMERO_INCRA"),
            rural.get("SIGEF"),
            rural.get("DENOMINACAORURAL"),
            rural.get("ACIDENTEGEOGRAFICO"),
            cond.get("NOME_CONDOMINIO"),
            cond.get("BLOCO"),
            cond.get("CONJUNTO"),
            cond.get("TORRE"),
            cond.get("APTO"),
            cond.get("VAGA"),
            tiff_path,
            now,
            now,
        ),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def update_imovel(imovel_id: int, campos: dict, db_path: str = DB_DEFAULT):
    if not campos:
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    sets = []
    values = []
    for k, v in campos.items():
        col = {
            "NUMERO_REGISTRO": "numero_registro",
            "VARIOS_ENDERECOS": "varios_enderecos",
            "REGISTRO_TIPO": "registro_tipo",
            "TIPO_DE_IMOVEL": "tipo_de_imovel",
            "LOCALIZACAO": "localizacao",
            "TIPO_LOGRADOURO": "tipo_logradouro",
            "NOME_LOGRADOURO": "nome_logradouro",
            "NUMERO_LOGRADOURO": "numero_logradouro",
            "UF": "uf",
            "CIDADE": "cidade",
            "BAIRRO": "bairro",
            "CEP": "cep",
            "COMPLEMENTO": "complemento",
            "QUADRA": "quadra",
            "CONJUNTO": "conjunto",
            "SETOR": "setor",
            "LOTE": "lote",
            "LOTEAMENTO": "loteamento",
            "CONTRIBUINTE": "contribuinte",
        }.get(k)
        if col:
            sets.append(f"{col} = ?")
            if k == "CONTRIBUINTE":
                values.append(json.dumps(v))
            else:
                values.append(v)

    if not sets:
        conn.close()
        return

    sets.append("updated_at = ?")
    values.append(datetime.utcnow().isoformat())
    values.append(imovel_id)

    sql = "UPDATE imoveis SET " + ", ".join(sets) + " WHERE id = ?"
    cur.execute(sql, values)
    conn.commit()
    conn.close()


def row_to_json(row) -> dict:
    (
        _id,
        numero_registro,
        varios_enderecos,
        registro_tipo,
        tipo_de_imovel,
        localizacao,
        tipo_logradouro,
        nome_logradouro,
        numero_logradouro,
        uf,
        cidade,
        bairro,
        cep,
        complemento,
        quadra,
        conjunto,
        setor,
        lote,
        loteamento,
        contribuinte,
        rural_car,
        rural_nirf,
        rural_ccir,
        rural_numero_incra,
        rural_sigef,
        rural_denominacaorural,
        rural_acidentegeografico,
        condominio_nome,
        condominio_bloco,
        condominio_conjunto,
        condominio_torre,
        condominio_apto,
        condominio_vaga,
        arquivo_tiff,
        created_at,
        updated_at,
    ) = row

    return {
        "ID": _id,
        "NUMERO_REGISTRO": numero_registro,
        "VARIOS_ENDERECOS": varios_enderecos,
        "REGISTRO_TIPO": registro_tipo,
        "TIPO_DE_IMOVEL": tipo_de_imovel,
        "LOCALIZACAO": localizacao,
        "TIPO_LOGRADOURO": tipo_logradouro,
        "NOME_LOGRADOURO": nome_logradouro,
        "NUMERO_LOGRADOURO": numero_logradouro,
        "UF": uf,
        "CIDADE": cidade,
        "BAIRRO": bairro,
        "CEP": cep,
        "COMPLEMENTO": complemento,
        "QUADRA": quadra,
        "CONJUNTO": conjunto,
        "SETOR": setor,
        "LOTE": lote,
        "LOTEAMENTO": loteamento,
        "CONTRIBUINTE": json.loads(contribuinte) if contribuinte else [],
        "RURAL": {
            "CAR": rural_car or "",
            "NIRF": rural_nirf or "",
            "CCIR": rural_ccir or "",
            "NUMERO_INCRA": rural_numero_incra or "",
            "SIGEF": rural_sigef or "",
            "DENOMINACAORURAL": rural_denominacaorural or "",
            "ACIDENTEGEOGRAFICO": rural_acidentegeografico or "",
        },
        "CONDOMINIO": {
            "NOME_CONDOMINIO": condominio_nome or "",
            "BLOCO": condominio_bloco or "",
            "CONJUNTO": condominio_conjunto or "",
            "TORRE": condominio_torre or "",
            "APTO": condominio_apto or "",
            "VAGA": condominio_vaga or "",
        },
        "ARQUIVO_TIFF": arquivo_tiff,
        "CREATED_AT": created_at,
        "UPDATED_AT": updated_at,
    }


def export_to_json(db_path: str, output_path: str, since: str | None = None):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    if since:
        cur.execute(
            "SELECT * FROM imoveis WHERE updated_at >= ? ORDER BY id",
            (since,),
        )
    else:
        cur.execute("SELECT * FROM imoveis ORDER BY id")

    rows = cur.fetchall()
    conn.close()

    data = [row_to_json(r) for r in rows]
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def export_to_excel(db_path: str, output_path: str, since: str | None = None):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    if since:
        cur.execute(
            "SELECT * FROM imoveis WHERE updated_at >= ? ORDER BY id",
            (since,),
        )
    else:
        cur.execute("SELECT * FROM imoveis ORDER BY id")

    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    conn.close()

    df = pd.DataFrame(rows, columns=cols)
    df.to_excel(output_path, index=False)


# =====================================================================
# INTERFACE GRÁFICA
# =====================================================================

class ImoveisApp(tk.Tk):
    def __init__(self, db_path=DB_DEFAULT):
        super().__init__()
        self.title("Cadastro de Imóveis - ONR Indicador Real")
        self.geometry("1100x620")

        self.db_path = db_path
        self.selected_id = None

        self.create_widgets()
        self.load_registros()

    def create_widgets(self):
        # Frame de topo (botões principais)
        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", padx=10, pady=5)

        btn_importar = ttk.Button(top_frame, text="Importar TIFF", command=self.importar_tiff)
        btn_importar.pack(side="left", padx=5)

        btn_ver_tiff = ttk.Button(top_frame, text="Visualizar TIFF", command=self.visualizar_tiff)
        btn_ver_tiff.pack(side="left", padx=5)

        ttk.Label(top_frame, text="Desde (ISO p/ últimas alterações):").pack(side="left", padx=5)
        self.entry_since = ttk.Entry(top_frame, width=25)
        self.entry_since.pack(side="left", padx=5)
        self.entry_since.insert(0, "2025-01-01T00:00:00")

        btn_json_completo = ttk.Button(
            top_frame, text="Exportar JSON (Completo)", command=self.exportar_json_completo
        )
        btn_json_completo.pack(side="left", padx=5)

        btn_json_alt = ttk.Button(
            top_frame, text="Exportar JSON (Alterações)", command=self.exportar_json_alteracoes
        )
        btn_json_alt.pack(side="left", padx=5)

        btn_xlsx_completo = ttk.Button(
            top_frame, text="Exportar Excel (Completo)", command=self.exportar_excel_completo
        )
        btn_xlsx_completo.pack(side="left", padx=5)

        btn_xlsx_alt = ttk.Button(
            top_frame, text="Exportar Excel (Alterações)", command=self.exportar_excel_alteracoes
        )
        btn_xlsx_alt.pack(side="left", padx=5)

        # Frame principal dividido em lista + formulário
        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # ---- LISTA DE REGISTROS ----
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side="left", fill="y")

        ttk.Label(left_frame, text="Registros:").pack(anchor="w")

        self.tree = ttk.Treeview(left_frame, columns=("ID", "NUM", "LOGR", "BAIRRO"), show="headings", height=25)
        self.tree.heading("ID", text="ID")
        self.tree.heading("NUM", text="Número Registro")
        self.tree.heading("LOGR", text="Logradouro")
        self.tree.heading("BAIRRO", text="Bairro")
        self.tree.column("ID", width=40)
        self.tree.column("NUM", width=120)
        self.tree.column("LOGR", width=180)
        self.tree.column("BAIRRO", width=140)
        self.tree.pack(fill="y", expand=False)

        self.tree.bind("<<TreeviewSelect>>", self.on_select_registro)

        # ---- FORMULÁRIO DE EDIÇÃO ----
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side="left", fill="both", expand=True, padx=10)

        self.entries = {}

        def add_field(row, label_text, key):
            lbl = ttk.Label(right_frame, text=label_text + ":")
            lbl.grid(row=row, column=0, sticky="e", padx=5, pady=2)
            ent = ttk.Entry(right_frame, width=40)
            ent.grid(row=row, column=1, sticky="w", padx=5, pady=2)
            self.entries[key] = ent

        row = 0
        add_field(row, "Número Registro", "NUMERO_REGISTRO"); row += 1
        add_field(row, "Vários Endereços (S/N)", "VARIOS_ENDERECOS"); row += 1
        add_field(row, "Registro Tipo", "REGISTRO_TIPO"); row += 1
        add_field(row, "Tipo de Imóvel", "TIPO_DE_IMOVEL"); row += 1
        add_field(row, "Localização", "LOCALIZACAO"); row += 1
        add_field(row, "Tipo Logradouro", "TIPO_LOGRADOURO"); row += 1
        add_field(row, "Nome Logradouro", "NOME_LOGRADOURO"); row += 1
        add_field(row, "Número Logradouro", "NUMERO_LOGRADOURO"); row += 1
        add_field(row, "UF (código IBGE)", "UF"); row += 1
        add_field(row, "Cidade (código IBGE)", "CIDADE"); row += 1
        add_field(row, "Bairro", "BAIRRO"); row += 1
        add_field(row, "CEP", "CEP"); row += 1
        add_field(row, "Complemento", "COMPLEMENTO"); row += 1
        add_field(row, "Quadra", "QUADRA"); row += 1
        add_field(row, "Conjunto", "CONJUNTO"); row += 1
        add_field(row, "Setor", "SETOR"); row += 1
        add_field(row, "Lote", "LOTE"); row += 1
        add_field(row, "Loteamento", "LOTEAMENTO"); row += 1
        add_field(row, "Contribuinte (lista, separada por vírgula)", "CONTRIBUINTE"); row += 1

        btn_salvar = ttk.Button(right_frame, text="Salvar Alterações", command=self.salvar_alteracoes)
        btn_salvar.grid(row=row, column=0, columnspan=2, pady=10)

    # ---------------- LISTAGEM / CARREGAMENTO ----------------

    def load_registros(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT id, numero_registro, nome_logradouro, bairro FROM imoveis ORDER BY id")
        for row in cur.fetchall():
            _id, num, logr, bairro = row
            self.tree.insert("", "end", values=(str(_id), num or "", logr or "", bairro or ""))
        conn.close()

    def on_select_registro(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        item = self.tree.item(sel[0])
        _id = item["values"][0]
        self.selected_id = int(_id)
        self.carregar_registro(self.selected_id)

    def carregar_registro(self, imovel_id: int):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT * FROM imoveis WHERE id = ?", (imovel_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return

        data = row_to_json(row)

        # Preenche os campos
        self.entries["NUMERO_REGISTRO"].delete(0, tk.END)
        self.entries["NUMERO_REGISTRO"].insert(0, data.get("NUMERO_REGISTRO") or "")

        self.entries["VARIOS_ENDERECOS"].delete(0, tk.END)
        self.entries["VARIOS_ENDERECOS"].insert(0, data.get("VARIOS_ENDERECOS") or "")

        for key in [
            "REGISTRO_TIPO", "TIPO_DE_IMOVEL", "LOCALIZACAO", "TIPO_LOGRADOURO",
            "NOME_LOGRADOURO", "NUMERO_LOGRADOURO", "UF", "CIDADE", "BAIRRO", "CEP",
            "COMPLEMENTO", "QUADRA", "CONJUNTO", "SETOR", "LOTE", "LOTEAMENTO"
        ]:
            self.entries[key].delete(0, tk.END)
            val = data.get(key)
            self.entries[key].insert(0, "" if val is None else str(val))

        contrib = data.get("CONTRIBUINTE", [])
        self.entries["CONTRIBUINTE"].delete(0, tk.END)
        self.entries["CONTRIBUINTE"].insert(0, ", ".join(contrib))

    # ---------------- AÇÕES DE BOTÃO ----------------

    def importar_tiff(self):
        file_paths = filedialog.askopenfilenames(
            title="Selecione um ou mais arquivos TIFF",
            filetypes=[("Arquivos TIFF", "*.tif;*.tiff"), ("Todos os arquivos", "*.*")]
        )
        if not file_paths:
            return

        sucesso = 0
        erros = []

        for file_path in file_paths:
            try:
                text = ocr_tiff_to_text(file_path)
                data = parse_text_to_dict(text)
                save_dict_to_db(data, tiff_path=file_path, db_path=self.db_path)
                sucesso += 1
            except Exception as e:
                erros.append(f"{os.path.basename(file_path)}: {e}")

        self.load_registros()

        msg = f"{sucesso} arquivo(s) importado(s) com sucesso."
        if erros:
            msg += "\n\nOcorreram erros em:\n" + "\n".join(erros)

        if sucesso > 0:
            messagebox.showinfo("Importação concluída", msg)
        else:
            messagebox.showerror("Erro na importação", msg)

    def visualizar_tiff(self):
        if self.selected_id is None:
            messagebox.showwarning("Atenção", "Selecione um registro na lista para visualizar o TIFF.")
            return

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT arquivo_tiff FROM imoveis WHERE id = ?", (self.selected_id,))
        row = cur.fetchone()
        conn.close()

        if not row or not row[0]:
            messagebox.showwarning("Aviso", "Nenhum arquivo TIFF associado a este registro.")
            return

        caminho = row[0]
        abrir_arquivo_no_sistema(caminho)

    def salvar_alteracoes(self):
        if self.selected_id is None:
            messagebox.showwarning("Atenção", "Nenhum registro selecionado.")
            return

        try:
            campos = {
                "NUMERO_REGISTRO": self.entries["NUMERO_REGISTRO"].get().strip(),
                "VARIOS_ENDERECOS": self.entries["VARIOS_ENDERECOS"].get().strip() or "N",
                "REGISTRO_TIPO": int(self.entries["REGISTRO_TIPO"].get().strip() or "1"),
                "TIPO_DE_IMOVEL": int(self.entries["TIPO_DE_IMOVEL"].get().strip() or "1"),
                "LOCALIZACAO": int(self.entries["LOCALIZACAO"].get().strip() or "0"),
                "TIPO_LOGRADOURO": int(self.entries["TIPO_LOGRADOURO"].get().strip() or "0"),
                "NOME_LOGRADOURO": self.entries["NOME_LOGRADOURO"].get().strip(),
                "NUMERO_LOGRADOURO": self.entries["NUMERO_LOGRADOURO"].get().strip(),
                "UF": int(self.entries["UF"].get().strip() or "0"),
                "CIDADE": int(self.entries["CIDADE"].get().strip() or "0"),
                "BAIRRO": self.entries["BAIRRO"].get().strip(),
                "CEP": self.entries["CEP"].get().strip(),
                "COMPLEMENTO": self.entries["COMPLEMENTO"].get().strip(),
                "QUADRA": self.entries["QUADRA"].get().strip(),
                "CONJUNTO": self.entries["CONJUNTO"].get().strip(),
                "SETOR": self.entries["SETOR"].get().strip(),
                "LOTE": self.entries["LOTE"].get().strip(),
                "LOTEAMENTO": self.entries["LOTEAMENTO"].get().strip(),
            }

            contrib_raw = self.entries["CONTRIBUINTE"].get().strip()
            if contrib_raw:
                contrib_list = [c.strip() for c in contrib_raw.split(",") if c.strip()]
            else:
                contrib_list = []
            campos["CONTRIBUINTE"] = contrib_list

            update_imovel(self.selected_id, campos, db_path=self.db_path)
            messagebox.showinfo("Sucesso", "Alterações salvas.")
            self.load_registros()
        except ValueError:
            messagebox.showerror("Erro", "Campos numéricos com valores inválidos.")
        except Exception as e:
            messagebox.showerror("Erro ao salvar", str(e))

    # ---- EXPORTAÇÕES ----

    def get_since(self, require=False):
        since = self.entry_since.get().strip()
        if require and not since:
            messagebox.showwarning("Atenção", "Informe a data 'Desde' no campo superior.")
            return None
        return since or None

    def exportar_json_completo(self):
        filename = filedialog.asksaveasfilename(
            title="Salvar JSON (Completo)",
            defaultextension=".json",
            filetypes=[("JSON", "*.json")]
        )
        if not filename:
            return
        try:
            export_to_json(self.db_path, filename, since=None)
            messagebox.showinfo("Sucesso", f"JSON exportado para {filename}")
        except Exception as e:
            messagebox.showerror("Erro ao exportar JSON", str(e))

    def exportar_json_alteracoes(self):
        since = self.get_since(require=True)
        if not since:
            return
        filename = filedialog.asksaveasfilename(
            title="Salvar JSON (Alterações)",
            defaultextension=".json",
            filetypes=[("JSON", "*.json")]
        )
        if not filename:
            return
        try:
            export_to_json(self.db_path, filename, since=since)
            messagebox.showinfo("Sucesso", f"JSON exportado para {filename}")
        except Exception as e:
            messagebox.showerror("Erro ao exportar JSON", str(e))

    def exportar_excel_completo(self):
        filename = filedialog.asksaveasfilename(
            title="Salvar Excel (Completo)",
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")]
        )
        if not filename:
            return
        try:
            export_to_excel(self.db_path, filename, since=None)
            messagebox.showinfo("Sucesso", f"Excel exportado para {filename}")
        except Exception as e:
            messagebox.showerror("Erro ao exportar Excel", str(e))

    def exportar_excel_alteracoes(self):
        since = self.get_since(require=True)
        if not since:
            return
        filename = filedialog.asksaveasfilename(
            title="Salvar Excel (Alterações)",
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")]
        )
        if not filename:
            return
        try:
            export_to_excel(self.db_path, filename, since=since)
            messagebox.showinfo("Sucesso", f"Excel exportado para {filename}")
        except Exception as e:
            messagebox.showerror("Erro ao exportar Excel", str(e))


def main():
    init_db(DB_DEFAULT)
    app = ImoveisApp(db_path=DB_DEFAULT)
    app.mainloop()


if __name__ == "__main__":
    main()
