"""
Script to write the PDF template file with Jinja2 delimiters intact.
Rewritten to match "Start2Go" Reference Design:
- Parametric Layout (Margins, Fonts, Colors)
- Full Bleed Color Bands
- "Magazine" Style Typography
"""

TEMPLATE_PATH = r"C:\ProAG\puretego-crm\app\templates\proposals\pdf_template.html"

T = []

# ---- 1. DESIGN SYSTEM (Global Parameters) ----
T.append('{%- set C1 = theme.primary -%}')       # Main Brand Color
T.append('{%- set C_TXT = "#333333" -%}')        # Body Text
T.append('{%- set C_GRY = "#666666" -%}')        # Subtitles
T.append('{%- set F_HERO = "42pt" -%}')          # Cover Title
T.append('{%- set F_H1 = "28pt" -%}')            # Section Headers
T.append('{%- set F_H2 = "18pt" -%}')            # Subtitles
T.append('{%- set F_BODY = "11pt" -%}')          # Body Text

# ---- DOCTYPE + HEAD ----
T.append('<!DOCTYPE html>')
T.append('<html>')
T.append('<head>')
T.append('<meta charset="utf-8">')
T.append('<style>')

# ---- 2. CSS RESET & LAYOUT ----
T.append('  @page {')
T.append('    size: A4;')
T.append('    margin: 0cm; /* Full bleed for bands */')
T.append('    @frame content_frame {')
T.append('        left: 2cm;')
T.append('        width: 17cm;')
T.append('        top: 2cm;')
T.append('        height: 25cm;')
T.append('    }')
T.append('  }')
T.append('  body { font-family: Helvetica, Arial, sans-serif; color: {{ C_TXT }}; line-height: 1.5; font-size: {{ F_BODY }}; }')

# Utilities
T.append('  .text-white { color: white; }')
T.append('  .text-primary { color: {{ C1 }}; }')
T.append('  .bold { font-weight: bold; }')
T.append('  .uppercase { text-transform: uppercase; }')
T.append('  .text-center { text-align: center; }')
T.append('  .text-right { text-align: right; }')
T.append('  .mb-1 { margin-bottom: 1cm; }')
T.append('  .mb-2 { margin-bottom: 2cm; }')

# ---- 3. COMPONENT STYLES ----
# Cover
T.append('  .cover-hero { background-color: {{ C1 }}; height: 60%; width: 100%; position: absolute; top: 0; left: 0; }')
T.append('  .cover-content { position: absolute; top: 15%; width: 100%; text-align: center; color: white; padding: 0 1cm; }')
T.append('  .client-name { font-size: 56pt; font-weight: bold; line-height: 1.1; margin-bottom: 0.5cm; }')
T.append('  .proposal-title { font-size: 24pt; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 2cm; opacity: 0.9; }')
T.append('  .cover-footer { position: absolute; bottom: 2cm; right: 2cm; text-align: right; }')

# Section Bands
T.append('  .section-band { background-color: {{ C1 }}; color: white; padding: 0.8cm 2cm; margin-left: -2cm; margin-right: -2cm; margin-bottom: 1.5cm; }')
T.append('  .sec-num { font-size: 36pt; font-weight: bold; opacity: 0.4; margin-right: 0.5cm; }')
T.append('  .sec-title { font-size: 24pt; font-weight: bold; text-transform: uppercase; }')

# Diagnostics
T.append('  .score-circle { width: 4cm; height: 4cm; background-color: {{ C1 }}; border-radius: 50%; color: white; font-size: 36pt; font-weight: bold; text-align: center; line-height: 3.8cm; margin: 0 auto; }')
T.append('  .diag-table { width: 100%; border-collapse: collapse; margin-top: 1cm; }')
T.append('  .diag-table th { text-align: left; padding: 10px; border-bottom: 2px solid {{ C1 }}; color: {{ C1 }}; font-weight: bold; }')
T.append('  .diag-table td { padding: 10px; border-bottom: 1px solid #eee; }')
T.append('  .pass { color: #28a745; font-weight: bold; }')
T.append('  .fail { color: #dc3545; font-weight: bold; }')

# Investment
T.append('  .option-card { border: 1px solid #ddd; padding: 0; margin-bottom: 1cm; page-break-inside: avoid; }')
T.append('  .opt-header { background-color: #f8f9fa; padding: 10px 15px; border-bottom: 1px solid #ddd; font-weight: bold; font-size: 14pt; color: {{ C1 }}; }')
T.append('  .total-box { background-color: {{ C1 }}; color: white; padding: 1cm; text-align: right; font-size: 20pt; font-weight: bold; margin-top: 1cm; }')
T.append('</style>')
T.append('</head>')
T.append('<body>')

# ==== COVER PAGE (Full Bleed Hero) ====
T.append('<div style="page-break-after: always;">')
T.append('<div class="cover-hero">') # Color Block (60%)
# Logo in White Box (Top Left)
T.append('{% if company_info.logo_url %}')
T.append('<div style="background:white; padding: 20px; display:inline-block; margin-left: 2cm; margin-top: 2cm; border-radius: 4px;">')
T.append('<img src="{{ company_info.logo_url }}" style="height: 1.5cm;">')
T.append('</div>')
T.append('{% endif %}')

