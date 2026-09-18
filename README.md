# Central de Mídias Líder

Portal HTML/CSS/JS servido por FastAPI, integrado ao OneDrive empresarial via Microsoft Graph. Busca paginada, fotos, vídeos, materiais e download dos arquivos originais. O acesso do aplicativo ao OneDrive é somente leitura, limitado à pasta autorizada.

## Publicar no Coolify

Consulte [o passo a passo](docs/coolify.md). O Dockerfile da raiz entrega frontend e API juntos na porta 8000. Configure um volume persistente e as credenciais Microsoft como variáveis de runtime no Coolify. A primeira inicialização cria o catálogo; reinicializações reutilizam o índice salvo.

## Executar localmente

Requer Python 3.12. Na raiz, copie `.env.example` para `.env` e preencha as cinco variáveis Microsoft/OneDrive. Depois:

```powershell
python -m venv .venv
.venv/Scripts/Activate.ps1
pip install -r backend/requirements.txt
cd backend
python -m app.services.sync
python -m uvicorn app.main:app --host 127.0.0.1 --port 8876
```

Abra http://127.0.0.1:8876. O frontend usa a API no mesmo domínio; `frontend/js/config.js` deve manter `API_BASE_URL` vazio.

## Catálogo e atualização

Dentro de `backend`, execute `python -m app.services.sync` para atualizar o índice. A varredura pagina todas as subpastas autorizadas e só substitui o arquivo após concluir sem falhas. O servidor recarrega o índice atualizado automaticamente. A atualização após a primeira carga é manual nesta versão.

Arquivos são agrupados pelas pastas e códigos existentes. Códigos iguais em linhas distintas não são mesclados. Coleções sem código continuam como coleções; EANs ausentes não são inventados. Novidades considera a alteração dos arquivos. Mais acessados conta aberturas no portal, sem identificar visitantes; não mede visitantes únicos.

O índice e as contagens ficam em `backend/data/private/`, ignorado pelo Git e pelo build Docker. Links temporários são resolvidos pelo backend e não persistidos. Downloads aceitam apenas IDs indexados. Logs e atalhos Windows não integram o catálogo. Alguns formatos de materiais exigem aplicativo compatível para visualização.

## Validação

Na pasta `backend`: `python -m unittest discover -s tests -v`. Os testes usam dados de exemplo isolados. Na raiz: `docker build -t lider-midias:coolify .`.

## Estrutura

- `frontend/`: interface e logo oficial.
- `backend/app/`: API, busca e cliente Graph.
- `backend/app/services/sync.py`: sincronização do catálogo.
- `backend/tests/`: testes sem chamadas reais ao Graph.
- `Dockerfile`, `deploy/start.sh`: execução no Coolify.
- `render.yaml`: configuração antiga do Render, não usada no Coolify.

## API

`GET /health`, `GET /api/search?q=...&offset=0&limit=24`, `GET /api/products/{id}`, `GET /api/products/{id}/media`, `GET /api/categories`, `GET /api/latest`, `POST /api/products/{id}/view` e `GET /api/media/{id}/{thumbnail|content|download}`.

O portal ainda não possui login próprio. Quem tiver acesso ao endereço pode consultar e baixar o catálogo. Para uso restrito, configure a proteção de acesso no proxy antes de liberar o domínio. A permissão somente leitura do Microsoft Graph continua valendo independentemente disso.
