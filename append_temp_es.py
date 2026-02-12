
import os

def append_translations():
    file_path = r'app/translations/es/LC_MESSAGES/messages.po'
    if not os.path.exists(file_path):
        return

    translations = {
        "DASHBOARD_AWAITING_PAYMENT": "Esperando Pago",
        "DASHBOARD_TOTAL_CLIENTS": "Total de Clientes",
        "Awaiting Payment": "Esperando Pago",
        "Total Clients": "Total de Clientes",
        "Edit Client": "Editar Cliente",
        "Basic Information": "Información Básica",
        "Detailed Information": "Información Detallada"
    }

    with open(file_path, 'a', encoding='utf-8') as f:
        for msgid, msgstr in translations.items():
            f.write(f'\nmsgid "{msgid}"\nmsgstr "{msgstr}"\n')

if __name__ == "__main__":
    append_translations()
