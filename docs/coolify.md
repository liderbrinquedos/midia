# Deploy no Coolify com Docker Compose

## Corrigir o erro do deploy anterior

O log mostrou que o Coolify executou `docker compose -f render.yaml build`. `render.yaml` é uma configuração do Render, não um Compose, daí o erro `services must be a mapping`. Selecione o novo arquivo abaixo; o Dockerfile continua sendo usado pelo Compose para construir a imagem.

## Campos no Coolify

1. Repositório: `liderbrinquedos/midia`, branch `main`.
2. Build Pack: **Docker Compose**.
3. Base Directory: `/`.
4. Docker Compose Location: `/docker-compose.yml` (substitua `/render.yaml`).
5. Salve e recarregue a definição Compose pelo painel, se solicitado.
6. Em **Domains for portal**, informe `https://midias.liderbrinquedos.com.br:8000` (ou o domínio escolhido com `:8000`). No Coolify, essa porta indica o destino interno do proxy; visitantes usam HTTPS normal, sem a porta no endereço.
7. Configure as variáveis abaixo e execute Deploy.

Não adicione comandos de build/start, portas públicas ou labels manuais de proxy. O Compose expõe a porta interna 8000; o Coolify configura o acesso pelo domínio. O frontend e a API ficam juntos, com API_BASE_URL vazio.

## Variáveis de runtime

Copie do `.env` local para Environment Variables do Coolify:

- `MICROSOFT_TENANT_ID`
- `MICROSOFT_CLIENT_ID`
- `MICROSOFT_CLIENT_SECRET` (valor do segredo válido, marcado como secreto)
- `ONEDRIVE_DRIVE_ID`
- `ONEDRIVE_ROOT_ITEM_ID`
- `CORS_ORIGINS=https://midias.liderbrinquedos.com.br` (sem `:8000`; ajuste ao domínio usado)

Não configure como Build Variables. O Compose permite construir a imagem sem credenciais, mas a primeira sincronização exige os cinco valores Microsoft/OneDrive. MEDIA_INDEX_PATH já é fixado no caminho Linux correto; não copie o caminho Windows.

## Volume persistente

O Compose cria o volume nomeado `midias-data` e monta em `/app/backend/data/private`. O Coolify/Docker pode prefixar o nome para isolar a aplicação. Ele guarda o índice e as contagens de acessos. Não adicione outro volume no mesmo destino pelo painel e não exclua esse volume durante um redeploy. Use uma única instância e faça backup do volume.

Se já houver um volume com catálogo de uma implantação anterior, preserve-o antes de migrar. O volume novo começará com uma sincronização completa; contagens antigas não são copiadas automaticamente.

## Primeira inicialização

Sem índice no volume, o contêiner lê as subpastas autorizadas do OneDrive antes de iniciar a API. Os logs mostram o avanço por pastas e arquivos. Aguarde alguns minutos; o health check tem tolerância inicial de 600 segundos. Se a sincronização falhar, confira as variáveis e a autorização da pasta. Um volume com índice existente permite inicialização imediata nos próximos deploys.

Após subir, confira `/health`, a indicação `ONEDRIVE · CATÁLOGO REAL`, busca por código, miniatura e download. Configure o DNS do domínio para o proxy Coolify. O portal não tem login próprio; para uso restrito, configure proteção no proxy antes de disponibilizá-lo.

## Atualizar o catálogo

No terminal do serviço `portal`, execute uma sincronização por vez:

```sh
cd /app/backend
python -m app.services.sync --output /app/backend/data/private/media_index.json
```

O índice completo substitui o anterior de forma atômica e é recarregado automaticamente. A sincronização recorrente ainda não está agendada. Não use `docker compose down -v`: isso apaga o volume e as contagens.

## Validar o Compose sem expor segredos

```sh
docker compose --env-file .env.example config --quiet
docker compose --env-file .env.example build
```

Referências oficiais: [Docker Compose](https://coolify.io/docs/applications/builds/docker-compose) e [domínios](https://coolify.io/docs/core/networking/domains).
