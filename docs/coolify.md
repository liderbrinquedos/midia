# Deploy no Coolify pelo GitHub

## Aplicação

1. Crie uma aplicação a partir do repositório `liderbrinquedos/midia`. Se privado, selecione a conexão GitHub que tem acesso a ele.
2. Selecione a branch `main` e Build Pack **Dockerfile**.
3. Base Directory: `/`. Dockerfile Location: `/Dockerfile`.
4. Ports Exposes: `8000`. Não configure comando de build/start adicional: o Dockerfile já define a execução.
5. Domínio: o endereço HTTPS escolhido para o portal (por exemplo, `https://midias.liderbrinquedos.com.br`). O DNS precisa apontar para o servidor/proxy Coolify. Faça a troca de DNS quando o deploy estiver validado.

Frontend e API usam o mesmo domínio. Mantenha `frontend/js/config.js` com API_BASE_URL vazio.

## Variáveis de ambiente

Cadastre como variáveis **de runtime**, não Build Variables:

| Nome | Valor |
| --- | --- |
| MICROSOFT_TENANT_ID | ID do diretório Microsoft já configurado |
| MICROSOFT_CLIENT_ID | ID do aplicativo já autorizado |
| MICROSOFT_CLIENT_SECRET | Valor do segredo válido, marcado como secreto |
| ONEDRIVE_DRIVE_ID | ID do drive autorizado |
| ONEDRIVE_ROOT_ITEM_ID | ID da pasta raiz autorizada |
| CORS_ORIGINS | Domínio HTTPS do portal |

Copie os cinco valores do `.env` local para o painel. Não copie MEDIA_INDEX_PATH do Windows. O contêiner já usa `/app/backend/data/private/media_index.json`. Não são necessárias variáveis públicas de frontend nem credenciais durante o build.

## Persistência — antes do primeiro deploy

Em Persistent Storage, adicione um **volume nomeado**:

- Nome sugerido: `lider-midias-data`.
- Destination Path: `/app/backend/data/private`.

O volume guarda `media_index.json` e `views.sqlite3`. Use uma instância/réplica. Faça backup do volume no Coolify. Prefira volume nomeado; um bind mount vazio do host exige permissão de escrita para UID/GID `10001:10001`.

## Deploy e primeira carga

Clique em Deploy. Sem índice no volume, o contêiner sincroniza o OneDrive antes de iniciar a API. Os logs mostram a quantidade de pastas e arquivos lidos, sem imprimir credenciais. Aguarde alguns minutos. Se a sincronização falhar, a inicialização falha explicitamente; confira as variáveis e a autorização da pasta nos logs.

O Dockerfile inclui health check em `/health`, porta 8000, com tolerância inicial de 600 segundos. O Coolify usa o HEALTHCHECK da imagem. Se o servidor precisar de mais tempo para a primeira carga, aumente o limite de espera do deploy. Em novos deploys, o volume preservado evita repetir a primeira carga.

## Conferência

- `/health` retorna `{"status":"ok"}`.
- A página mostra `ONEDRIVE · CATÁLOGO REAL`.
- Busque um código real e abra uma foto.
- Confirme o download do original.
- Reinicie a aplicação e confira se catálogo e Mais acessados foram preservados.

O portal não tem login próprio. Para restringir o público, configure a proteção no proxy antes de disponibilizar o endereço. Permissão de leitura no OneDrive não funciona como login para os visitantes do portal.

## Atualizar o catálogo

No terminal da aplicação Coolify, execute uma única sincronização por vez:

```sh
cd /app/backend
python -m app.services.sync --output /app/backend/data/private/media_index.json
```

O servidor recarrega automaticamente o índice completo. Uma falha preserva o catálogo anterior. A sincronização recorrente ainda não está agendada. Atualizações de código vêm do Git: use Redeploy após o push ou habilite auto-deploy pela integração GitHub do Coolify.

## Referências

- https://coolify.io/docs/applications/builds/dockerfile
- https://coolify.io/docs/applications/configuration/health-checks
- https://coolify.io/docs/core/persistent-storage/storage-mounts/overview
