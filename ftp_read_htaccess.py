import ftplib

FTP_HOST = "ftp.puretego.online"
FTP_USER = "puretego"
FTP_PASS = "Kn16Nt]wB3O:3k"
TARGET_DIR = "gbpcheck.puretego.online"

def read_htaccess():
    try:
        ftp = ftplib.FTP(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)
        
        # Navigate
        files = ftp.nlst()
        if TARGET_DIR in files:
            ftp.cwd(TARGET_DIR)
        elif 'public_html' in files:
             ftp.cwd('public_html')
             if TARGET_DIR in ftp.nlst():
                 ftp.cwd(TARGET_DIR)
        
        print(f"CWD: {ftp.pwd()}")
        
        print("Reading .htaccess...")
        lines = []
        try:
            ftp.retrlines("RETR .htaccess", lines.append)
            print("\n".join(lines))
        except ftplib.error_perm as e:
            print(f"Permission error or file missing: {e}")

        ftp.quit()
    except Exception as e:
        print(f"FTP Error: {e}")

if __name__ == "__main__":
    read_htaccess()
