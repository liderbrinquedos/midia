"""Server-only Microsoft Graph client. No tokens or temporary URLs are persisted."""
import asyncio
import os
import time
from urllib.parse import quote, urlparse
import httpx
from app import config

class GraphError(Exception):
    def __init__(self, status=502):
        self.status = status
        super().__init__(f'Microsoft Graph unavailable (HTTP {status})')

class OneDriveService:
    def __init__(self, tenant=None, client_id=None, secret=None, drive=None, root=None, transport=None):
        self.tenant = tenant or os.getenv('MICROSOFT_TENANT_ID', '')
        self.client_id = client_id or os.getenv('MICROSOFT_CLIENT_ID', '')
        self.secret = secret or os.getenv('MICROSOFT_CLIENT_SECRET', '')
        self.drive = drive or os.getenv('ONEDRIVE_DRIVE_ID', '')
        self.root = root or os.getenv('ONEDRIVE_ROOT_ITEM_ID', '')
        self.http = httpx.AsyncClient(timeout=45, transport=transport)
        self._token = ''
        self._expiry = 0
        self._lock = asyncio.Lock()

    async def __aenter__(self): return self
    async def __aexit__(self, *args): await self.http.aclose()

    async def token(self):
        async with self._lock:
            if self._token and time.monotonic() < self._expiry: return self._token
            if not all([self.tenant, self.client_id, self.secret, self.drive, self.root]): raise GraphError(503)
            try:
                r = await self.http.post(f'https://login.microsoftonline.com/{quote(self.tenant, safe="")}/oauth2/v2.0/token', data={
                    'client_id':self.client_id, 'client_secret':self.secret,
                    'grant_type':'client_credentials', 'scope':'https://graph.microsoft.com/.default'})
            except httpx.HTTPError: raise GraphError() from None
            if r.status_code != 200: raise GraphError(r.status_code)
            data = r.json()
            self._token = data['access_token']
            self._expiry = time.monotonic() + max(0,int(data.get('expires_in',3600))-90)
            return self._token

    async def get(self, path, params=None):
        url = path if path.startswith('https://') else 'https://graph.microsoft.com/v1.0/' + path.lstrip('/')
        parsed = urlparse(url)
        if parsed.scheme != 'https' or parsed.netloc != 'graph.microsoft.com' or not parsed.path.startswith('/v1.0/'):
            raise GraphError(502)
        for attempt in range(5):
            try: r = await self.http.get(url,params=params,headers={'Authorization':'Bearer '+await self.token()})
            except httpx.HTTPError:
                if attempt == 4: raise GraphError() from None
                await asyncio.sleep(2 ** attempt);continue
            if r.status_code == 401 and attempt == 0:
                self._expiry=0;continue
            if r.status_code in [429,500,502,503,504] and attempt < 4:
                try: delay=float(r.headers.get('Retry-After',2**attempt))
                except ValueError: delay=2**attempt
                await asyncio.sleep(min(60,max(1,delay)));continue
            if r.status_code != 200: raise GraphError(r.status_code)
            return r.json()
        raise GraphError()

    def item_path(self, item_id):
        return f'drives/{quote(self.drive, safe="")}/items/{quote(item_id, safe="")}'

    async def children(self, item_id):
        url=self.item_path(item_id)+'/children'
        params={'$select':'id,name,file,folder,size,lastModifiedDateTime,parentReference,remoteItem','$top':'200'}
        values=[];seen=set()
        while url:
            if url in seen: raise GraphError()
            seen.add(url)
            data=await self.get(url,params)
            values.extend(data.get('value',[]))
            url=data.get('@odata.nextLink');params=None
        return values

    async def item(self,item_id): return await self.get(self.item_path(item_id))
    async def thumbnail(self,item_id):
        data=await self.get(self.item_path(item_id)+'/thumbnails')
        values=data.get('value',[])
        return values[0].get('medium',{}).get('url') if values else None
