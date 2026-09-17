"""Integration intentionally disabled until Microsoft configuration is approved.
Future adapter: acquire server-side token, enumerate configured drive root,
paginate children and update the index through an independent sync job.
Never persist expiring Graph download URLs as permanent links.
"""
import os

class OneDriveService:
    def __init__(self):
        self.tenant_id = os.getenv('MICROSOFT_TENANT_ID', '')
        self.client_id = os.getenv('MICROSOFT_CLIENT_ID', '')
        self.client_secret = os.getenv('MICROSOFT_CLIENT_SECRET', '')
        self.drive_id = os.getenv('ONEDRIVE_DRIVE_ID', '')
    async def list_children(self):
        raise RuntimeError('Microsoft Graph ainda não habilitado: aguarda configuração e aprovação.')
