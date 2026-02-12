
import re
import os

def repair_po_file(file_path, corrections):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split into entries (using double newlines as separator)
    entries = re.split(r'\n\n(?=#|msgid)', content)
    
    new_entries = []
    seen_ids = set()

    for entry in entries:
        # Extract msgid
        match = re.search(r'^msgid "(.*?)"', entry, re.MULTILINE)
        if match:
            msgid = match.group(1)
            
            # If we already processed this msgid, skip duplicates
            if msgid in seen_ids:
                continue
            seen_ids.add(msgid)
            
            # Apply correction if present
            if msgid in corrections:
                # Replace msgstr and remove fuzzy markers
                entry = re.sub(r'^#, fuzzy\n?', '', entry, flags=re.MULTILINE)
                entry = re.sub(r'^msgstr ".*?"', f'msgstr "{corrections[msgid]}"', entry, flags=re.MULTILINE | re.DOTALL)
            
        new_entries.append(entry)

    # Add missing corrections that weren't in the file
    for msgid, msgstr in corrections.items():
        if msgid not in seen_ids:
            new_entries.append(f'msgid "{msgid}"\nmsgstr "{msgstr}"')

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("\n\n".join(new_entries))
    print(f"Repaired {file_path}")

pt_corrections = {
    "Client Details": "Detalhes do Cliente",
    "Client Information": "Informações do Cliente",
    "Connected Profiles": "Perfis Conectados",
    "Primary": "Principal",
    "Additional Details": "Detalhes Adicionais",
    "Receptionist": "Recepcionista",
    "Decision Maker": "Tomador de Decisão",
    "Decision Factors": "Fatores de Decisão",
    "Preferred Time": "Horário de Preferência",
    "Preferred Method": "Método de Preferência",
    "Observations": "Observações",
    "Interactions": "Interações",
    "Proposals": "Propostas",
    "Visits": "Visitas",
    "Health Check": "Análise de Saúde",
    "SEO Ranking": "Ranking SEO",
    "GMB Insights": "Insights do GMB",
    "Projects / Post-Sales": "Projetos / Pós-Venda",
    "Services Catalog": "Catálogo de Serviços",
    "Service Packages": "Pacotes de Serviços",
    "Log Visit / Call": "Registrar Visita / Chamada",
    "New Proposal": "Nova Proposta",
    "Track Keyword": "Rastrear Palavra-chave",
    "Update Data": "Atualizar Dados",
    "Total Impressions": "Total de Impressões",
    "Calls": "Chamadas",
    "Website Clicks": "Cliques no Site",
    "Active Projects and Deliveries": "Projetos e Entregas Ativas",
    "Start New Project": "Iniciar Novo Projeto",
    "Manage": "Gerenciar",
    "Confirm Deletion": "Confirmar Exclusão",
    "Delete Client": "Excluir Cliente",
    "Are you sure you want to delete the client": "Tem certeza que deseja excluir o cliente",
    "This action will move the client to the trash (Soft Delete).": "Esta ação moverá o cliente para a lixeira (Soft Delete).",
    "New User": "Novo Usuário",
    "Manage Users": "Gerenciar Usuários",
    "User List": "Lista de Usuários",
    "Deactivate": "Desativar",
    "Activate": "Ativar",
    "Latest Interactions": "Últimas Interações",
    "Recent Activity": "Atividade Recente",
    "Latest Visits": "Últimas Visitas",
    "Latest Health Checks": "Últimas Análises de Saúde",
    "No recent interactions.": "Nenhuma interação recente.",
    "No recent visits.": "Nenhuma visita recente.",
    "Operational Task Queue (Pending)": "Fila de Tarefas Operacionais (Pendente)",
    "No pending tasks.": "Nenhuma tarefa pendente.",
    "Project": "Projeto",
    "End Date": "Data de Término",
    "Value": "Valor",
    "New Appointment": "Novo Agendamento",
    "Month": "Mês",
    "Week": "Semana",
    "Agenda": "Agenda",
    "New Column": "Nova Coluna",
    "Restore Default": "Restaurar Padrão",
    "Linked Profiles": "Perfis Conectados",
    "Connect Google Account": "Conectar Conta Google",
    "Google Account": "Conta Google",
    "Token Expired": "Token Expirado",
    "Back": "Voltar",
    "Connect your Google accounts to sync profiles and reviews": "Conecte suas contas Google para sincronizar perfis e avaliações",
    "Company": "Empresa",
    "Manage Users": "Gerenciar Usuários"
}

