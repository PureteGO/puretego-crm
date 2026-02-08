import zipfile
import os
from datetime import datetime

def create_backup():
    # Setup paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = os.path.join(project_root, f"FULL_BACKUP_PRE_REFACTOR_{timestamp}.zip")
    
    print(f"Iniciando backup em: {zip_filename}")
    print(f"Raiz do projeto: {project_root}")
    
    # Exclusions
    exclude_dirs = {'.git', 'venv', '__pycache__', 'tmp', '.idea', '.vscode'}
    exclude_extensions = {'.zip', '.pyc', '.pyo', '.pyd'}
    
    count = 0
    try:
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(project_root):
                # Filter directories in-place
                dirs[:] = [d for d in dirs if d not in exclude_dirs]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Exclude extensions
                    _, ext = os.path.splitext(file)
                    if ext.lower() in exclude_extensions:
                        continue
                        
                    # Calculate arcname (relative path inside zip)
                    arcname = os.path.relpath(file_path, project_root)
                    
                    # Avoid backing up the backup script itself if running from root, or connection files if needed
                    # But mainly avoid putting the new zip inside itself (handled by .zip exclusion)
                    
                    # Create entry
                    try:
                        zipf.write(file_path, arcname)
                        count += 1
                    except PermissionError:
                        print(f"Atenção: Permissão negada ao acessar {file_path}. Pulando.")
                    except Exception as e:
                        print(f"Erro ao adicionar {file_path}: {e}")

        print(f"Backup concluído com sucesso!")
        print(f"Total de arquivos: {count}")
        print(f"Arquivo gerado: {zip_filename}")
        
    except Exception as e:
        print(f"CRITICAL ERROR: Falha ao criar backup: {e}")

if __name__ == "__main__":
    create_backup()
