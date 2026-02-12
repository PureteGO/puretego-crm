
import os
import re

def parse_po_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    entries = []
    current_entry = {}
    
    # Simple parser: active entries and commented entries
    # We want to map msgid -> msgstr for commented entries (#~)
    
    # Regex for msgid/msgstr
    # Handles multi-line strings roughly
    
    commented_translations = {}
    
    # First pass: Extract commented translations
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('#~ msgid "'):
            msgid = line[10:-1]
            # Check for multi-line msgid? usually localized tools put them on one line or standard format
            # Let's assume oneliner for now or simplistic
            i += 1
            if i < len(lines) and lines[i].strip().startswith('#~ msgstr "'):
                msgstr = lines[i].strip()[11:-1]
                if msgid and msgstr:
                    commented_translations[msgid] = msgstr
        i += 1
        
    return commented_translations

def update_po_file(filepath, recovered_map, manual_map=None):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    new_lines = []
    i = 0
    updated_count = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check for active msgid
        if line.strip().startswith('msgid "'):
            current_msgid = line.strip()[7:-1]
            
            # Check if next line is msgstr ""
            if i + 1 < len(lines) and lines[i+1].strip() == 'msgstr ""':
                # Found empty translation
                translation = None
                
                # Check manual map first (priority)
                if manual_map and current_msgid in manual_map:
                    translation = manual_map[current_msgid]
                # Check recovered map
                elif current_msgid in recovered_map:
                    translation = recovered_map[current_msgid]
                
                if translation:
                    new_lines.append(line) # msgid ...
                    new_lines.append(f'msgstr "{translation}"\n')
                    i += 2
                    updated_count += 1
                    continue
        
        new_lines.append(line)
        i += 1
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
        
    print(f"Updated {filepath}: {updated_count} translations recovered/added.")

# Manual Dictionaries
manual_pt = {
    "New Visit": "Nova Visita",
    "New Call": "Nova Chamada",
    "You have overdue tasks": "Você tem tarefas atrasadas",
    "There are items that require your attention.": "Existem itens que requerem sua atenção.",
    "View Overdue Items": "Ver Itens Atrasados",
    "Quick Health Check (GMB)": "Raio-X Rápido (GBP)",
    "Enter the company name to perform an instant Google My Business analysis.": "Digite o nome da empresa para uma análise instantânea do Google Perfil da Empresa.",
    "Company name (e.g., AGR Equipamientos)...": "Nome da empresa (ex: AGR Equipamientos)...",
    "Verify Now": "Verificar Agora",
    "Agenda - Today": "Agenda - Hoje",
    "Next 7 Days": "Próximos 7 Dias",
    "NEW LEADS (7d)": "NOVOS LEADS (7d)",
    "NEW LEADS (15d)": "NOVOS LEADS (15d)",
    "Last 7 Days": "Últimos 7 Dias",
    "Last 15 Days": "Últimos 15 Dias",
    "CLOSED SALES": "VENDAS FECHADAS",
    "This Month": "Este Mês",
    "AVG TICKET": "TICKET MÉDIO",
    "Average Value Won": "Valor Médio Ganho",
    "Dashboard": "Painel",
    "Welcome, %(name)s!": "Bem-vindo, %(name)s!",
    "SaaS Admin": "Admin SaaS",
    "Clients": "Clientes",
    "Proposals": "Propostas",
    "Services & Packages": "Serviços & Pacotes",
    "Finance": "Finanças",
    "Users": "Usuários",
    "Total Proposals": "Total de Propostas",
    "Pending Contracts": "Contratos Pendentes",
    "Renewal Alerts (Next 30 Days)": "Alertas de Renovação (Próx 30 dias)",
    "Operational Task Queue (Pending)": "Fila de Tarefas (Pendentes)"
}

manual_es = {
    "New Visit": "Nueva Visita",
    "New Call": "Nueva Llamada",
    "You have overdue tasks": "Usted tiene tareas vencidas",
    "There are items that require your attention.": "Hay elementos que requieren su atención.",
    "View Overdue Items": "Ver Elementos Vencidos",
    "Quick Health Check (GMB)": "Diagnóstico Rápido (GBP)",
    "Enter the company name to perform an instant Google My Business analysis.": "Ingrese el nombre de la empresa para un análisis instantáneo de Google Perfil de Negocio.",
    "Company name (e.g., AGR Equipamientos)...": "Nombre de la empresa (ej: AGR Equipamientos)...",
    "Verify Now": "Verificar Ahora",
    "Agenda - Today": "Agenda - Hoy",
    "Next 7 Days": "Próximos 7 Días",
    "NEW LEADS (7d)": "NUEVOS LEADS (7d)",
    "NEW LEADS (15d)": "NUEVOS LEADS (15d)",
    "Last 7 Days": "Últimos 7 Días",
    "Last 15 Days": "Últimos 15 Días",
    "CLOSED SALES": "VENTAS CERRADAS",
    "This Month": "Este Mes",
    "AVG TICKET": "TICKET PROMEDIO",
    "Average Value Won": "Valor Promedio Ganado",
    "Dashboard": "Tablero",
    "Welcome, %(name)s!": "¡Bienvenido, %(name)s!",
    "SaaS Admin": "Admin SaaS",
    "Clients": "Clientes",
    "Proposals": "Propuestas",
    "Services & Packages": "Servicios y Paquetes",
    "Finance": "Finanzas",
    "Users": "Usuarios",
    "Total Proposals": "Total de Propuestas",
    "Pending Contracts": "Contratos Pendientes",
    "Renewal Alerts (Next 30 Days)": "Alertas de Renovación (Próx 30 días)",
    "Operational Task Queue (Pending)": "Cola de Tareas (Pendientes)"
}

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Process Portuguese (pt_BR)
    pt_path = os.path.join(base_dir, 'app', 'translations', 'pt_BR', 'LC_MESSAGES', 'messages.po')
    if os.path.exists(pt_path):
        print(f"Processing {pt_path}...")
        recovered = parse_po_file(pt_path)
        print(f"Found {len(recovered)} commented translations in pt_BR.")
        update_po_file(pt_path, recovered, manual_pt)
        
    # Process Spanish (es)
    es_path = os.path.join(base_dir, 'app', 'translations', 'es', 'LC_MESSAGES', 'messages.po')
    if os.path.exists(es_path):
        print(f"Processing {es_path}...")
        recovered = parse_po_file(es_path)
        print(f"Found {len(recovered)} commented translations in es.")
        update_po_file(es_path, recovered, manual_es)

if __name__ == "__main__":
    main()
