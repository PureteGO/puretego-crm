import os
import re

def parse_po_active(filepath):
    """Parses active translations (not commented out)."""
    if not os.path.exists(filepath):
        return {}
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Simple regex for msgid/msgstr pairs
    # msgid "..."
    # msgstr "..."
    pattern = re.compile(r'^msgid "(.*)"\nmsgstr "(.*)"', re.MULTILINE)
    return {m.group(1): m.group(2) for m in pattern.finditer(content)}

def fix_catalog_massively(filepath, reference_map, language):
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    i = 0
    updated_count = 0
    
    # Generic translation map for common keys if we don't have a specific word
    # Mostly to fix keys like TAB_... EDIT_...
    key_translations = {
        'es': {
            'TAB_BASIC_INFORMATION': 'Información Básica',
            'TAB_DETAILED_INFORMATION': 'Información Detallada',
            'EDIT_CLIENT_HEADER': 'Editar Cliente',
            'NEW_LEADS_7D': 'NUEVOS LEADS (7d)',
            'NEW_LEADS_15D': 'NUEVOS LEADS (15d)',
            'CLOSED_SALES': 'VENTAS CERRADAS',
            'AVG_TICKET': 'TICKET PROMEDIO',
            'QUICK_HEALTH_CHECK': 'Chequeo Rápido de Salud',
            'NEW_VISIT': 'Nueva Visita',
            'NEW_CALL': 'Nueva Llamada'
        },
        'en': {
            'TAB_BASIC_INFORMATION': 'Basic Information',
            'TAB_DETAILED_INFORMATION': 'Detailed Information',
            'EDIT_CLIENT_HEADER': 'Edit Client',
            'NEW_LEADS_7D': 'NEW LEADS (7d)',
            'NEW_LEADS_15D': 'NEW LEADS (15d)',
            'CLOSED_SALES': 'CLOSED SALES',
            'AVG_TICKET': 'AVG TICKET',
            'QUICK_HEALTH_CHECK': 'Quick Health Check',
            'NEW_VISIT': 'New Visit',
            'NEW_CALL': 'New Call'
        }
    }

    # Suspect pattern in Spanish: "Cliente eliminado correctamente"
    bad_pattern_es = "Cliente eliminado correctamente"

    while i < len(lines):
        line = lines[i]
        
        if line.strip().startswith('msgid "'):
            msgid = line.strip()[7:-1]
            
            # Check if next line is msgstr
            if i + 1 < len(lines) and lines[i+1].strip().startswith('msgstr '):
                msgstr = lines[i+1].strip()[8:-1]
                
                needs_fix = False
                new_val = None
                
                # Rule 1: Key-based override
                if msgid in key_translations.get(language, {}):
                    needs_fix = True
                    new_val = key_translations[language][msgid]
                
                # Rule 2: Suspect Spanish corruption
                elif language == 'es' and msgstr == bad_pattern_es:
                    # Is the msgid actually about deletion?
                    if not any(word in msgid.lower() for word in ['delete', 'remove', 'eliminado']):
                        # It's likely corrupted. Try to find a better one.
                        # For now, if it's a key, we might use generic logic
                        # or just leave it for now if we don't have a replacement.
                        # But standard dashboard keys are fixed in Rule 1.
                        pass
                
                # Rule 3: Empty string for a known translated key in PT
                elif msgstr == "" and msgid in reference_map:
                    # If it's a KEY style, we can at least use Rule 1 logic or Key name
                    if "_" in msgid and msgid.isupper():
                        if msgid in key_translations.get(language, {}):
                            needs_fix = True
                            new_val = key_translations[language][msgid]

                if needs_fix and new_val:
                    new_lines.append(line)
                    new_lines.append(f'msgstr "{new_val}"\n')
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
    pt_path = os.path.join(base_dir, 'app', 'translations', 'pt_BR', 'LC_MESSAGES', 'messages.po')
    es_path = os.path.join(base_dir, 'app', 'translations', 'es', 'LC_MESSAGES', 'messages.po')
    en_path = os.path.join(base_dir, 'app', 'translations', 'en', 'LC_MESSAGES', 'messages.po')
    
    pt_map = parse_po_active(pt_path)
    print(f"Loaded {len(pt_map)} active translations from pt_BR.")
    
    fix_catalog_massively(es_path, pt_map, 'es')
    fix_catalog_massively(en_path, pt_map, 'en')

if __name__ == "__main__":
    main()
