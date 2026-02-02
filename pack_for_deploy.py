import zipfile
import os

def create_deploy_zip():
    exclude_dirs = {'venv', '.git', '__pycache__', '.idea', '.vscode'}
    exclude_files = {'deploy.zip', '.env', 'start_local.bat', 'debug_start.py', 'pack_for_deploy.py'}
    
    zip_filename = 'deploy.zip'
    
    print(f"Creating {zip_filename}...")
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk('.'):
            # Modify dirs in-place to skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file in exclude_files or file.endswith('.pyc'):
                    continue
                
                file_path = os.path.join(root, file)
                # Archive name should be relative to project root
                arcname = os.path.relpath(file_path, '.')
                
                print(f"Adding {arcname}")
                zipf.write(file_path, arcname)
                
    print(f"\nSuccessfully created {zip_filename}!")

if __name__ == '__main__':
    create_deploy_zip()
