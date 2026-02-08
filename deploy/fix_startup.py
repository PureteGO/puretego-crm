
import os

target = "app/__init__.py"
if os.path.exists(target):
    with open(target, "r") as f:
        lines = f.readlines()
    
    new_lines = []
    for line in lines:
        if "flask_migrate" in line:
            continue
        if "Migrate(app" in line:
            continue
        new_lines.append(line)
        
    with open(target, "w") as f:
        f.write("".join(new_lines))
    print("Fixed app/__init__.py")
else:
    print(f"File {target} not found")
