from fastapi import APIRouter, HTTPException, Query
from app.services.index import index
router = APIRouter(prefix='/api')
@router.get('/search')
def search(q: str = Query('', max_length=200)):
    return {'query':q, 'results':index.search(q)}
@router.get('/categories')
def categories():
    return sorted({p['category'] for p in index.products})
@router.get('/latest')
def latest():
    return sorted(index.products, key=lambda p:p['updated_at'], reverse=True)
@router.get('/products/{code}')
def product(code: str):
    result = index.get(code)
    if not result:
        raise HTTPException(404, 'Produto não encontrado')
    return result
@router.get('/products/{code}/media')
def media(code: str):
    p = product(code)
    return {'images':p['images'], 'videos':p['videos']}
