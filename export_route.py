
@app.route("/exportar_json")
@login_required
def exportar_json():
    # Exporta tabela imoveis para JSON
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM imoveis")
    rows = cur.fetchall()
    conn.close()

    lista = [dict(row) for row in rows]
    json_str = json.dumps(lista, default=str, indent=4) # default=str handles datetime

    return Response(
        json_str,
        mimetype="application/json",
        headers={"Content-disposition": "attachment; filename=imoveis_export.json"}
    )
