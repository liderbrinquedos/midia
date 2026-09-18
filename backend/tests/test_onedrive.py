import asyncio
import json
import tempfile
import unittest
from pathlib import Path
import httpx
from app.services.onedrive import OneDriveService, GraphError
from app.services.sync import build_catalog, save_catalog

class GraphTests(unittest.IsolatedAsyncioTestCase):
    async def test_pagination_and_token_reuse(self):
        calls=[]
        def handle(request):
            calls.append(request)
            if request.url.host == 'login.microsoftonline.com':
                return httpx.Response(200,json={'access_token':'test-token','expires_in':3600})
            self.assertEqual(request.headers['authorization'],'Bearer test-token')
            if 'page=2' in str(request.url):
                return httpx.Response(200,json={'value':[{'id':'b'}]})
            return httpx.Response(200,json={'value':[{'id':'a'}],'@odata.nextLink':'https://graph.microsoft.com/v1.0/drives/drive/items/root/children?page=2'})
        async with OneDriveService('tenant','client','secret','drive','root',transport=httpx.MockTransport(handle)) as graph:
            self.assertEqual([x['id'] for x in await graph.children('root')],['a','b'])
        self.assertEqual(sum(r.url.host=='login.microsoftonline.com' for r in calls),1)

    async def test_rejects_untrusted_pagination(self):
        def handle(request):
            if request.url.host=='login.microsoftonline.com':
                return httpx.Response(200,json={'access_token':'token','expires_in':3600})
            return httpx.Response(200,json={'value':[], '@odata.nextLink':'https://evil.example/steal'})
        async with OneDriveService('tenant','client','secret','drive','root',transport=httpx.MockTransport(handle)) as graph:
            with self.assertRaises(GraphError): await graph.children('root')

class CatalogTests(unittest.TestCase):
    def item(self,id,name,path,mime='image/jpeg'):
        return {'id':id,'name':name,'path':path,'file':{'mimeType':mime},'lastModifiedDateTime':'2026-09-18T00:00:00Z','size':20}

    def test_groups_views_and_matches_unique_video(self):
        catalog=build_catalog([
            self.item('a','frente.jpg',['Banco de Imagens - Lider Brinquedos','Disney','1234 Caminhão']),
            self.item('b','lateral.jpg',['Banco de Imagens - Lider Brinquedos','Disney','1234 Caminhão','Imagens']),
            self.item('v','1234-CAMINHAO.mp4',['TODOS OS VIDEOS'],'video/mp4')])
        self.assertEqual(len(catalog['products']),1)
        p=catalog['products'][0]
        self.assertEqual(p['code'],'1234')
        self.assertEqual(len(p['images']),2)
        self.assertEqual(len(p['videos']),1)
        self.assertEqual(p['ean'],'')
        self.assertNotIn('downloadUrl',json.dumps(catalog))

    def test_duplicate_codes_in_different_branches_do_not_merge(self):
        catalog=build_catalog([
            self.item('a','a.jpg',['Banco de Imagens - Apolo','1234 Bola']),
            self.item('b','b.jpg',['Banco de Imagens - Lider Brinquedos','1234 Boneco']),
            self.item('v','1234-video.mp4',['TODOS OS VIDEOS'],'video/mp4')])
        self.assertEqual(len(catalog['products']),3)
        self.assertEqual(len({p['id'] for p in catalog['products']}),3)

    def test_ignores_logs_and_keeps_documents(self):
        catalog=build_catalog([self.item('log','debug.log',['Pasta'],'text/plain'),self.item('pdf','catalogo.pdf',['Pasta'],'application/pdf')])
        self.assertEqual(len(catalog['products']),1)
        self.assertEqual(len(catalog['products'][0]['documents']),1)

    def test_atomic_write_preserves_previous_on_invalid_input(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'index.json';path.write_text('previous')
            with self.assertRaises(ValueError): save_catalog(path,{'products':[]})
            self.assertEqual(path.read_text(),'previous')
