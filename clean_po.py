
import re
import os

def clean_po(file_path):
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Remove all #, fuzzy lines
    content = re.sub(r'^#,\s*fuzzy.*\n', '', content, flags=re.MULTILINE)
    
    # 2. Remove all obsolete entries (#~ msgid ...)
    content = re.sub(r'^#~.*\n', '', content, flags=re.MULTILINE)
    
    # 3. Fix trailing spaces in msgid and msgstr
    content = re.sub(r'msgid "([^"]+)"\s+\n', r'msgid "\1"\n', content)
    content = re.sub(r'msgstr "([^"]*)"\s+\n', r'msgstr "\1"\n', content)

    # 4. Custom fixes for the Dashboard and Client Edit
    # Ensure "Awaiting Payment" has no trailing spaces in index
    content = content.replace('msgid "Awaiting Payment" ', 'msgid "Awaiting Payment"')
    content = content.replace('msgid "Total Clients" ', 'msgid "Total Clients"')
    
    # Fix specific bad translations I saw in previous views
    content = content.replace('msgstr "Por favor aguarde enquanto consultamos o Google."', 'msgstr "Aguardando Pagamento"')
    # Wait, I should find the entry for Total Proposals and fix it too
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Refined cleanup for {file_path}")

clean_po(r'app/translations/pt_BR/LC_MESSAGES/messages.po')
clean_po(r'app/translations/es/LC_MESSAGES/messages.po')
