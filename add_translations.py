
import os

translations = {
    "en": [
        ('msgid "Projetos / Contratos Ativos"', 'msgstr "Projects / Active Contracts"'),
        ('msgid "Ativos"', 'msgstr "Active"'),
        ('msgid "Concluídos"', 'msgstr "Completed"'),
        ('msgid "Todos"', 'msgstr "All"'),
        ('msgid "Gerenciar Projeto"', 'msgstr "Manage Project"'),
        ('msgid "Nenhum projeto encontrado."', 'msgstr "No projects found."'),
        ('msgid "Projetos são criados a partir da visualização de um Cliente."', 'msgstr "Projects are created from the Client view."'),
        ('msgid "Ver Clientes"', 'msgstr "View Clients"'),
        ('msgid "Sem descrição."', 'msgstr "No description."')
    ],
    "es": [
        ('msgid "Projetos / Contratos Ativos"', 'msgstr "Proyectos / Contratos Activos"'),
        ('msgid "Ativos"', 'msgstr "Activos"'),
        ('msgid "Concluídos"', 'msgstr "Concluidos"'),
        ('msgid "Todos"', 'msgstr "Todos"'),
        ('msgid "Gerenciar Projeto"', 'msgstr "Gestionar Proyecto"'),
        ('msgid "Nenhum projeto encontrado."', 'msgstr "Ningún proyecto encontrado."'),
        ('msgid "Projetos são criados a partir da visualização de um Cliente."', 'msgstr "Los proyectos se crean partiendo de la vista de Cliente."'),
        ('msgid "Ver Clientes"', 'msgstr "Ver Clientes"'),
        ('msgid "Sem descrição."', 'msgstr "Sin descripción."')
    ],
    "pt": [ # pt and pt_BR
        ('msgid "Projetos / Contratos Ativos"', 'msgstr "Projetos / Contratos Ativos"'),
        ('msgid "Ativos"', 'msgstr "Ativos"'),
        ('msgid "Concluídos"', 'msgstr "Concluídos"'),
        ('msgid "Todos"', 'msgstr "Todos"'),
        ('msgid "Gerenciar Projeto"', 'msgstr "Gerenciar Projeto"'),
        ('msgid "Nenhum projeto encontrado."', 'msgstr "Nenhum projeto encontrado."'),
        ('msgid "Projetos são criados a partir da visualização de um Cliente."', 'msgstr "Projetos são criados a partir da visualização de um Cliente."'),
        ('msgid "Ver Clientes"', 'msgstr "Ver Clientes"'),
        ('msgid "Sem descrição."', 'msgstr "Sem descrição."')
    ]
}

base_dir = r"c:\ProAG\puretego-crm\app\translations"
langs = ["en", "es", "pt", "pt_BR"]

for lang in langs:
    path = os.path.join(base_dir, lang, "LC_MESSAGES", "messages.po")
    key = "pt" if "pt" in lang else lang
    
    if os.path.exists(path):
        print(f"Updating {path}...")
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n\n")
            for msgid, msgstr in translations[key]:
                f.write(f"{msgid}\n{msgstr}\n\n")
    else:
        print(f"Path not found: {path}")

print("Done appending translations.")