es_corrections = {
    "Client Details": "Detalles del Cliente",
    "Client Information": "Información del Cliente",
    "Connected Profiles": "Perfiles Conectados",
    "Primary": "Principal",
    "Additional Details": "Detalles Adicionales",
    "Receptionist": "Recepcionista",
    "Decision Maker": "Tomador de Decisión",
    "Decision Factors": "Factores de Decisión",
    "Preferred Time": "Horario de Preferencia",
    "Preferred Method": "Método de Preferencia",
    "Observations": "Observaciones",
    "Interactions": "Interacciones",
    "Proposals": "Propuestas",
    "Visits": "Visitas",
    "Health Check": "Auditoría de Salud",
    "SEO Ranking": "Ranking SEO",
    "GMB Insights": "Insights de GMB",
    "Projects / Post-Sales": "Proyectos / Post-Venta",
    "Log Visit / Call": "Registrar Visita / Llamada",
    "New Proposal": "Nueva Propuesta",
    "Track Keyword": "Rastrear Palabra Clave",
    "Update Data": "Actualizar Datos",
    "Total Impressions": "Total de Impresiones",
    "Calls": "Llamadas",
    "Website Clicks": "Clics en Sitio Web",
    "Active Projects and Deliveries": "Proyectos y Entregas Activas",
    "Start New Project": "Iniciar Nuevo Proyecto",
    "Manage": "Gestionar",
    "Confirm Deletion": "Confirmar Eliminación",
    "Delete Client": "Eliminar Cliente",
    "Are you sure you want to delete the client": "¿Está seguro de que desea eliminar al cliente",
    "This action will move the client to the trash (Soft Delete).": "Esta acción moverá al cliente a la papelera (Soft Delete).",
    "New User": "Nuevo Usuario",
    "Manage Users": "Gestionar Usuarios",
    "User List": "Lista de Usuarios",
    "Deactivate": "Desactivar",
    "Activate": "Activar",
    "Latest Interactions": "Últimas Interacciones",
    "Recent Activity": "Actividad Reciente",
    "Latest Visits": "Últimas Visitas",
    "Latest Health Checks": "Últimas Auditorías de Salud",
    "No recent interactions.": "No hay interacciones recientes.",
    "No recent visits.": "No hay visitas recientes.",
    "Operational Task Queue (Pending)": "Cola de Tareas Operativas (Pendiente)",
    "No pending tasks.": "No hay tareas pendientes.",
    "Project": "Proyecto",
    "End Date": "Fecha de Finalización",
    "Value": "Valor",
    "New Appointment": "Nueva Cita",
    "Month": "Mes",
    "Week": "Semana",
    "Agenda": "Agenda",
    "New Column": "Nueva Columna",
    "Restore Default": "Restaurar por Defecto",
    "Linked Profiles": "Perfiles Conectados",
    "Connect Google Account": "Conectar Cuenta de Google",
    "Google Account": "Cuenta de Google",
    "Token Expired": "Token Caducado",
    "Back": "Volver",
    "Connect your Google accounts to sync profiles and reviews": "Conecte sus cuentas de Google para sincronizar perfiles y reseñas",
    "Company": "Empresa",
    "Manage Users": "Gestionar Usuarios"
}

en_corrections = {
    "DASHBOARD_AWAITING_PAYMENT": "Awaiting Payment",
    "DASHBOARD_TOTAL_CLIENTS": "Total Clients",
    "DASHBOARD_TOTAL_PROPOSALS": "Total Proposals",
    "DASHBOARD_PENDING_CONTRACTS": "Pending Contracts",
    "DASHBOARD_NEW_LEADS_7D": "New Leads (7d)",
    "DASHBOARD_NEW_LEADS_15D": "New Leads (15d)",
    "DASHBOARD_CLOSED_SALES": "Closed Sales",
    "DASHBOARD_AVG_TICKET": "Avg Ticket"
}

repair_po_file(r'app/translations/pt_BR/LC_MESSAGES/messages.po', pt_corrections)
repair_po_file(r'app/translations/pt/LC_MESSAGES/messages.po', pt_corrections)
repair_po_file(r'app/translations/es/LC_MESSAGES/messages.po', es_corrections)
repair_po_file(r'app/translations/en/LC_MESSAGES/messages.po', en_corrections)
