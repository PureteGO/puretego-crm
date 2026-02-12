import os

file_path = 'app/translations/pt_BR/LC_MESSAGES/messages.po'

new_translations = [
    ('Restore Default', 'Restaurar Padrão'),
    ('New Column', 'Nova Coluna'),
    ('Add Client to Column', 'Adicionar Cliente na Coluna'),
    ('Stage Name', 'Nome da Etapa'),
    ('Edit Stage', 'Editar Etapa'),
    ('Add Client', 'Adicionar Cliente'),
    ('WARNING: This will remove all custom columns and move ALL clients to No Stage. Are you sure?', 'AVISO: Isso removerá todas as colunas personalizadas e moverá TODOS os clientes para Sem Etapa. Tem certeza?'),
    ('Quick Health Check (GMB)', 'Verificação Rápida (GMB)'),
    ('Sales Closed', 'Vendas Fechadas'),
    ('SaaS Admin', 'Admin SaaS'),
    ('SuperAdmin', 'SuperAdmin')
]

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

with open(file_path, 'a', encoding='utf-8') as f:
    for msgid, msgstr in new_translations:
        if f'msgid "{msgid}"' not in content:
            f.write(f'\nmsgid "{msgid}"\nmsgstr "{msgstr}"\n')
            print(f"Added: {msgid}")
        else:
            print(f"Skipped (exists): {msgid}")
