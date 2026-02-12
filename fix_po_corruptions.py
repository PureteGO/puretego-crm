import os

def fix_po_corruption(filepath, corrections):
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    i = 0
    updated_count = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check for msgid
        if line.strip().startswith('msgid "'):
            msgid = line.strip()[7:-1]
            
            # Check if this msgid is in our corrections
            if msgid in corrections:
                new_lines.append(line)
                # Next line should be msgstr
                if i + 1 < len(lines) and lines[i+1].strip().startswith('msgstr '):
                    new_lines.append(f'msgstr "{corrections[msgid]}"\n')
                    i += 2
                    updated_count += 1
                    continue
        
        new_lines.append(line)
        i += 1

    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"Updated {filepath}: {updated_count} corrections applied.")

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Correct values based on PT reference and common sense
    corrections = {
        "EDIT_CLIENT_HEADER": "Editar Cliente",
        "TAB_BASIC_INFORMATION": "Informação Básica",
        "TAB_DETAILED_INFORMATION": "Informação Detalhada"
    }
    
    # Spanish Corrections
    es_corrections = {
        "EDIT_CLIENT_HEADER": "Editar Cliente",
        "TAB_BASIC_INFORMATION": "Información Básica",
        "TAB_DETAILED_INFORMATION": "Información Detallada"
    }
    
    # English Corrections
    en_corrections = {
        "EDIT_CLIENT_HEADER": "Edit Client",
        "TAB_BASIC_INFORMATION": "Basic Information",
        "TAB_DETAILED_INFORMATION": "Detailed Information"
    }

    es_path = os.path.join(base_dir, 'app', 'translations', 'es', 'LC_MESSAGES', 'messages.po')
    en_path = os.path.join(base_dir, 'app', 'translations', 'en', 'LC_MESSAGES', 'messages.po')
    
    fix_po_corruption(es_path, es_corrections)
    fix_po_corruption(en_path, en_corrections)

if __name__ == "__main__":
    main()
