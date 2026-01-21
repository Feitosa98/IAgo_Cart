import os
import zipfile
import io
import json
import tempfile
import math
from datetime import datetime
from db_manager import get_compat_conn
from pdf2image import convert_from_path
from PIL import Image

class ExportService:
    @staticmethod
    def generate_organized_zip(tenant_schema, user_id=None):
        """
        Gera ZIP no padrão estrito 'ConversorPro':
        - Formato: TIFF Single Page, 200 DPI.
        - Pastas: Blocos de 500 (1 a 499, 500 a 999...).
        - Arquivos: {NumReg:08d}_{Folha:05d}{Face}.tif
            - Face 'f' (impar/frente), 'v' (par/verso).
        """
        
        conn = get_compat_conn()
        cur = conn.cursor()
        
        try:
            cur.execute(f"SET search_path TO {tenant_schema}, public")
            
            # Busca apenas registros válidos numéricos para garantir a ordenação das pastas
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
                        raw_reg_num = row[0]
                        file_path = row[1]
                        
                        # Tenta extrair número inteiro do registro para cálculo de pasta
                        try:
                            # Remove caracteres não numéricos para achar o ID lógico
                            digits_only = "".join(filter(str.isdigit, str(raw_reg_num)))
                            reg_int = int(digits_only)
                        except ValueError:
                            # Se não for numérico (ex: "123A"), usa pasta "Outros" ou lógica fallback
                            # Mas o padrão exige numérico. Vamos tentar manter o original se falhar.
                            # Para o padrão ConversorPro funcionar, precisa ser numérico.
                            # Fallback: assume 0.
                            reg_int = 0

                        # Cálculo da Pasta (Bucket)
                        # Ex: 1 a 499 (0-499), 500 a 999
                        # bucket_start = (reg_int // 500) * 500
                        # bucket_end = bucket_start + 499
                        # O usuario pediu "1 a 499". Isso é curioso pois "0" ficaria de fora? 
                        # Geralmente TI começa 0 ou 1.
                        # Se reg=1 -> 1//500 = 0 -> 0 a 499.
                        # Se reg=500 -> 500//500=1 -> 500 a 999.
                        # Vamos ajustar para display:
                        bucket_index = (reg_int // 500)
                        folder_start = bucket_index * 500
                        folder_end = folder_start + 499
                        
                        # Ajuste cosmético pedido: "1 a 499" (se bucket 0)
                        if folder_start == 0: 
                            folder_name = f"1 a {folder_end}"
                        else:
                            folder_name = f"{folder_start} a {folder_end}"

                        if not file_path or not os.path.exists(file_path):
                            continue
                            
                        # Extrair Imagens (Páginas)
                        images = []
                        _, ext = os.path.splitext(file_path)
                        ext = ext.lower()

                        try:
                            if ext == '.pdf':
                                poppler_path = os.environ.get('POPPLER_PATH', '/usr/bin')
                                if os.name == 'nt' and not os.path.exists(poppler_path):
                                     poppler_path = None 
                                
                                images = convert_from_path(file_path, dpi=200, poppler_path=poppler_path)
                            
                            elif ext in ['.tif', '.tiff']:
                                # TIFF pode ser multipage
                                try:
                                    img = Image.open(file_path)
                                    # Iterate pages
                                    for i in range(img.n_frames):
                                        img.seek(i)
                                        images.append(img.copy())
                                except Exception as e:
                                    print(f"Erro lendo TIFF {file_path}: {e}")
                            
                            elif ext in ['.jpg', '.jpeg', '.png', '.bmp']:
                                with Image.open(file_path) as img:
                                    images.append(img.copy())
                        except Exception as e:
                            print(f"Erro abrindo arquivo {file_path}: {e}")
                            continue

                        # Salvar Pagina a Pagina no padrão
                        # {Registro:08d}_{Folha:05d}{Face}.tif
                        # P1 (i=0) -> Folha 00001 Frente (f)
                        # P2 (i=1) -> Folha 00001 Verso (v)
                        # P3 (i=2) -> Folha 00002 Frente (f)
                        
                        for i, img in enumerate(images):
                            # Converter para P&B (1-bit pixels, black and white) se desejado "preto-e-branco"
                            # ConversorPro geralmente usa 1 bit (mode '1') para economizar espaço em doc
                            if img.mode != '1':
                                img = img.convert('1', dither=Image.NONE)

                            # Definir Folha e Face
                            folha_seq = (i // 2) + 1
                            face = 'v' if (i % 2) != 0 else 'f' # 0=f, 1=v, 2=f...
                            
                            filename = f"{reg_int:08d}_{folha_seq:05d}{face}.tif"
                            archive_path = f"{folder_name}/{filename}"
                            
                            # Salvar em temp e adicionar ao ZIP
                            temp_tif = os.path.join(temp_dir, filename)
                            img.save(temp_tif, compression="tiff_deflate", dpi=(200, 200))
                            
                            zf.write(temp_tif, archive_path)
                            added_count += 1

                # Metadata
                info = {
                    "generated_at": datetime.now().isoformat(),
                    "total_pages_exported": added_count,
                    "standard": "ConversorPro V2 (Split Pages)",
                }
                zf.writestr("export_info.json", json.dumps(info, indent=2))

            memory_file.seek(0)
            return memory_file, None
            
        except Exception as e:
            print(f"Error generating ZIP: {e}")
            import traceback
            traceback.print_exc()
            return None, str(e)
        finally:
            conn.close()
