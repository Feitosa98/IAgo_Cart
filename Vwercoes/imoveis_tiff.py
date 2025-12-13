import argparse
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from PIL import Image
import pytesseract
import pandas as pd


DB_DEFAULT = "imoveis.db"


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
            created_at TEXT,
            updated_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def ocr_tiff_to_text(tiff_path: str) -> str:
    image = Image.open(tiff_path)
    # Se o TIFF tiver várias páginas, você pode iterar aqui.
    # Para simplificar, vamos assumir apenas a primeira página.
    return pytesseract.image_to_string(image, lang="por")  # ajuste o idioma se necessário


def parse_text_to_dict(text: str) -> dict:
    """
    MODELO de extração.
    Você vai ajustar os padrões (regex) conforme o layout real do seu documento.
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


def save_dict_to_db(data: dict, db_path: str = DB_DEFAULT) -> int:
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
            created_at, updated_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
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
            now,
            now,
        ),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def update_imovel(imovel_id: int, campos: dict, db_path: str = DB_DEFAULT):
    """
    Atualiza campos simples na tabela (nível 1).
    Você pode expandir para atualizar também RURAL/CONDOMINIO.
    """
    if not campos:
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    sets = []
    values = []
    for k, v in campos.items():
        # Mapeia chaves JSON para colunas
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


def import_tiff_command(args):
    init_db(args.db)
    text = ocr_tiff_to_text(args.tiff)
    data = parse_text_to_dict(text)
    new_id = save_dict_to_db(data, db_path=args.db)
    print(f"Registro salvo com ID {new_id} no banco {args.db}")


def export_json_command(args):
    mode = args.mode
    since = None
    if mode == "alteracoes" and args.since:
        since = args.since  # ISO 8601, ex: 2025-01-01T00:00:00

    export_to_json(args.db, args.output, since=since)
    print(f"JSON exportado para {args.output}")


def export_excel_command(args):
    mode = args.mode
    since = None
    if mode == "alteracoes" and args.since:
        since = args.since

    export_to_excel(args.db, args.output, since=since)
    print(f"Excel exportado para {args.output}")


def main():
    parser = argparse.ArgumentParser(
        description="Leitura de TIFF, extração de dados e armazenamento em banco SQLite."
    )
    parser.add_argument("--db", default=DB_DEFAULT, help="Caminho do banco SQLite")

    subparsers = parser.add_subparsers(dest="command")

    # Importar TIFF
    p_import = subparsers.add_parser("importar_tiff", help="Ler TIFF e salvar no banco")
    p_import.add_argument("tiff", help="Caminho do arquivo TIFF")
    p_import.set_defaults(func=import_tiff_command)

    # Exportar JSON
    p_json = subparsers.add_parser("exportar_json", help="Exportar dados para JSON")
    p_json.add_argument("output", help="Arquivo de saída .json")
    p_json.add_argument(
        "--mode",
        choices=["completo", "alteracoes"],
        default="completo",
        help="Exportação completa ou só alterações",
    )
    p_json.add_argument(
        "--since",
        help="Data/hora mínima (ISO 8601) para modo 'alteracoes', ex: 2025-01-01T00:00:00",
    )
    p_json.set_defaults(func=export_json_command)

    # Exportar Excel
    p_xlsx = subparsers.add_parser("exportar_excel", help="Exportar dados para Excel")
    p_xlsx.add_argument("output", help="Arquivo de saída .xlsx")
    p_xlsx.add_argument(
        "--mode",
        choices=["completo", "alteracoes"],
        default="completo",
        help="Exportação completa ou só alterações",
    )
    p_xlsx.add_argument(
        "--since",
        help="Data/hora mínima (ISO 8601) para modo 'alteracoes', ex: 2025-01-01T00:00:00",
    )
    p_xlsx.set_defaults(func=export_excel_command)

    args = parser.parse_args()

    if not hasattr(args, "func"):
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
