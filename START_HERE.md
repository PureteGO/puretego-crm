# Comece Aqui Amanhã! ☀️

Siga esta sequência exata para finalizar e fazer o deploy:

### 1. Preencher e Compilar Traduções
Abra o terminal e rode:
```powershell
python fill_google_translations.py
venv\Scripts\pybabel compile -d app/translations
```

### 2. Reiniciar o Servidor
Se o servidor estiver rodando, pare (Ctrl+C) e reinicie para carregar as novas traduções:
```powershell
.\start_local.bat
```

### 3. Verificar no Navegador
Acesse:
- [Dashboard (Português/Espanhol)](http://127.0.0.1:5000/dashboard)
  - *Verifique:* Cards "Contratos Pendentes", "Total Propostas".
- [Integração Google](http://127.0.0.1:5000/integrations/google/)
  - *Verifique:* Títulos em Português/Espanhol ("Contas Conectadas", botões, tabela).

### 4. Deploy Seguro 🚀
Se tudo estiver OK no passo 3:
```powershell
git add .
git commit -m "fix: translations standardization for dashboard and google integration"
git push orig master
# (E depois o seu comando de deploy de costume no servidor)
```

### 5. Limpeza (Pós-Deploy)
```powershell
del fill_google_translations.py
del find_empty_translations.py
```
