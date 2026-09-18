from urllib.parse import quote, urlparse
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse, StreamingResponse
import httpx
from app.services.index import index, public, views
from app.services.onedrive import OneDriveService, GraphError
router = APIRouter(prefix='/api')
graph = OneDriveService()

@router.get('/search')
def search(q: str = Query('', max_length=200), offset: int = Query(0,ge=0), limit: int = Query(24,ge=1,le=100), sort: str = Query('recent',pattern='^(recent|name|popular)$')):
    items=index.search(q)
    if sort=='popular':
        counts=views()
        items=sorted([p for p in items if counts.get(p['id'],0)>0],key=lambda p:counts[p['id']],reverse=True)
    else: items=sorted(items,key=lambda p:p['name'].casefold() if sort=='name' else p['updated_at'],reverse=sort=='recent')
    return {'query':q,'results':[public(p) for p in items[offset:offset+limit]],'total':len(items),'offset':offset,'limit':limit,'source':index.meta.get('source'),'synced_at':index.meta.get('synced_at')}
@router.get('/categories')
def categories(): return sorted({p['category'] for p in index.products})
@router.get('/latest')
def latest(): return [public(p) for p in sorted(index.products,key=lambda p:p['updated_at'],reverse=True)[:24]]
@router.get('/products/{code}')
def product(code: str):
    result=index.get(code)
    if not result: raise HTTPException(404,'Produto não encontrado')
    return public(result)
@router.post('/products/{code}/view')
def register_view(code: str):
    p=product(code)
    views(p['id'])
    return {'ok':True}
@router.get('/products/{code}/media')
def media(code: str):
    p=product(code)
    return {k:p[k] for k in ['images','videos','documents']}

@router.get('/media/{item_id}/{action}')
async def file(item_id: str, action: str):
    index.reload()
    f=index.files.get(item_id)
    if not f or action not in ['thumbnail','content','download']: raise HTTPException(404,'Arquivo não encontrado')
    try:
        if action=='thumbnail': url=await graph.thumbnail(item_id)
        else: url=(await graph.item(item_id)).get('@microsoft.graph.downloadUrl')
    except GraphError: raise HTTPException(503,'OneDrive indisponível. Tente novamente.') from None
    if not url or urlparse(url).scheme!='https': raise HTTPException(404,'Prévia indisponível')
    if action!='download': return RedirectResponse(url,headers={'Cache-Control':'private, max-age=60'})
    # No bearer token is forwarded to the temporary SharePoint URL.
    client=httpx.AsyncClient(timeout=60,follow_redirects=True)
    try:
        response=await client.send(client.build_request('GET',url),stream=True)
        response.raise_for_status()
    except httpx.HTTPError:
        await client.aclose()
        raise HTTPException(503,'Não foi possível baixar o arquivo') from None
    async def chunks():
        try:
            async for chunk in response.aiter_bytes(): yield chunk
        finally:
            await response.aclose()
            await client.aclose()
    return StreamingResponse(chunks(),media_type=f.get('mime_type') or 'application/octet-stream',headers={'Content-Disposition':"attachment; filename*=UTF-8''"+quote(f['file'],safe=''),'Cache-Control':'no-store'})
