from core.models import Home, Block, Plan, PhotoGallery, MetroStation, ShortPlan, \
    MetroLine, Lead, Category, SubCategory
from app.settings import MEDIA_ROOT, EMAIL_HOST_USER, EMAIL_RECIPIENT_LIST
from core.parser.photos import PhotoParser
from core.storage import MediaStorage
from pathlib import Path
import shutil
import patoolib
import os
from django.db import connection
from core.uploader.uploader import Uploader
from django.core.mail import send_mail
from django.template.loader import get_template


class UploadManager(MediaStorage):
    """Прослайка для управления загрузками из xls-файлов"""

    # Загружает дома
    def upload_homes(self, xls_url):
        # очищаем дома и категории домов
        Home.objects.all().delete()
        Category.objects.all().delete()
        SubCategory.objects.all().delete()

        # получаем маппинг линий метро {станция: линия} для записи в Home
        metro_lines = MetroStation.get_metro_lines_mapping()

        # загружаем xls в Home
        Uploader(Home, xls_url, 'homes', 2, metro_lines).upload()

        # удаляем xls из хранилища
        self.delete_file(xls_url)

    # Загружает планировки с корпусами
    def upload_plans(self, xls_url):
        # очищаем таблицы Block, Plan и ShortPlan
        Block.objects.all().delete()
        ShortPlan.objects.all().delete()

        # загружаем xls в Block
        Uploader(Block, xls_url, 'blocks').upload()

        # загружаем xls в Plan
        blocks_dates = Block.get_block_date_mapping()
        Uploader(Plan, xls_url, 'plans', 2, blocks_dates).upload()

        # записываем короткие планировки ShortPlan
        short_plans = Plan.get_home_rooms_json()
        ShortPlan.write(short_plans)

        # записываем вычисляемые данные в Home
        block_storage = Block.get_home_date_mapping()
        block_counts = Block.get_home_block_mapping()
        plans_storage = Plan.get_home_plans_json()
        short_plan_storage = ShortPlan.get_price_set()
        Home.write_calculated_data(block_storage, block_counts, plans_storage, short_plan_storage)

        # удаляем xls из хранилища
        self.delete_file(xls_url)

    # Загружает категории домов
    def upload_category(self, xls_url):
        # очищаем таблицы с категориями и подкатегориями
        Category.objects.all().delete()
        SubCategory.objects.all().delete()

        # загружаем категории и подкатегории
        Uploader(Category, xls_url, 'categories').upload()
        Uploader(SubCategory, xls_url, 'subcategories').upload()

        # загружаем связи категорий с домами
        Uploader(SubCategory, xls_url, 'mapping', 2, Home).upload_many()

        self.delete_file(xls_url)

    # Загружает станции и линии метро
    def upload_metro(self, xls_url):
        MetroLine.objects.all().delete()
        Uploader(MetroLine, xls_url, 'lines').upload()
        Uploader(MetroStation, xls_url, 'stations').upload()
        self.delete_file(xls_url)

    # Удаляет все дома с корпусами, планировками, галереями и категориями
    @staticmethod
    def delete_homes():
        Home.objects.all().delete()
        Category.objects.all().delete()
        PhotoManager().remove_gallery()

    # Удаляет все станции и линии метро
    @staticmethod
    def delete_metro():
        MetroLine.objects.all().delete()


class PhotoManager(MediaStorage):
    """Прослойка для управления загрузкой фото"""

    photo_storage = Path(MEDIA_ROOT, 'core/photos')

    # Загружает фото в галереи и превью
    def upload_photos(self, rar_file_url):
        # очищаем папки галерей
        self.remove_gallery()

        # распаковываем архив
        unpacked_url = self.unpack_photo_archive(rar_file_url)

        # раскидываем фотки по папкам
        PhotoParser().parse(unpacked_url)

        # пишем адреса фоток в таблицы бд
        PhotoGallery.write_photos_url()
        Home.write_preview_url(PhotoGallery)

        # очищаем папку storage (папка и архив)
        self.clean_directory(self.storage)

    # Очищает папки галерей и url к фото в таблицах
    def remove_gallery(self):
        for path in self.photo_storage.iterdir():
            self.clean_directory(path)
        PhotoGallery.remove_all()
        Home.write_preview_url(PhotoGallery)

    # Распаковывает rar-архив, возвращает url распакованной папки
    def unpack_photo_archive(self, rar_url):
        archive_dir = Path(self.storage, r'archive')
        try:
            os.mkdir(archive_dir)
        except FileExistsError:
            self.clean_directory(archive_dir)
        patoolib.extract_archive(rar_url, outdir=archive_dir)
        return archive_dir

    # Создает zip-архив со структурой папок с домами
    def create_empty_photo_archive(self):
        archive_dir = Path(self.storage, r'archive')
        self.clean_directory(self.storage)
        Path.mkdir(archive_dir)

        for home in Home.objects.all():
            dir_name = Path(archive_dir, r'{} ({})'.format(home.name, home.id))
            Path.mkdir(dir_name)

        archive = shutil.make_archive(archive_dir, 'zip', archive_dir)
        archive_url = os.path.abspath(archive)
        shutil.rmtree(archive_dir)
        return archive_url


# TODO: Вынести в отдельное приложение
class LeadManager:
    """Прослайка для управления лидами с сайта"""

    def __init__(self, page, form_name, phone):
        self.page = page
        self.form_name = form_name
        self.phone = phone

    @classmethod
    def create(cls, page, form_name, phone):
        lead = cls(page=page, form_name=form_name, phone=phone)
        lead.save()
        lead.send_to_mail()
        return True

    def save(self):
        Lead.objects.create(page=self.page, form_name=self.form_name, phone=self.phone)

    def send_to_mail(self):
        send_mail(
            'Новая заявка',
            'message',
            EMAIL_HOST_USER,
            EMAIL_RECIPIENT_LIST,
            fail_silently=False,
            html_message=get_template('core/lead_message.html').render({
                'page': self.page,
                'form_name': self.form_name,
                'phone': self.phone,
            })
        )
