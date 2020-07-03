from django.core.files.storage import FileSystemStorage
from app.settings import MEDIA_ROOT
from pathlib import Path
import shutil
import os


class MediaStorage:
    """Управляет файлами в медиа-хранилище на сервере"""

    storage = Path(MEDIA_ROOT, 'core/storage')
    file_system = FileSystemStorage(location=storage)

    @classmethod
    def save_file(cls, request):
        file = request.FILES['file']
        file_name = cls.file_system.save(file.name, file)
        file_url = cls.file_system.path(file_name)
        return file_url

    @classmethod
    def delete_file(cls, file_url):
        cls.file_system.delete(file_url)

    @classmethod
    def clean_directory(cls, path=storage):
        for root, dirs, files in os.walk(path):
            for f in files:
                os.unlink(os.path.join(root, f))
            for d in dirs:
                shutil.rmtree(os.path.join(root, d))
