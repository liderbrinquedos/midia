"""Recursive read-only sync. Publish a new index only after a complete traversal."""
import argparse
import asyncio
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
from app.config import ROOT
from app.services.onedrive import OneDriveService

IMAGE_EXT={'.jpg','.jpeg','.png','.webp','.gif','.bmp','.tif','.tiff','.heic','.avif'}
VIDEO_EXT={'.mp4','.mov','.webm','.avi','.m4v','.mkv','.wmv'}
DOC_EXT={'.rar','.psb','.pdf','.psd','.ai','.eps','.cdr','.svg','.zip','.docx','.xlsx','.pptx'}
CODE=re.compile(r'^(PET[ -]?\d+|\d{3,6})(?=[\s_\-–.]|$)',re.I)

def identity(label):
    match=CODE.match(label.strip())
    if match and match.group(1) not in {'2023','2024','2025','2026'}:
        code=re.sub(r'[ -]','',match.group(1)).upper()
        name=label[match.end():].strip(' _-–.') or label
        return code,name
    return '',label

def media_type(name):
    ext=Path(name).suffix.lower()
    return 'images' if ext in IMAGE_EXT else 'videos' if ext in VIDEO_EXT else 'documents' if ext in DOC_EXT else None

def build_catalog(items):
    groups={};unmatched=[];skipped=Counter()
    def add(item,key,code,name,branch,line):
        pid=hashlib.sha256(key.encode()).hexdigest()[:20]
        p=groups.setdefault(key,dict(id=pid,code=code,name=name,category=branch.replace('Banco de Imagens - ',''),line=line,
            reference=code,ean='',description='',updated_at='',images=[],videos=[],documents=[],views=0))
        kind=media_type(item['name'])
        mid=item['id'];prefix='/api/media/'+mid
        p[kind].append(dict(id=mid,type=kind,file=item['name'],size=item.get('size',0),
            mime_type=item.get('file',{}).get('mimeType','application/octet-stream'),
            thumbnail=prefix+'/thumbnail',url=prefix+'/content',download=prefix+'/download',
            onedrive_path='/'.join(item['path']+[item['name']]),updated_at=item.get('lastModifiedDateTime','')))
        p['updated_at']=max(p['updated_at'],item.get('lastModifiedDateTime',''))
    for item in items:
        kind=media_type(item['name'])
        if not kind:
            skipped[Path(item['name']).suffix.lower() or '(sem extensão)']+=1;continue
        path=list(item['path'])
        while len(path)>1 and path[-1].upper() in {'PNG','PSD','JPG','JPEG','IMAGENS','FOTOS','VIDEOS','VÍDEOS'}: path.pop()
        branch=path[0] if path else 'Banco de mídias'
        # Nearest coded ancestor identifies the product; separate branches never merge by code alone.
        coded=[(i,identity(label)) for i,label in enumerate(path[1:],1) if identity(label)[0]]
        if coded:
            i,(code,name)=coded[-1];key='/'.join(path[:i+1]);line=path[1] if i>1 else branch.replace('Banco de Imagens - ','')
        else:
            code,name=identity(Path(item['name']).stem)
            if code and branch=='TODOS OS VIDEOS':
                unmatched.append((item,code,name));continue
            if code:
                key='/'.join(path)+'/'+code;line=path[-1] if len(path)>1 else ''
            else:
                key='/'.join(path) or 'Banco de mídias';name=path[-1] if path else 'Banco de mídias';line=path[1] if len(path)>2 else ''
        add(item,key,code,name,branch,line)
    for item,code,name in unmatched:
        matches=[key for key,p in groups.items() if p['code']==code]
        if len(matches)==1:
            p=groups[matches[0]];add(item,matches[0],code,p['name'],p['category'],p['line'])
        else:add(item,'TODOS OS VIDEOS/'+code,code,name,'TODOS OS VIDEOS','Vídeos')
    products=list(groups.values())
    for p in products:
        for kind in ['images','videos','documents']:
            p[kind].sort(key=lambda f:(Path(f['file']).suffix.lower() not in {'.jpg','.jpeg','.png','.webp'}, f['file'].casefold()))
    products.sort(key=lambda p:p['updated_at'],reverse=True)
    return dict(source='onedrive',synced_at=datetime.now(timezone.utc).isoformat(),products=products,
        stats={'products':len(products),'files':sum(len(p[k]) for p in products for k in ['images','videos','documents']),
               'ignored_extensions':dict(skipped)})

def save_catalog(path,catalog):
    if not catalog.get('products'): raise ValueError('Empty index refused; previous catalog preserved')
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(catalog,ensure_ascii=False),encoding='utf-8')
    os.replace(tmp,path)

async def scan(graph):
    pending=[(graph.root,[])];seen=set();items=[];folders=0
    while pending:
        batch=pending[:6];pending=pending[6:]
        results=await asyncio.gather(*(graph.children(i) for i,_ in batch))
        for (folder_id,path),children in zip(batch,results):
            if folder_id in seen: continue
            seen.add(folder_id);folders+=1
            for item in children:
                if item.get('remoteItem'): raise ValueError('Shortcut found: explicit scope review required')
                if 'folder' in item:
                    if item['id'] not in seen: pending.append((item['id'],path+[item['name']]))
                elif 'file' in item:
                    items.append({**item,'path':path})
        if folders%30<6: print(f'Scanned {folders} folders, {len(items)} files; {len(pending)} pending',flush=True)
    return items

async def run(output):
    async with OneDriveService() as graph:
        items=await scan(graph)
    catalog=build_catalog(items)
    save_catalog(output,catalog)
    print(json.dumps(catalog['stats'],ensure_ascii=True),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',default=str(ROOT/'backend/data/private/media_index.json'))
    args=parser.parse_args()
    asyncio.run(run(args.output))
