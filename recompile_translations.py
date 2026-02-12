
import os
import sys
import subprocess

def recompile():
    print("--- Fixing Translations on Server ---")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to translations folder
    trans_dir = os.path.join(base_dir, 'app', 'translations')
    
    if not os.path.isdir(trans_dir):
        print(f"ERROR: Directory not found: {trans_dir}")
        return
        
    print(f"Target Directory: {trans_dir} (Absolute)")
    
    # Run pybabel compile
    # We use sys.executable to use the current python env
    cmd = [sys.executable, '-m', 'babel.messages.frontend', 'compile', '-d', trans_dir]
    
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        # Capture output to show user
        res = subprocess.run(cmd, capture_output=True, text=True)
        print("\n--- Command Output ---")
        print(res.stdout)
        if res.stderr:
            print("\n--- Errors/Warnings ---")
            print(res.stderr)
            
        if res.returncode == 0:
            print("\nSUCCESS: Translations compiled.")
            print("Please restart the application now (touch tmp/restart.txt or use cPanel).")
        else:
            print(f"\nFAILED: Compile exited with code {res.returncode}")
            
    except Exception as e:
        print(f"\nEXCEPTION: {e}")

if __name__ == "__main__":
    recompile()
