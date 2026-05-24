import subprocess
subprocess.run(['ssh-keygen', '-t', 'rsa', '-b', '2048', '-f', 'id_rsa_cyberpanel', '-N', ''], check=True)
with open('id_rsa_cyberpanel.pub', 'r') as f:
    print(f.read())
