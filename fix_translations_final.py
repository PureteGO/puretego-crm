import os
import re

def fix_catalog_final(filepath, corrections):
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # We will use a more precise replacement logic
    # Find active msgid/msgstr blocks
    # Pattern: #: file... \n msgid "..." \n msgstr "..."
    
    parts = re.split(r'(\n\n)', content)
    updated_count = 0
    new_parts = []
    
    for part in parts:
        msgid_match = re.search(r'^msgid "(.*)"$', part, re.MULTILINE)
        if msgid_match:
            msgid = msgid_match.group(1)
            if msgid in corrections:
                # Replace the msgstr line
                new_part = re.sub(r'^msgstr ".*"$', f'msgstr "{corrections[msgid]}"', part, flags=re.MULTILINE)
                if new_part != part:
                    part = new_part
                    updated_count += 1
        new_parts.append(part)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("".join(new_parts))
    
    print(f"Updated {filepath}: {updated_count} corrections applied.")

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Comprehensive corrections map
    es_map = {
        "EDIT_CLIENT_HEADER": "Editar Cliente",
        "TAB_BASIC_INFORMATION": "Información Básica",
        "TAB_DETAILED_INFORMATION": "Información Detallada",
        "Business Information": "Información del Negocio",
        "Basic Information": "Información Básica",
        "Detailed Information": "Información Detallada",
        "Primary Contact": "Contacto Principal",
        "Client Limit": "Límite de Clientes",
        "Cliente Desconhecido": "Cliente Desconocido",
        "Business Name / Client": "Nombre del Negocio / Cliente",
        "Google Maps Name (GMB)": "Nombre en Google Maps (GMB)",
        "Phone / WhatsApp": "Teléfono / WhatsApp",
        "Back": "Volver",
        "NEW LEADS (7d)": "NUEVOS LEADS (7d)",
        "NEW LEADS (15d)": "NUEVOS LEADS (15d)",
        "CLOSED SALES": "VENTAS CERRADAS",
        "AVG TICKET": "TICKET PROMEDIO",
        "Awaiting Payment": "Pendiente de Pago",
        "Pending Contracts": "Contratos Pendientes",
        "Total Clients": "Total Clientes",
        "Total Proposals": "Total Propuestas",
        "Renewal Alerts (Next 30 Days)": "Alertas de Renovación (Próximos 30 Días)",
        "Operational Task Queue (Pending)": "Cola de Tareas Operativas (Pendientes)",
        "Recent Activity": "Actividade Reciente",
        "Latest Leads": "Últimos Leads",
        "Latest Interactions": "Últimas Interacciones",
        "Latest Visits": "Últimas Visitas",
        "Latest Health Checks": "Últimos Health Checks",
        "New Visit": "Nueva Visita",
        "New Call": "Nueva Llamada",
        "Quick Health Check (GMB)": "Chequeo Rápido de Salud (GMB)",
        "Verify Now": "Verificar Ahora",
        "Analyzing...": "Analizando...",
        "Company name (e.g., AGR Equipamientos)...": "Nombre de la empresa (p. ej., AGR Equipamientos)...",
        "Loading...": "Cargando...",
        "Log Interaction": "Registrar Interacción",
        "Edit Interaction": "Editar Interacción",
        "Type": "Tipo",
        "Manage Types": "Gestionar Tipos",
        "Date/Time": "Fecha/Hora",
        "Notes": "Notas",
        "Already done (mark as completed)": "Ya realizado (marcar como completado)",
        "Next Step Suggestion": "Sugerencia de Siguiente Paso",
        "Schedule": "Agendar",
        "No scheduling": "Sin agendamiento",
        "Manage Interaction Types": "Gestionar Tipos de Interacción",
        "New Type": "Nuevo Tipo",
        "Name (ex: Technical Visit)": "Nombre (ej: Visita Técnica)",
        "Is call": "Es una llamada",
        "Call": "Llamada",
        "Visit/Other": "Visita/Otro",
        "Delete this type?": "¿Eliminar este tipo?",
        "Edit Type": "Editar Tipo",
        "Name": "Nombre",
        "Icon": "Icono",
        "Type": "Tipo",
        "Actions": "Acciones",
        "Save": "Guardar",
        "Cancel": "Cancelar",
        "Contact and Decision Details": "Detalles de Contacto y Decisión",
        "Receptionist Name": "Nombre del Recepcionista",
        "Decision Maker Name": "Nombre del Tomador de Decisiones",
        "Decision Factors": "Factores de Decisión",
        "Funnel Start Date": "Fecha de Inicio del Embudo",
        "Date when the client entered the sales funnel.": "Fecha en que el cliente entró en el embudo de ventas.",
        "Best Contact Time": "Mejor Horário de Contacto",
        "Preferred Contact Method": "Método de Contacto Preferido",
        "In-person Visit": "Visita Presencial",
        "Additional Information / Observations": "Información Adicional / Observaciones",
        "Any other relevant detail...": "Cualquier otro detalle relevante...",
        "Who receives/answers first": "Quién recibe/responde primero",
        "Who signs the check": "Quién firma el cheque",
        "Ex: Tuesday afternoon": "Ej: Martes por la tarde",
        "Select...": "Seleccionar...",
        "CRM": "CRM",
        "Sales": "Ventas",
        "Attention: Follow-up required": "Atención: Seguimiento pendiente",
        "The following leads were worked on today but have no next step scheduled. Define a next step before the day ends to maintain the sales process.": "Los siguientes leads fueron atendidos hoy pero no tienen un próximo paso programado. Defina una acción antes del final del día para mantener el proceso de ventas.",
        "Back to Client": "Volver al Cliente"
    }
    
    en_map = {
        "EDIT_CLIENT_HEADER": "Edit Client",
        "TAB_BASIC_INFORMATION": "Basic Information",
        "TAB_DETAILED_INFORMATION": "Detailed Information",
        "Business Information": "Business Information",
        "Basic Information": "Basic Information",
        "Detailed Information": "Detailed Information",
        "Primary Contact": "Primary Contact",
        "Client Limit": "Client Limit",
        "Cliente Desconhecido": "Unknown Client",
        "Business Name / Client": "Business Name / Client",
        "Google Maps Name (GMB)": "Google Maps Name (GMB)",
        "Phone / WhatsApp": "Phone / WhatsApp",
        "Back": "Back",
        "NEW LEADS (7d)": "NEW LEADS (7d)",
        "NEW LEADS (15d)": "NEW LEADS (15d)",
        "CLOSED SALES": "CLOSED SALES",
        "AVG TICKET": "AVG TICKET",
        "Awaiting Payment": "Awaiting Payment",
        "Pending Contracts": "Pending Contracts",
        "Total Clients": "Total Clients",
        "Total Proposals": "Total Proposals",
        "Renewal Alerts (Next 30 Days)": "Renewal Alerts (Next 30 Days)",
        "Operational Task Queue (Pending)": "Operational Task Queue (Pending)",
        "Recent Activity": "Recent Activity",
        "Latest Leads": "Latest Leads",
        "Latest Interactions": "Latest Interactions",
        "Latest Visits": "Latest Visits",
        "Latest Health Checks": "Latest Health Checks",
        "New Visit": "New Visit",
        "New Call": "New Call",
        "Quick Health Check (GMB)": "Quick Health Check (GMB)",
        "Verify Now": "Verify Now",
        "Analyzing...": "Analyzing...",
        "Company name (e.g., AGR Equipamientos)...": "Company name (e.g., AGR Equipamientos)...",
        "Loading...": "Loading...",
        "Log Interaction": "Log Interaction",
        "Edit Interaction": "Edit Interaction",
        "Type": "Type",
        "Manage Types": "Manage Types",
        "Date/Time": "Date/Time",
        "Notes": "Notes",
        "Already done (mark as completed)": "Already done (mark as completed)",
        "Next Step Suggestion": "Next Step Suggestion",
        "Schedule": "Schedule",
        "No scheduling": "No scheduling",
        "Manage Interaction Types": "Manage Interaction Types",
        "New Type": "New Type",
        "Name (ex: Technical Visit)": "Name (ex: Technical Visit)",
        "Is call": "Is call",
        "Call": "Call",
        "Visit/Other": "Visit/Other",
        "Delete this type?": "Delete this type?",
        "Edit Type": "Edit Type",
        "Name": "Name",
        "Icon": "Icon",
        "Type": "Type",
        "Actions": "Actions",
        "Save": "Save",
        "Cancel": "Cancel",
        "Contact and Decision Details": "Contact and Decision Details",
        "Receptionist Name": "Receptionist Name",
        "Decision Maker Name": "Decision Maker Name",
        "Decision Factors": "Decision Factors",
        "Funnel Start Date": "Funnel Start Date",
        "Date when the client entered the sales funnel.": "Date when the client entered the sales funnel.",
        "Best Contact Time": "Best Contact Time",
        "Preferred Contact Method": "Preferred Contact Method",
        "In-person Visit": "In-person Visit",
        "Additional Information / Observations": "Additional Information / Observations",
        "Any other relevant detail...": "Any other relevant detail...",
        "Who receives/answers first": "Who receives/answers first",
        "Who signs the check": "Who signs the check",
        "Ex: Tuesday afternoon": "Ex: Tuesday afternoon",
        "Select...": "Select...",
        "CRM": "CRM",
        "Sales": "Sales",
        "Attention: Follow-up required": "Attention: Follow-up required",
        "The following leads were worked on today but have no next step scheduled. Define a next step before the day ends to maintain the sales process.": "The following leads were worked on today but have no next step scheduled. Define a next step before the day ends to maintain the sales process.",
        "Back to Client": "Back to Client"
    }
    
    pt_map = {
        "Log Interaction": "Registrar Interação",
        "Edit Interaction": "Editar Interação",
        "Type": "Tipo",
        "Manage Types": "Gerenciar Tipos",
        "Date/Time": "Data/Hora",
        "Notes": "Observações",
        "Already done (mark as completed)": "Já realizado (marcar como concluído)",
        "Next Step Suggestion": "Sugestão de Próximo Passo",
        "Schedule": "Agendar",
        "No scheduling": "Não agendar",
        "Manage Interaction Types": "Gerenciar Tipos de Interação",
        "New Type": "Novo Tipo",
        "Name (ex: Technical Visit)": "Nome (ex: Visita Técnica)",
        "Is call": "É uma chamada",
        "Call": "Chamada",
        "Visit/Other": "Visita/Outro",
        "Delete this type?": "Excluir este tipo?",
        "Edit Type": "Editar Tipo",
        "Name": "Nome",
        "Icon": "Ícone",
        "Type": "Tipo",
        "Actions": "Ações",
        "Save": "Salvar",
        "Cancel": "Cancelar",
        "Contact and Decision Details": "Detalhes de Contato e Decisão",
        "Receptionist Name": "Nome da Recepcionista",
        "Decision Maker Name": "Nome do Tomador de Decisão",
        "Decision Factors": "Fatores de Decisão",
        "Funnel Start Date": "Data de Início no Funil",
        "Date when the client entered the sales funnel.": "Data em que o cliente entrou no funil de vendas.",
        "Best Contact Time": "Melhor Horário de Contato",
        "Preferred Contact Method": "Método de Contato Preferido",
        "In-person Visit": "Visita Presencial",
        "Additional Information / Observations": "Informações Adicionais / Observações",
        "Any other relevant detail...": "Qualquer outro detalhe relevante...",
        "Who receives/answers first": "Quem recebe/responde primeiro",
        "Who signs the check": "Quem assina o cheque",
        "Ex: Tuesday afternoon": "Ex: Terça à tarde",
        "Select...": "Selecionar...",
        "CRM": "CRM",
        "Sales": "Vendas",
        "Attention: Follow-up required": "Atenção: Seguimento pendente",
        "The following leads were worked on today but have no next step scheduled. Define a next step before the day ends to maintain the sales process.": "Os seguintes leads foram atendidos hoje, mas não possuem um próximo passo agendado. Defina uma ação antes do fim do dia para manter o processo de vendas.",
        "Back to Client": "Voltar para o Cliente"
    }

    es_path = os.path.join(base_dir, 'app', 'translations', 'es', 'LC_MESSAGES', 'messages.po')
    en_path = os.path.join(base_dir, 'app', 'translations', 'en', 'LC_MESSAGES', 'messages.po')
    pt_path = os.path.join(base_dir, 'app', 'translations', 'pt_BR', 'LC_MESSAGES', 'messages.po')
    
    fix_catalog_final(es_path, es_map)
    fix_catalog_final(en_path, en_map)
    fix_catalog_final(pt_path, pt_map)

if __name__ == "__main__":
    main()
