
import os

def check_po_bytes(file_path, search_str):
    with open(file_path, 'rb') as f:
        content = f.read()
    
    search_bytes = f'msgid "{search_str}"'.encode('utf-8')
    index = content.find(search_bytes)
    if index != -1:
        print(f"Found '{search_str}' in PO at index {index}")
        start = max(0, index - 5)
        end = min(len(content), index + len(search_bytes) + 20)
        print(f"Bytes: {content[start:end]}")
    else:
        print(f"'{search_str}' NOT found in PO bytes")

check_po_bytes(r'app/translations/pt_BR/LC_MESSAGES/messages.po', "Awaiting Payment")
check_po_bytes(r'app/translations/pt_BR/LC_MESSAGES/messages.po', "Total Clients")
check_po_bytes(r'app/translations/pt_BR/LC_MESSAGES/messages.po', "Pending Contracts")
check_po_bytes(r'app/translations/pt_BR/LC_MESSAGES/messages.po', "Total Proposals")
