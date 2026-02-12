
import re
import os

def collapse_getters(file_path):
    if not os.path.exists(file_path):
        return
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Match {{ _('...') }} or {{ _("...") }} with potential newlines
    # We want to catch the whole {{ ... }} block and make it one line.
    
    pattern = r'\{\{\s*_\(\s*([\'"])(.*?)\1\s*\)\s*\}\}'
    
    def replacer(match):
        quote = match.group(1)
        inner = match.group(2)
        # Collapse internal whitespace in the translation KEY if it was multiline
        # But wait, the KEY must match the PO file exactly. 
        # If I change the key here, I must update the PO.
        clean_inner = " ".join(inner.split())
        return f"{{{{ _('{clean_inner}') }}}}"

    new_content = re.sub(pattern, replacer, content, flags=re.DOTALL)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"Collapsed getters in {file_path}")

files = [
    r'app/templates/dashboard/index.html',
    r'app/templates/dashboard/_finance.html',
    r'app/templates/dashboard/_production.html',
    r'app/templates/dashboard/_sales.html',
    r'app/templates/dashboard/_sdr.html',
    r'app/templates/clients/edit.html'
]

for f in files:
    collapse_getters(f)
