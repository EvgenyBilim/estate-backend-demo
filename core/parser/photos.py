from app.settings import MEDIA_ROOT
from pathlib import Path
from core.parser.utils import get_id_from_name, delete_space_in_name, resize_to_preview,\
    save_full_size


class PhotoParser:
    """
    Парсер для фотогалерей жилих комплексов. Парсит ранее загруженный и распакованный
    архив, ресайзит фото для каждой из галерей и раскидывает фото по папкам галерей.
    """

    photos = Path(MEDIA_ROOT, r'core/photos')
    storage = Path(MEDIA_ROOT, r'core/storage')
    galleries = ['preview_285', 'preview_531', 'resize', 'full']

    def parse(self, archive_dir):
        """Итерируется по фото, при каждой итерации вызывает метод create"""

        archive = Path(archive_dir).iterdir()

        for home_dir in archive:
            for photo in home_dir.iterdir():
                self.create(home_dir.name, photo)

    def create(self, home_name, photo):
        """
        У нас есть 4 галереи с разным размером фото. Для каждой из галарей
        есть своя директория. Этот метод создает внтури каждой из этих директорий
        папку (если ее еще нет), чье название соответствует id дома и вызывает метод write
        """

        for gallery_name in self.galleries:
            home_id = get_id_from_name(home_name)
            home_path = Path(self.photos, gallery_name, home_id)

            try:
                Path.mkdir(home_path)
            except FileExistsError:
                pass

            self.write(gallery_name, home_path, photo)

    @staticmethod
    def write(gallery_name, path_to_save, photo):
        """
        Делает нужный ресайз фото в зависимости от параметра gallery_name
        и сохраняет фото в директории соответствующей галереи
        """

        name = Path(path_to_save, photo.name)
        name = delete_space_in_name(name)

        # TODO: Переименовать поля, чтобы не было размеров в названиях
        if gallery_name == 'preview_285':
            resize_to_preview(photo, name, 1.4, 294, 210)

        if gallery_name == 'preview_531':
            resize_to_preview(photo, name, 1.6, 480, 300)

        if gallery_name == 'resize':
            resize_to_preview(photo, name, 1.35, 567, 420)

        if gallery_name == 'full':
            save_full_size(photo, name)
