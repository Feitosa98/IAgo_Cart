import os
import zipfile
from datetime import datetime

def versionar_projeto():
    # Define excluded folders/extensions
    EXCLUDE_DIRS = {
        '__pycache__', 
        'backups', 
        'venv', 
        '.git', 
        '.idea', 
        '__MACOSX'
    }
    EXCLUDE_EXTENSIONS = {
        '.pyc', 
        '.log', 
        '.zip',
        '.db-journal' # Don't back up journal files usually
    }
    
    # Define files to verify (ensure we are in root)
    REQUIRED = ['imoveis_web.py', 'templates', 'static']
    
    cwd = os.getcwd()
    if not all(os.path.exists(f) for f in REQUIRED):
        print("Erro: Não parece ser a raiz do projeto. Faltando imoveis_web.py ou pastas.")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    version_name = f"release_v1.0_{timestamp}.zip"
    
    # Create versions folder if not exists
    if not os.path.exists("versoes"):
        os.makedirs("versoes")
        
    zip_path = os.path.join("versoes", version_name)
    
    print(f"Criando versão: {zip_path}...")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(cwd):
            # Edit dirs in-place to skip excluded
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            
            # Skip the versions folder itself!
            if "versoes" in root:
                continue
                
            for file in files:
                if any(file.endswith(ext) for ext in EXCLUDE_EXTENSIONS):
                    continue
                
                # Check specifics
                # Skip existing zips if they are in root
                if file.endswith('.zip'):
                    continue

                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, cwd)
                
                # Add to zip
                print(f"  + Adicionando: {rel_path}")
                zipf.write(abs_path, rel_path)
                
    print("\n" + "="*40)
    print(f"SUCESSO! Versão criada em: {zip_path}")
    print("="*40)

if __name__ == "__main__":
    versionar_projeto()
