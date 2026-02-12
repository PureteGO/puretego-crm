
import os
import re

def standardize_template(file_path):
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex to find {{ _('Total\n                    Proposals') }} and similar
    # It catches {{ _('String1\n                    String2') }}
    # and replaces it with {{ _('String1 String2') }}
    
    def replacer(match):
        inner = match.group(1)
        # Remove newlines and collapse multiple spaces to a single one
        cleaned = re.sub(r'\s*\n\s*', ' ', inner).strip()
        return f"{{{{ _('{cleaned}') }}}}"

    # Target specific multiline patterns found in the templates
    new_content = re.sub(r'\{\{\s*_\(\'([^\']*)\'\)\s*\}\}', replacer, content, flags=re.DOTALL)
    
    # Fix specifically the ones I saw in index.html
    new_content = new_content.replace("{{ _('Awaiting Payment')\n                    }}", "{{ _('Awaiting Payment') }}")
    new_content = new_content.replace("{{ _('Total\n                    Proposals') }}", "{{ _('Total Proposals') }}")
    new_content = new_content.replace("{{ _('Pending\n                    Contracts') }}", "{{ _('Pending Contracts') }}")
    new_content = new_content.replace("_('Total Clients') }}\n                </h6>", "_('Total Clients') }}</h6>")

    # Audit for other common ones
    new_content = new_content.replace("_('Leads in\n                    Prospecting') }}", "_('Leads in Prospecting') }}")
    new_content = new_content.replace("_('Scheduled\n                    Meetings') }}", "_('Scheduled Meetings') }}")
    new_content = new_content.replace("_('Health Checks\n                    Done') }}", "_('Health Checks Done') }}")
    new_content = new_content.replace("_('Critical\n                    Leads') }}", "_('Critical Leads') }}")
    new_content = new_content.replace("_('Upcoming\n                    Meetings') }}", "_('Upcoming Meetings') }}")
    new_content = new_content.replace("_('Proposals\n                    Sent') }}", "_('Proposals Sent') }}")
    new_content = new_content.replace("_('Value in\n                    Negotiation') }}", "_('Value in Negotiation') }}")
    new_content = new_content.replace("_('SDR Opportunities\n                    (Handoffs)') }}", "_('SDR Opportunities (Handoffs)') }}")

    if content != new_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Standardized {file_path}")
    else:
        print(f"No changes needed for {file_path}")

# Run for all dashboard templates
standardize_template(r'app/templates/dashboard/index.html')
standardize_template(r'app/templates/dashboard/_finance.html')
standardize_template(r'app/templates/dashboard/_production.html')
standardize_template(r'app/templates/dashboard/_sdr.html')
standardize_template(r'app/templates/dashboard/_sales.html')
standardize_template(r'app/templates/clients/edit.html')
