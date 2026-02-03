import ftplib
import os

FTP_HOST = "ftp.puretego.online"
FTP_USER = "puretego"
FTP_PASS = "Kn16Nt]wB3O:3k"
TARGET_DIR = "gbpcheck.puretego.online"

def rmtree(ftp, dir_path):
    print(f"Entering {dir_path}...")
    try:
        ftp.cwd(dir_path)
        names = ftp.nlst()
        for name in names:
            if name in ('.', '..'): continue
            
            # Try to navigate to see if it's a dir
            try:
                ftp.cwd(name)
                ftp.cwd('..')
                # It is a dir, recurse
                rmtree(ftp, name)
            except ftplib.error_perm:
                # It is a file, delete
                try:
                    ftp.delete(name)
                    # print(f"Deleted {name}")
                except Exception as e:
                    print(f"Failed to delete {name}: {e}")
        
        # Go back up and delete the now-empty dir
        ftp.cwd('..')
        ftp.rmd(dir_path)
        print(f"Removed directory {dir_path}")
    except Exception as e:
        print(f"Error removing {dir_path}: {e}")

def clean_server():
    try:
        ftp = ftplib.FTP(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)
        print(f"Connected to {FTP_HOST}")
        
        ftp.cwd(TARGET_DIR)
        print(f"In {TARGET_DIR}")
        
        files = ftp.nlst()
        
        # Delete specific files
        for f in ['passenger_wsgi.py', 'run.py', 'app.py', 'index.py']:
            if f in files:
                try:
                    ftp.delete(f)
                    print(f"Deleted {f}")
                except:
                    print(f"Could not delete {f}")
        
        # Delete app folder
        if 'app' in files:
            print("Removing 'app' folder (this may take a moment)...")
            rmtree(ftp, 'app')
        else:
            print("'app' folder not found (already clean?)")

        # Verify final state
        print("\nFinal file list:")
        print(ftp.nlst())
        
        ftp.quit()
        print("\nCleanup Complete!")
    except Exception as e:
        print(f"FTP Error: {e}")

if __name__ == "__main__":
    clean_server()
