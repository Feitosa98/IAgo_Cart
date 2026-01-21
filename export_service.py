import os
import zipfile
import io
import json
from datetime import datetime
from db_manager import get_compat_conn

class ExportService:
    @staticmethod
    def generate_organized_zip(tenant_schema, user_id=None):
        """
        Gera um arquivo ZIP contendo todas as matrículas CONCLUÍDAS do tenant atual.
        Os arquivos são renomeados para o padrão do ConversorPro: {NumeroRegistro}.pdf
        """
        
        # 1. Connect to DB
        conn = get_compat_conn()
        cur = conn.cursor()
        
        try:
            # Set schema
            cur.execute(f"SET search_path TO {tenant_schema}, public")
            
            # Fetch Completed Imoveis
            # Selecionamos apenas os que tem arquivo_tiff (caminho do arquivo) e estão concluídos
            sql = """
                SELECT numero_registro, arquivo_tiff, ocr_text, dados_extraidos
                FROM imoveis 
                WHERE status_trabalho = 'CONCLUIDO' 
                AND arquivo_tiff IS NOT NULL
            """
            cur.execute(sql)
            rows = cur.fetchall()
            
            if not rows:
                return None, "Nenhuma matrícula concluída encontrada para exportação."

            # 2. Create ZIP in Memory
            memory_file = io.BytesIO()
            with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                added_count = 0
                
                for row in rows:
                    reg_num = row[0]
                    file_path = row[1]
                    # ocr_text = row[2] # Not using for now unless requested
                    
                    # Clean registry number for filename (remove invalid chars)
                    safe_reg_num = "".join([c for c in str(reg_num) if c.isalnum() or c in ('-','_')])
                    
                    if not file_path or not os.path.exists(file_path):
                        continue
                        
                    # Determine extension
                    _, ext = os.path.splitext(file_path)
                    if not ext:
                        ext = ".pdf" # Default
                        
                    # ConversorPro Pattern: Just the Registry Number ideally.
                    # Structure: /Matriculas/{safe_reg_num}{ext}
                    archive_name = f"Matriculas/{safe_reg_num}{ext}"
                    
                    zf.write(file_path, archive_name)
                    added_count += 1
                
                # Add a metadata summary file
                info = {
                    "generated_at": datetime.now().isoformat(),
                    "total_files": added_count,
                    "tenant": tenant_schema,
                    "exported_by_user_id": user_id
                }
                zf.writestr("export_info.json", json.dumps(info, indent=2))

            memory_file.seek(0)
            return memory_file, None
            
        except Exception as e:
            print(f"Error generating ZIP: {e}")
            return None, str(e)
        finally:
            conn.close()
