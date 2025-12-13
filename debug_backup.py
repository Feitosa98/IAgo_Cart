
import os
import shutil
from datetime import datetime
import sqlite3

def test_backup():
    print("Iniciando teste de backup...")
    DB_PATH = "imoveis.db"
    backup_dir = "backups"
    
    if not os.path.exists(DB_PATH):
        print(f"ERRO: Banco de dados {DB_PATH} não encontrado.")
        return

    try:
        if not os.path.exists(backup_dir):
            print(f"Criando diretório {backup_dir}...")
            os.makedirs(backup_dir)
        else:
            print(f"Diretório {backup_dir} já existe.")
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"imoveis_backup_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_file)
        
        print(f"Tentando copiar para {backup_path}...")
        shutil.copy2(DB_PATH, backup_path)
        
        if os.path.exists(backup_path):
             print(f"SUCESSO: Arquivo criado. Tamanho: {os.path.getsize(backup_path)} bytes.")
        else:
             print("ERRO: Arquivo não encontrado após cópia.")

    except Exception as e:
        print(f"EXCEÇÃO: {e}")

if __name__ == "__main__":
    test_backup()
