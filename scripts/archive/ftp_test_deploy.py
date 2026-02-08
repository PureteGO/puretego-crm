import ftplib
import os

FTP_HOST = "ftp.puretego.online"
FTP_USER = "puretego"
FTP_PASS = "Kn16Nt]wB3O:3k"
TARGET_DIR = "gbpcheck.puretego.online"
LOCAL_FILE = "passenger_wsgi_hello.py"
REMOTE_FILE = "passenger_wsgi.py"

def deploy():
    try:
        print(f"Connecting to {FTP_HOST}...")
        ftp = ftplib.FTP(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)
        print("Logged in.")
        
        # Navigate to target directory
        files = ftp.nlst()
        if TARGET_DIR in files:
            ftp.cwd(TARGET_DIR)
        elif 'public_html' in files:
             ftp.cwd('public_html')
             if TARGET_DIR in ftp.nlst():
                 ftp.cwd(TARGET_DIR)
        
        print(f"Current Dir: {ftp.pwd()}")
        
        # Upload file (rename to passenger_wsgi.py on target)
        if os.path.exists("htaccess_disable.txt"):
             print("Uploading disabled .htaccess...")
             with open("htaccess_disable.txt", "rb") as file:
                 ftp.storbinary("STOR .htaccess", file)
             print("Upload .htaccess successful!")
        
        if os.path.exists(LOCAL_FILE):
            print(f"Uploading {LOCAL_FILE} as {REMOTE_FILE}...")
            with open(LOCAL_FILE, "rb") as file:
                ftp.storbinary(f"STOR {REMOTE_FILE}", file)
            print("Upload passenges_wsgi successful!")

        if os.path.exists("static_check.txt"):
             # Ensure public dir exists
            if 'public' not in ftp.nlst():
                ftp.mkd('public')
            
            print("Uploading static_check.txt to public/...")
            with open("static_check.txt", "rb") as file:
                ftp.storbinary("STOR public/static_check.txt", file)
            print("Upload static successful!")
        
        # Touch tmp/restart.txt to trigger reload            
            # Touch tmp/restart.txt to trigger reload
            print("Triggering restart...")
            try:
                if 'tmp' not in ftp.nlst():
                    ftp.mkd('tmp')
                
                with open("temp_restart.txt", "w") as f:
                    f.write("restart")
                
                with open("temp_restart.txt", "rb") as f:
                    ftp.storbinary("STOR tmp/restart.txt", f)
                
                os.remove("temp_restart.txt")
                print("Restart triggered.")
            except Exception as e:
                print(f"Failed to trigger restart: {e}")

        else:
            print(f"Local file {LOCAL_FILE} missing.")
            
        ftp.quit()
    except Exception as e:
        print(f"FTP Error: {e}")

if __name__ == "__main__":
    deploy()
