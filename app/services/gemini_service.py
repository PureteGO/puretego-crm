import logging
import google.generativeai as genai
from flask import current_app
import os

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        self.api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash') # Using Flash as requested
        else:
            self.model = None
            logger.warning("GOOGLE_API_KEY not found. Gemini features disabled.")

    def generate_content(self, prompt):
        if not self.model:
            return "Erro: API Key do Google Gemini não configurada."
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            current_app.logger.error(f"Gemini API Error: {str(e)}")
            return "Desculpe, não consegui gerar o conteúdo no momento. Tente novamente mais tarde."

    def generate_post_suggestion(self, client_name, address, segment=None):
        prompt = f"""
        Você é um especialista em marketing digital para pequenos negócios locais.
        Crie uma sugestão de post para redes sociais (Instagram/Facebook) para o cliente: {client_name}.
        Endereço: {address}.
        Segmento: {segment or 'Geral'}.
        
        O post deve ser engajador, usar emojis, e incluir uma 'Chamada para Ação' (CTA) clara.
        Foque em uma oferta ou novidade semanal.
        """
        return self.generate_content(prompt)

    def generate_faq_suggestion(self, client_name, segment=None):
        prompt = f"""
        Crie uma lista de 5 Perguntas Frequentes (Q&A) relevantes para o perfil do Google Business Profile de: {client_name}.
        Segmento: {segment or 'Comércio Local'}.
        
        Formato:
        1. **Pergunta:** ...
           **Resposta:** ...
        
        As respostas devem ser profissionais e convidar o cliente a visitar ou entrar em contato.
        """
        return self.generate_content(prompt)

    def generate_quick_check_summary(self, input_data):
        """
        Gera o sumário do Quick Health Check usando o prompt específico.
        input_data deve ser um dicionário/JSON com a estrutura necessária.
        """
        import json
        
        # Serialize input carefully to avoid issues
        json_input = json.dumps(input_data, ensure_ascii=False)
        
        prompt = f"""
You are an assistant specialized in Google Business Profile and Local SEO.
Your job is to generate a short **Quick Health Check** summary for the business owner, in the language specified by the `language` field.

You MUST strictly follow the business logic described below, including the score adjustment with a multiplier based on missing critical items and the website vs. social profile rule.

---

## INPUT (JSON)

```json
{json_input}
```

(Note: strict adherence to the checks in the JSON is required)

## INTERNAL LOGIC (DO NOT EXPOSE AS RULES)

Follow this internal logic step by step. You may reason about it, but you must NOT describe these rules explicitly to the user.

### 1. Detect critical failures

- A critical failure exists whenever a `criteria_results` item:
  - has `type = 'critical'` AND
  - `passed = False` OR `passed = None`.

- Count how many such items exist.
  - Name this number `critical_missing_count`.

### 2. Website vs. social profile handling

- The criterion "Possui Site / Posee Sitio Web / Has Website" must respect this rule:

  - If `site_type = 'website_real'`:
    - Treat as the business having a real professional website.

  - If `site_type = 'social_profile'` OR `site_type = 'link_hub'`:
    - Treat as the business **NOT** having a professional website.
    - Conceptually, this should behave like a failed critical item for the “Has Website” criterion, even if some other logic marked it as passed.

  - If `site_type = 'none'`:
    - The business has no website at all.

- Even if the raw data says "site detected", you must interpret `social_profile` or `link_hub` as a **problem**: the business still needs a real website.

### 3. Adjust score with multiplier

- Start from `summary.score_publico` as the base numeric score.

- Recalculate `critical_missing_count` considering the website rule above. If the website field is `social_profile`, `link_hub`, or `none`, the “Has Website” criterion should be considered a critical failure in your reasoning.

- Define a multiplier according to the final `critical_missing_count`:

  - If `critical_missing_count == 0` → `multiplier = 1.0`
  - If `critical_missing_count == 1` → `multiplier = 0.8`
  - If `critical_missing_count == 2` → `multiplier = 0.6`
  - If `critical_missing_count >= 3` → `multiplier = 0.4`

- Compute:

  - `score_ajustado = round(score_publico * multiplier)`

- You MUST use `score_ajustado` (not `score_publico`) for any score you mention in the text, like “70/100”.

### 4. Textual classification based on adjusted score and critical failures

- Use `critical_missing_count` and `score_ajustado` to derive a short textual classification, depending on `language`.

- For Portuguese (`pt`):

  - If `critical_missing_count == 0`:
    - If `score_ajustado >= 80` → “boa”
    - If `score_ajustado >= 60` → “regular”
    - Else → “fraca”
  - If `critical_missing_count == 1` → “regular”
  - If `critical_missing_count >= 2` → “fraca”

- For Spanish (`es`):

  - If `critical_missing_count == 0`:
    - If `score_ajustado >= 80` → “buena”
    - If `score_ajustado >= 60` → “regular”
    - Else → “débil”
  - If `critical_missing_count == 1` → “regular”
  - If `critical_missing_count >= 2` → “débil”

- For English (`en`):

  - If `critical_missing_count == 0`:
    - If `score_ajustado >= 80` → “good”
    - If `score_ajustado >= 60` → “fair”
    - Else → “weak”
  - If `critical_missing_count == 1` → “fair”
  - If `critical_missing_count >= 2` → “weak”

- When there are critical failures (1 or more), avoid overly positive adjectives like “excellent”, “perfeito”, “excelente”, “perfect”.

---

## OUTPUT REQUIREMENTS

You must generate a **very short** summary (Quick Health Check) directly to the business owner.

1. **Language control**

   - Always answer exclusively in the language defined by `language` (pt, es, or en).

2. **Length and structure**

   - Maximum **3 short sentences**.
   - No bullet points, no headings, no technical terms like “multiplier”, “weight” or “raw score”.
   - Do NOT mention JSON, fields, or internal logic.

3. **Content of each sentence**

   - Sentence 1:
     - Present the adjusted score (`score_ajustado`) and the textual classification.
     - Examples (adapt text):
       - pt: “Saúde geral do seu perfil: 42/100, considerada fraca por falhas em pontos fundamentais.”
       - es: “Salud general de tu perfil: 42/100, considerada débil por fallas en puntos fundamentales.”

   - Sentence 2:
     - Highlight main CRITICAL problems (Unverified, No real website, No posts, No replies).

   - Sentence 3:
     - Start with "Prioridade:" / "Prioridad:" / "Priority:".
     - Give 2–3 next actions.

4. **Tone**
   - Clear, direct, practical. No overselling if critical failures exist.

Your final response for this prompt is ONLY the 3-sentence paragraph in the selected language.
"""
        return self.generate_content(prompt)

    def generate_internal_audit_summary(self, input_data):
        """
        Gera o sumário interno (Health Check Oficial) usando o prompt específico.
        input_data deve ser um dicionário/JSON com a estrutura necessária.
        """
        import json
        
        # Serialize input carefully
        json_input = json.dumps(input_data, ensure_ascii=False)
        
        prompt = f"""
You are an internal Local SEO consultant reading a full Health Check for a Google Business Profile.
Your task is to produce an internal diagnostic and action plan, in the language specified by the `language` field.

You MUST strictly follow the same business logic used in the Quick Health Check, including the adjusted score multiplier and the website vs. social profile rule.

---

## INPUT (JSON)

```json
{json_input}
```

---

## INTERNAL LOGIC (DO NOT EXPOSE AS RULES)

### 1. Detect critical failures (same as Quick)
- A critical failure exists whenever a `criteria_results` item has `type = 'critical'` AND `passed = False`.
- Count them as `critical_missing_count`.

### 2. Website rule (same as Quick)
- `site_type = 'website_real'` → has professional website.
- `site_type = 'social_profile'` or `site_type = 'link_hub'`: Treat as NO professional website (critical failure).
- `site_type = 'none'`: No website.

Recalculate `critical_missing_count` considering this.

### 3. Adjust score with multiplier (same as Quick)
- Use `summary.score_publico` as base.
- Multiplier based on final `critical_missing_count`:
  - 0 critical missing → 1.0
  - 1 critical missing → 0.8
  - 2 critical missing → 0.6
  - 3+ critical missing → 0.4
- `score_ajustado = round(score_publico * multiplier)`

### 4. Additional internal emphasis
- If review replies are missing, mark as reputation opportunity.
- If posts are missing, mark as content opportunity.

---

## OUTPUT REQUIREMENTS

Generate an internal note for consultants/CSM.

1. **Language**
   - Always answer exclusively in the selected language (pt, es, or en).

2. **Structure** (Markdown, 4 sections with translated headings)

   - Section 1: Overview
     - Mention `score_ajustado`, number of critical failures, and impact.

   - Section 2: Critical Points
     - List ALL failed critical criteria.
     - Specific text for website issues (social profile vs none).

   - Section 3: Key Opportunities
     - Base on moderate/positive criteria and details.

   - Section 4: Priority Action Plan
     - Ordered list of 3-5 actions (Verify > Website > Posts > Reviews).

3. **Tone**
   - Business-focused, pragmatic. No meta explanations.

Your final response for this prompt is ONLY the four sections in Markdown, in the selected language.
"""
        return self.generate_content(prompt)