# Hero Content
T.append('<div class="cover-content">')
T.append('<div class="client-name">{{ proposal.client_name }}</div>')
T.append('<div class="proposal-title">{{ texts.proposal_title }}</div>')
T.append('<div style="font-size: 14pt; opacity: 0.8;">{{ texts.services_subtitle }}</div>')
T.append('</div>')
T.append('</div>') # End Hero

# Footer (White Area)
T.append('<div class="cover-footer">')
T.append('<div style="font-size: 16pt; font-weight: bold; color: {{ C1 }};">{{ proposal.proposal_date.strftime("%B %Y")|title }}</div>')
T.append('<div style="border: 2px solid black; width: 3cm; height: 3cm; margin-left: auto; margin-top: 10px; text-align: center; line-height: 3cm;">QR CODE</div>')
T.append('</div>')
T.append('</div>')

# ==== CONTENT PAGES ====

# Section 01: About
T.append('<div style="page-break-before: always;">')
T.append('<div class="section-band"><span class="sec-num">01</span><span class="sec-title">{{ texts.about_title }}</span></div>')
T.append('<div style="padding: 0 1cm;">')
T.append('<p style="margin-bottom: 1cm;">{{ texts.about_description }}</p>')
# Grid 2x2
T.append('<table style="width:100%">')
T.append('<tr><td style="padding:10px; width:50%; vertical-align:top;"><div style="font-weight:bold; color:{{ C1 }}; font-size:14pt; margin-bottom:5px;">{{ texts.pillar_1_title }}</div>{{ texts.pillar_1_desc }}</td>')
T.append('<td style="padding:10px; width:50%; vertical-align:top;"><div style="font-weight:bold; color:{{ C1 }}; font-size:14pt; margin-bottom:5px;">{{ texts.pillar_2_title }}</div>{{ texts.pillar_2_desc }}</td></tr>')
T.append('<tr><td style="padding:10px; width:50%; vertical-align:top;"><div style="font-weight:bold; color:{{ C1 }}; font-size:14pt; margin-bottom:5px;">{{ texts.pillar_3_title }}</div>{{ texts.pillar_3_desc }}</td>')
T.append('<td style="padding:10px; width:50%; vertical-align:top;"><div style="font-weight:bold; color:{{ C1 }}; font-size:14pt; margin-bottom:5px;">{{ texts.pillar_4_title }}</div>{{ texts.pillar_4_desc }}</td></tr>')
T.append('</table>')
T.append('</div></div>')

# Section 02: Diagnostics
T.append('<div style="page-break-before: always;">')
T.append('<div class="section-band"><span class="sec-num">02</span><span class="sec-title">{{ texts.audit_title }}</span></div>')
T.append('<div style="padding: 0 1cm;">')
T.append('<p class="mb-1">{{ texts.audit_subtitle }}</p>')
T.append('{% if proposal.health_check %}')
T.append('<div class="score-circle">{{ proposal.health_check.score }}%</div>')
T.append('<div class="text-center bold" style="margin-bottom: 1cm;">{{ texts.score_label }}</div>')
# Table
T.append('{% if proposal.health_check.report_data %}')
T.append('<table class="diag-table"><thead><tr><th>Criteria</th><th class="text-right">Status</th></tr></thead><tbody>')
T.append('{% if proposal.health_check.report_data.criteria %}')
T.append('{% for item in proposal.health_check.report_data.criteria %}<tr><td>{{ item.name }}</td><td class="text-right">{% if item.status == "Detectado" or item.score == 100 %}<span class="pass">&#10003;</span>{% else %}<span class="fail">&#10007;</span>{% endif %}</td></tr>{% endfor %}')
T.append('{% elif proposal.health_check.report_data.criteria_results %}')
T.append('{% for item in proposal.health_check.report_data.criteria_results %}<tr><td>{{ item.name_es or item.name_pt or "-" }}</td><td class="text-right">{% if item.passed %}<span class="pass">&#10003;</span>{% else %}<span class="fail">&#10007;</span>{% endif %}</td></tr>{% endfor %}')
T.append('{% endif %}')
T.append('</tbody></table>')
T.append('{% endif %}')
T.append('{% endif %}')
T.append('</div></div>')

# Section 03: Investment
T.append('<div style="page-break-before: always;">')
T.append('<div class="section-band"><span class="sec-num">03</span><span class="sec-title">{{ texts.proposal_label }}</span></div>')
T.append('<div style="padding: 0 1cm;">')
T.append('{% for option in proposal.options %}')
T.append('<div class="option-card"><div class="opt-header">{{ option.name or "Option" }}<span style="float:right">{{ proposal.currency }} {{ "{:,.0f}".format(option.total_amount|float) }}</span></div>')
T.append('<div style="padding:15px;"><table style="width:100%; border-collapse:collapse;">')
T.append('{% for item in option["items"] %}<tr><td style="padding:5px 0;"><b>{{ item.display_name }}</b><br><small style="color:#666">{{ item.description }}</small></td><td style="text-align:right; vertical-align:top;">{{ "{:,.0f}".format(item.total|float) }}</td></tr>{% endfor %}')
T.append('</table></div></div>')
T.append('{% endfor %}')
# Total Box
T.append('<div class="total-box">{{ texts.total_investment }}: {{ proposal.currency }} {{ "{:,.0f}".format(proposal.total_amount|float) }}</div>')
T.append('</div></div>')

T.append('</body></html>')

# ---- Write the file ----
content = '\n'.join(T)
with open(TEMPLATE_PATH, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Written {len(content)} bytes to {TEMPLATE_PATH}")
