import re
import os

files_to_fix = [
    r'c:\ProAG\puretego-crm\app\translations\pt_BR\LC_MESSAGES\messages.po',
    r'c:\ProAG\puretego-crm\app\translations\pt\LC_MESSAGES\messages.po'
]

replacements = {
    'msgid "Login"\nmsgstr "Opcional"': 'msgid "Login"\nmsgstr "Login"',
    'msgid "Log In"\nmsgstr "Nova Visita"': 'msgid "Log In"\nmsgstr "Entrar"',
    'msgid "Forgot your password?"\nmsgstr ""': 'msgid "Forgot your password?"\nmsgstr "Esqueceu a senha?"',
    'msgid "New Stage"\nmsgstr "Nova Visita"': 'msgid "New Stage"\nmsgstr "Nova Etapa"',
    'msgid "Log Visit"\nmsgstr "Nova Visita"': 'msgid "Log Visit"\nmsgstr "Registrar Visita"',
    'msgid "Package"\nmsgstr "Nova Visita"': 'msgid "Package"\nmsgstr "Pacote"',
    'msgid "Edit Visit"\nmsgstr "Nova Visita"': 'msgid "Edit Visit"\nmsgstr "Editar Visita"',
    'msgid "On-site Visit"\nmsgstr "Nova Visita"': 'msgid "On-site Visit"\nmsgstr "Visita Presencial"',
}

for filepath in files_to_fix:
    if not os.path.exists(filepath):
        continue
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for old, new in replacements.items():
        content = content.replace(old, new)
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print("Done fixing translations.")
