import ftplib
import logging

logging.basicConfig(level=logging.INFO)

FTP_HOST = "ftp.puretego.online"
FTP_USER = "puretego"
FTP_PASS = "Kn16Nt]wB3O:3k"
TARGET_DIR = "gbpcheck.puretego.online"
REMOTE_FILE = "passenger_wsgi.py"

def debug_perms():
    try:
        ftp = ftplib.FTP(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)
        logging.info("Logged in.")
        
        # Navigate
        files = ftp.nlst()
        if TARGET_DIR in files:
            ftp.cwd(TARGET_DIR)
        elif 'public_html' in files:
             ftp.cwd('public_html')
             if TARGET_DIR in ftp.nlst():
                 ftp.cwd(TARGET_DIR)
        
        logging.info(f"CWD: {ftp.pwd()}")
        
        # List detailed directory listing
        logging.info("Directory Listing:")
        ftp.retrlines('LIST')
        
        # Attempt CHMOD
        try:
            logging.info(f"Attempting CHMOD 644 {REMOTE_FILE}")
            resp = ftp.sendcmd(f"SITE CHMOD 644 {REMOTE_FILE}")
            logging.info(f"CHMOD Result: {resp}")
        except Exception as e:
            logging.error(f"CHMOD Failed: {e}")
            
        ftp.quit()
    except Exception as e:
        logging.error(f"FTP Error: {e}")

if __name__ == "__main__":
    debug_perms()
