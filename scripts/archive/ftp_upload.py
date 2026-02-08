import ftplib
import os

FTP_HOST = "ftp.puretego.online"
FTP_USER = "puretego"
FTP_PASS = "Kn16Nt]wB3O:3k"
TARGET_DIR = "gbpcheck.puretego.online" # Relative to home if main account

def upload_zip():
    try:
        ftp = ftplib.FTP(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)
        print(f"Connected to {FTP_HOST}")
        
        # List files to check path
        files = ftp.nlst()
        if TARGET_DIR in files:
            print(f"Found target dir: {TARGET_DIR}")
            ftp.cwd(TARGET_DIR)
        else:
            print(f"Target dir {TARGET_DIR} not found in root. Listing root:")
            print(files)
            # Try public_html just in case
            if 'public_html' in files:
                ftp.cwd('public_html')
                if TARGET_DIR in ftp.nlst():
                    ftp.cwd(TARGET_DIR)
                    print(f"Found in public_html/{TARGET_DIR}")
        
        # Upload deploy.zip
        filename = "deploy.zip"
        if os.path.exists(filename):
            print(f"Uploading {filename}...")
            with open(filename, "rb") as file:
                ftp.storbinary(f"STOR {filename}", file)
            print("Upload successful!")
        else:
            print("deploy.zip not found locally.")
            
        ftp.quit()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    upload_zip()
