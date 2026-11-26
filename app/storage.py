import mimetypes
import os
import uuid
from urllib.parse import quote

from django.conf import settings
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


@deconstructible
class SupabaseStorage(Storage):
    def __init__(self):
        self.bucket = settings.SUPABASE_BUCKET

    def _bucket(self):
        chave = os.environ.get("SUPABASE_SERVICE_KEY")
        if chave:
            from supabase import create_client
            cliente = create_client(os.environ["SUPABASE_URL"], chave)
        else:
            from .supabase_client import supabase as cliente
        return cliente.storage.from_(self.bucket)

    def get_available_name(self, name, max_length=None):
        pasta, arquivo = os.path.split(name)
        base, extensao = os.path.splitext(arquivo)
        novo = f"{base}_{uuid.uuid4().hex[:8]}{extensao}".lower()
        return f"{pasta}/{novo}" if pasta else novo

    def _save(self, name, content):
        if hasattr(content, "seek"):
            content.seek(0)
        dados = content.read()
        tipo = getattr(content, "content_type", None) or mimetypes.guess_type(name)[0] or "application/octet-stream"
        self._bucket().upload(name, dados, {"content-type": tipo})
        return name

    def exists(self, name):
        return False

    def delete(self, name):
        if name:
            try:
                self._bucket().remove([name])
            except Exception:
                pass

    def url(self, name):
        base = os.environ["SUPABASE_URL"].rstrip("/")
        return f"{base}/storage/v1/object/public/{self.bucket}/{quote(name)}"

    def size(self, name):
        return 0
