# Preparação para Deploy (Status Atual)

**⛔ Recomendação: NÃO DEPLOYAR AGORA**

## Estado dos Arquivos
- **Templates (`.html`):** ✅ Corrigidos. As chaves de tradução agora são linha única (`_('Texto')`), evitando erros.
- **Códigos (`.py`):** ✅ Scripts auxiliares criados e seguros.
- **Traduções (`.po`):** ⚠️ **Pendente.** O comando `pybabel update` criou as entradas, mas elas estão vazias aguardando o script de preenchimento.
- **Compilados (`.mo`):** ❌ **Desatualizados.** Precisam ser regerados após o passo anterior.

## O que acontecerá se subir agora:
- Partes do Dashboard e da Integração Google aparecerão em **Inglês** ou com textos faltando para os usuários finais.

## Próximos Passos (Amanhã)
1. Rodar `python fill_google_translations.py`
2. Rodar `pybabel compile -d app/translations`
3. Verificar visualmente.
4. `git add .`
5. `git commit -m "fix: standardization of translations for Dashboard and Google Integration"`
6. Deploy.
