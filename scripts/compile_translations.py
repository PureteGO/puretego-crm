
import sys
import os
import subprocess

# Add project root to path
sys.path.append(os.getcwd())

def compile_translations():
    print("Compiling translations...")
    try:
        # Assuming venv is used
        python_exe = os.path.join("venv", "Scripts", "python.exe")
        if not os.path.exists(python_exe):
            python_exe = "python" # Fallback
            
        cmd = [python_exe, "-m", "pybabel", "compile", "-d", "app/translations"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("SUCCESS: Translations compiled.")
            print(result.stdout)
        else:
            print("ERROR compiling translations:")
            print(result.stderr)
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    compile_translations()
