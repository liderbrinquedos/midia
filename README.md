# Central de Mídias Líder

Portal para representantes comerciais. Fase 1 demonstrativa, com frontend HTML/CSS/JS e backend FastAPI. Microsoft Graph permanece desativado.

## Executar localmente

Requer Python 3.12 ou superior. Na raiz do projeto:

```powershell
python -m venv .venv
.venv/Scripts/Activate.ps1
pip install -r backend/requirements.txt
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8876
```

Abra http://127.0.0.1:8876. O backend serve o frontend na prévia local. Documentação da API: `/docs`.

## Estrutura

- `frontend/index.html`: portal e modal de produto.
- `frontend/css/style.css`: identidade visual e layouts responsivos.
- `frontend/js/config.js`: configuração pública centralizada de API_BASE_URL.
- `frontend/js/app.js`: busca, navegação entre todos os produtos, novidades e mais acessados, modal e compartilhamento.
- `backend/app/main.py`: aplicação FastAPI e CORS.
- `backend/app/routers/media.py`: endpoints do catálogo.
- `backend/app/services/index.py`: repositório de busca em memória carregado do JSON.
- `backend/app/services/onedrive.py`: contrato inicial, sem chamadas ao Graph.
- `backend/data/media_index.json`: seis produtos demonstrativos.
- `backend/tests/test_api.py`: testes automatizados.
- `render.yaml`: configuração do backend no Render.

## API

GET /health retorna {"status":"ok"}.
GET /api/search?q=12345 retorna query e results.
GET /api/products/{codigo} retorna um produto ou 404.
GET /api/products/{codigo}/media retorna images e videos.
GET /api/categories retorna categorias.
GET /api/latest retorna produtos por data, do mais recente ao mais antigo.

A busca ignora acentos e caixa e cobre nome, código, referência, EAN, descrição, linha e categoria. Consultas são limitadas a 200 caracteres. O índice é carregado uma vez na inicialização; editar o JSON requer reiniciar o processo. Nenhuma busca consulta o OneDrive.

## Testes

Dentro de backend, execute `python -m unittest discover -s tests`.
Cinco testes passam: saúde, busca normalizada e identificadores, produto inexistente, endpoints de catálogo e busca vazia de resultados.
Verificação no navegador: busca por caminhao, abertura de produto, aba sem vídeos e retorno ao catálogo.

## Publicar

Backend: conecte o repositório correto ao Render usando render.yaml. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Defina CORS_ORIGINS com o domínio exato do frontend.
Frontend: configure `window.PORTAL_CONFIG.API_BASE_URL` em frontend/js/config.js com a URL HTTPS do backend Render. Publique apenas o conteúdo de frontend na raiz do subdomínio do Plesk. Este frontend não exige build. Não envie a pasta backend nem arquivos .env ao diretório público. Faça backup da demo anterior antes de substituir arquivos no Plesk.

## Configuração Microsoft

Copie .env.example para .env somente no ambiente do backend. As quatro variáveis MICROSOFT_TENANT_ID, MICROSOFT_CLIENT_ID, MICROSOFT_CLIENT_SECRET e ONEDRIVE_DRIVE_ID estão previstas, mas não ativam a integração. Não compartilhe segredos pelo frontend ou pelo Git.

Próxima fase: confirmar tipo de conta Microsoft, tenant e drive, permissões mínimas e consentimento administrativo, estrutura de pastas, identificação de produtos e origem dos metadados. Implementar sincronização independente da busca com paginação/delta, IDs estáveis e atualização atômica do índice. Resolver links temporários de download no backend sob demanda. Migrar a persistência por trás do serviço de índice quando necessário.

## Limites da prévia

Dados, códigos, EANs, datas e contagens de acessos são demonstrativos. As imagens são referências externas, incluindo produto de outro fabricante no cartão de caminhão; não constituem catálogo oficial Líder. Fontes em docs/image-sources.md. Imagens não são copiadas para o repositório e dependem da disponibilidade dos sites de origem. O logo oficial fornecido pelo usuário está em frontend/assets/logo-lider.webp.

O link de baixar abre a imagem externa para salvamento pelo navegador; download direto e ZIP ainda não estão implementados. Vídeos estão vazios. WhatsApp é bloqueado em localhost para não compartilhar links inacessíveis a terceiros. Em produção, o botão abre o compositor do WhatsApp; o usuário envia a mensagem. Login, favoritos, analytics reais, documentos, permissões e painel administrativo são etapas futuras. Prévia ainda não publicada e sem conexão ao Microsoft Graph.

## Catálogo real do OneDrive

Configure as cinco variáveis Microsoft/OneDrive de `.env.example` no `.env` privado. Não envie segredos ao Git. MEDIA_INDEX_PATH é opcional e aceita um caminho absoluto.

Na pasta `backend`, execute `python -m app.services.sync` para atualizar o catálogo. A varredura inclui todas as subpastas autorizadas e só substitui o índice após concluir sem falhas. O servidor recarrega o índice atualizado automaticamente. A sincronização é manual nesta versão; execute novamente quando o banco mudar. Em Render, mantenha o índice e views.sqlite3 em armazenamento persistente.

O catálogo agrupa arquivos pelas pastas e códigos existentes. Coleções sem código continuam como coleções. Códigos repetidos em linhas diferentes não são mesclados. EANs não são inventados. Novidades usa a data de alteração dos arquivos. Mais acessados registra aberturas no portal, sem identificar visitantes; não representa visitantes únicos.

A busca é paginada. Fotos, vídeos e materiais têm links de visualização e download do original. Alguns formatos exigem aplicativo compatível. URLs temporárias são resolvidas no servidor e não são gravadas no índice. Downloads só aceitam IDs presentes no catálogo. O índice privado e contagens locais são ignorados pelo Git. Logs e atalhos Windows não integram o catálogo. O servidor local usa 127.0.0.1; publicação e controle de acesso devem ser configurados na hospedagem.

Validação: `python -m unittest discover -s tests -v` dentro de `backend`. A suíte usa catálogo de exemplo isolado, sem credenciais nem chamadas reais ao Graph.
