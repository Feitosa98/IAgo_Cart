import os
import zipfile
import io
import json
import tempfile
from datetime import datetime
from db_manager import get_compat_conn
from pdf2image import convert_from_path
from PIL import Image

class ExportService:
    @staticmethod
    def generate_organized_zip(tenant_schema, user_id=None):
        """
        Gera um arquivo ZIP contendo todas as matrículas CONCLUÍDAS.
        Converte arquivos PDF para TIFF (Multipage) se necessário.
        Renomeia para: {NumeroRegistro}.tif
        """
        
        conn = get_compat_conn()
        cur = conn.cursor()
        
        try:
            cur.execute(f"SET search_path TO {tenant_schema}, public")
            
            sql = """
                SELECT numero_registro, arquivo_tiff
                FROM imoveis 
                WHERE status_trabalho = 'CONCLUIDO' 
                AND arquivo_tiff IS NOT NULL
            """
            cur.execute(sql)
            rows = cur.fetchall()
            
            if not rows:
                return None, "Nenhuma matrícula concluída encontrada."

            memory_file = io.BytesIO()
            with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                added_count = 0
                
                with tempfile.TemporaryDirectory() as temp_dir:
                    for row in rows:
                        reg_num = row[0]
                        file_path = row[1]
                        
                        safe_reg_num = "".join([c for c in str(reg_num) if c.isalnum() or c in ('-','_')])
                        
                        if not file_path or not os.path.exists(file_path):
                            continue
                            
                        _, ext = os.path.splitext(file_path)
                        ext = ext.lower()
                        
                        # Target filename in ZIP
                        archive_name = f"Matriculas/{safe_reg_num}.tif"
                        
                        if ext in ['.tif', '.tiff']:
                            # Já é TIFF, apenas adiciona
                            zf.write(file_path, archive_name)
                            added_count += 1
                            
                        elif ext in ['.jpg', '.jpeg', '.png', '.bmp']:
                            # Converte Imagem para TIFF
                            try:
                                with Image.open(file_path) as img:
                                    temp_tiff_path = os.path.join(temp_dir, f"{safe_reg_num}.tif")
                                    # Convert to RGB (in case of RGBA/P) before saving if needed, 
                                    # but TIFF handles most. Let's just save.
                                    # Simple save as TIFF
                                    img.save(temp_tiff_path, compression="tiff_deflate")
                                    
                                    zf.write(temp_tiff_path, archive_name)
                                    added_count += 1
                            except Exception as img_err:
                                print(f"Erro ao converter imagem {file_path}: {img_err}")
                                continue

                        elif ext == '.pdf':
                            # Converte PDF para TIFF Multipage
                            try:
                                # Convert pages to images
                                poppler_path = os.environ.get('POPPLER_PATH', '/usr/bin')
                                # Windows fallback (if testing locally without docker Env set)
                                if os.name == 'nt' and not os.path.exists(poppler_path):
                                     poppler_path = None # Rely on PATH
                                
                                images = convert_from_path(file_path, dpi=200, poppler_path=poppler_path)
                                
                                if images:
                                    temp_tiff_path = os.path.join(temp_dir, f"{safe_reg_num}.tif")
                                    # Save as Multipage TIFF
                                    images[0].save(
                                        temp_tiff_path, 
                                        save_all=True, 
                                        append_images=images[1:], 
                                        compression="tiff_deflate"
                                    )
                                    
                                    zf.write(temp_tiff_path, archive_name)
                                    added_count += 1
                            except Exception as conv_err:
                                print(f"Erro ao converter {file_path}: {conv_err}")
                                # Se falhar conversão, talvez adicionar o original com sufixo _error?
                                # Por enquanto, ignoramos ou logamos.
                                continue

                # Metadata
                info = {
                    "generated_at": datetime.now().isoformat(),
                    "total_files": added_count,
                    "tenant": tenant_schema,
                    "format_converted": "tiff-multipage"
                }
                zf.writestr("export_info.json", json.dumps(info, indent=2))

            memory_file.seek(0)
            return memory_file, None
            
        except Exception as e:
            print(f"Error generating ZIP: {e}")
            return None, str(e)
        finally:
            conn.close()
