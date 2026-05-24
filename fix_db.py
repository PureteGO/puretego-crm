import os
import subprocess

input_file = "app2maps2go_crm.sql"
output_file = "app2maps2go_crm_fixed.sql"

# Remove the sandbox mode line
with open(input_file, "r", encoding="utf-8") as f_in, open(output_file, "w", encoding="utf-8") as f_out:
    first_line = True
    for line in f_in:
        if first_line and "sandbox mode" in line:
            first_line = False
            continue
        first_line = False
        f_out.write(line)

print("File fixed. Starting import...")

# Run mysql import
cmd = r'C:\xampp\mysql\bin\mysql.exe -h127.0.0.1 -P3306 -uroot puretego_crm < app2maps2go_crm_fixed.sql'
result = subprocess.run(cmd, shell=True, check=True)
print("Import complete.")
