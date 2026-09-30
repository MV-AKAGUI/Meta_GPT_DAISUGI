---
name: auto-github-sync
description: Skill de sincronização automática e segura de projetos com o GitHub. Não mistura pastas, puxa (pull) atualizações antes de enviar (push) e isola o versionamento no repositório ativo.
---

# GitHub Auto-Sync Skill

## Contexto
Esta é a skill mestra do ecossistema DAISUGI para versionamento de código seguro. 

## Instruções de Execução
Sempre que acionada, ou logo após a validação/conclusão de uma tarefa que altere o código, o agente deve seguir estritamente o fluxo abaixo:

1. **Garantir o Escopo:** Certifique-se de estar operando EXCLUSIVAMENTE no diretório raiz do projeto atual.
2. **Checar Mudanças:** Rode git status para confirmar quais arquivos foram alterados.
3. **Sincronismo Prévio:** Rode git pull origin main (ou branch padrão) para evitar conflitos de versão e baixar atualizações remotas.
4. **Adição:** Rode git add . para salvar as modificações em "stage".
5. **Registro (Commit):** Rode git commit -m "Auto-sync: [Descrição breve das mudanças]" detalhando exatamente o que foi validado.
6. **Envio (Push):** Rode git push origin main.
7. **Confirmação:** Retorne ao usuário informando o sucesso da sincronização segura.
