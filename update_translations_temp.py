
import os
import re

po_file_path = r'c:\ProAG\puretego-crm\app\translations\pt\LC_MESSAGES\messages.po'

def fix_translations():
    with open(po_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    
    # List of translations
    translations = {
        "New Receivable": "Novo Recebível",
        "Paid": "Pago",
        "All": "Todos",
        "Pending": "Pendente",
        "New Payable": "Nova Conta a Pagar",
        "Repeat for [N] months": "Repetir por [N] meses",
        "Register Payable": "Cadastrar Conta",
        "Mark this payable as paid?": "Marcar esta conta como paga?",
        "Due (Open)": "A Vencer",
        "Account Payable": "Conta a Pagar",
        "Finance": "Finanças",
        "Accounts Receivable": "Contas a Receber",
        "Accounts Payable": "Contas a Pagar",
        "Commissions": "Comissões",
        "Description": "Descrição",
        "Value": "Valor",
        "Due Date": "Vencimento",
        "Category": "Categoria",
        "Status": "Status",
        "Actions": "Ações",
        "No entries registered.": "Nenhum lançamento registrado.",
        "Manage Categories": "Gerenciar Categorias",
        "Category Name": "Nome da Categoria",
        "Color": "Cor"
    }

    for msgid, msgstr in translations.items():
        pattern = re.compile(f'msgid "{re.escape(msgid)}"', re.MULTILINE)
        if not pattern.search(content):
            print(f"Adding missing: {msgid}")
            content += f'\n\nmsgid "{msgid}"\nmsgstr "{msgstr}"\n'

    # Specific fix for "All" -> "Cancelar"
    bad_all_pattern = re.compile(r'msgid "All"\s+msgstr "Cancelar"')
    if bad_all_pattern.search(content):
        print("Fixing 'All' -> 'Cancelar' to 'All' -> 'Todos'")
        content = bad_all_pattern.sub('msgid "All"\nmsgstr "Todos"', content)

    # Check "Paid"
    paid_empty_pattern = re.compile(r'msgid "Paid"\s+msgstr ""')
    if paid_empty_pattern.search(content):
         print("Filling empty 'Paid' translation")
         content = paid_empty_pattern.sub('msgid "Paid"\nmsgstr "Pago"', content)

    if content != original_content:
        with open(po_file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Successfully updated messages.po")
    else:
        print("No changes needed in messages.po")

if __name__ == "__main__":
    fix_translations()
