from django.db import models
from core.utils.mapping import WALL_TYPE, TRIM_SHORT, TRIM_FULL, ROOM_SHORT, ROOM_MIDDLE, ROOM_FULL
from app.settings import MEDIA_ROOT, SITE_URL
from pathlib import Path
from django.db import connection
from core.utils.models_utils import wrap_homes_description, delivery_date_to_string, \
    rooms_mapping, trim_mapping, floors_parser, price_to_short, details_metro_distance, \
    calc_sort_metro_distance, details_delivery, calc_min_date, get_text_plans_count, \
    trim_details, get_payment, min_max_price, get_price_set, get_metro_line, \
    get_preview_photo_url, get_preview_plug_url, set_number_for_photo, get_banks, get_text_blocks_count


class Home(models.Model):
    """Модель жилого комплекса. Данные парсятся из xls-файла."""

    id = models.IntegerField(primary_key=True, unique=True)
    sort_order = models.IntegerField(unique=True, null=True)
    name = models.CharField(max_length=128, unique=True, null=True)
    page_url = models.CharField(max_length=128, unique=True, null=True)
    developer = models.CharField(max_length=64, null=True)
    tag_list = models.CharField(max_length=256, null=True)
    address = models.CharField(max_length=256, null=True)
    district = models.CharField(max_length=128, null=True)
    metro = models.CharField(max_length=64, null=True)
    metro_distance = models.CharField(max_length=5, null=True)
    wall_type = models.CharField(max_length=16, null=True)
    trim = models.CharField(max_length=16, null=True)
    agreement = models.CharField(max_length=16, null=True)
    description = models.CharField(max_length=10_000, null=True)
    wall_type_string = models.CharField(max_length=128, null=True)
    metro_distance_string = models.CharField(max_length=32, null=True)
    sort_metro_distance = models.IntegerField(unique=False, null=True)
    metro_line = models.CharField(max_length=1024, null=True)
    preview_285 = models.CharField(max_length=1024, null=True)
    preview_531 = models.CharField(max_length=1024, null=True)
    delivery_part = models.CharField(max_length=32, null=True)
    delivery_month = models.CharField(max_length=32, null=True)
    will_done_min = models.DateField(auto_now_add=False, null=True)
    plans_count = models.CharField(max_length=20, null=True)
    blocks_count = models.CharField(max_length=20, null=True)
    trim_full = models.CharField(max_length=256, null=True)
    trim_short = models.CharField(max_length=256, null=True)
    payment = models.CharField(max_length=1024, null=True)
    banks = models.CharField(max_length=1024, null=True)
    min_price = models.IntegerField(unique=False, null=True)
    max_price = models.IntegerField(unique=False, null=True)
    price_set = models.CharField(max_length=256, null=True)

    # Создает объект для записи из xls в Home
    @classmethod
    def create_obj_from_xls(cls, page, string, *args):
        wall_type = page['K' + string].value
        metro = page['I' + string].value
        metro_distance = page['J' + string].value
        metro_lines = args[0][0]

        obj = cls(
            id=page['A' + string].value,
            sort_order=page['B' + string].value,
            name=page['C' + string].value,
            page_url=page['D' + string].value,
            developer=page['E' + string].value,
            tag_list=page['F' + string].value,
            address=page['G' + string].value,
            district=page['H' + string].value,
            metro=metro,
            metro_distance=metro_distance,
            wall_type=wall_type,
            trim=page['L' + string].value,
            agreement=page['M' + string].value,
            description=wrap_homes_description(page['N' + string].value),
            wall_type_string=WALL_TYPE[wall_type],
            metro_distance_string=details_metro_distance(metro_distance),
            sort_metro_distance=calc_sort_metro_distance(metro_distance),
            metro_line=get_metro_line(metro_lines, metro, SITE_URL),
            preview_285=get_preview_plug_url('285', SITE_URL),
            preview_531=get_preview_plug_url('531', SITE_URL),
        )
        return obj

    # Вычисляет и пишет данные в Home
    @classmethod
    def write_calculated_data(cls, block_storage, block_counts, plan_storage, short_plan_storage):
        homes = cls.objects.all()

        for home in homes:
            home.delivery_part = details_delivery(block_storage, home.id, 'part')
            home.delivery_month = details_delivery(block_storage, home.id, 'year')
            home.will_done_min = calc_min_date(block_storage, home.id)
            home.plans_count = get_text_plans_count(plan_storage, home.id)
            home.blocks_count = get_text_blocks_count(block_counts, home.id)
            home.trim_full = trim_details(plan_storage, home.id, 'trim_full', home.trim)
            home.trim_short = trim_details(plan_storage, home.id, 'trim_short', home.trim)
            home.payment = get_payment(plan_storage, home.id)
            home.banks = get_banks(plan_storage, home.id)
            home.min_price = min_max_price(plan_storage, home.id, 'min')
            home.max_price = min_max_price(plan_storage, home.id, 'max')
            home.price_set = get_price_set(short_plan_storage, home.id)
            home.save()

    # Пишет url превьюшек в Home
    @classmethod
    def write_preview_url(cls, gallery):
        for home in cls.objects.all():
            home.preview_285 = get_preview_photo_url(gallery, home.id, '285', SITE_URL)
            home.preview_531 = get_preview_photo_url(gallery, home.id, '531', SITE_URL)
            home.save()


class Block(models.Model):
    """Модель корпуса жилого комплекса. Данные парсятся из xls-файла."""

    home = models.ForeignKey(Home, on_delete=models.CASCADE, null=True)
    home_name = models.CharField(max_length=128, null=True)
    number = models.CharField(max_length=24, null=True)
    will_done = models.DateField(auto_now_add=False, null=True)
    block_oid = models.CharField(primary_key=True, unique=True, max_length=32, default='')
    will_done_string = models.CharField(max_length=64, null=True)

    # Создает объект для записи из xls в Block
    @classmethod
    def create_obj_from_xls(cls, page, string, *args):
        obj = cls(
            home_id=page['A' + string].value,
            home_name=page['B' + string].value,
            number=page['C' + string].value,
            will_done=page['D' + string].value,
            block_oid=(str(page['A' + string].value) + str(page['C' + string].value)),
            will_done_string=delivery_date_to_string(page['D' + string].value),
        )
        return obj

    # Возвращает словарь {Дом: [Сроки сдачи]}, используется для записи даты в Home
    @classmethod
    def get_home_date_mapping(cls):
        mapping = {}
        for block in cls.objects.all():
            if block.home_id not in mapping:
                mapping.update({block.home_id: [block.will_done]})
            else:
                mapping[block.home_id].append(block.will_done)
        return mapping

    # Возвращает словарь {Корпус: Срок сдачи}, используется для записи даты в Plan
    @classmethod
    def get_block_date_mapping(cls):
        mapping = {}
        for block in cls.objects.all():
            mapping.update({block.block_oid: block.will_done_string})
        return mapping

    # Возвращает словарь {Дом: [Корпуса]}, используется для записи кол-ва корпусов в Home
    @classmethod
    def get_home_block_mapping(cls):
        mapping = {}
        for block in cls.objects.all():
            if block.home_id not in mapping:
                mapping.update({block.home_id: [block.block_oid]})
            else:
                mapping[block.home_id].append(block.block_oid)
        return mapping


class Plan(models.Model):
    """Модель планировки (квартиры) жилого комплекса. Данные парсятся из xls-файла."""

    home = models.ForeignKey(Home, on_delete=models.CASCADE, null=True)
    home_name = models.CharField(max_length=128, null=True)
    block_number = models.CharField(max_length=24, null=True)
    rooms = models.CharField(max_length=10, null=True)
    square_total = models.FloatField(null=True)
    square_kitchen = models.FloatField(null=True)
    trim = models.CharField(max_length=16, null=True)
    agreement = models.CharField(max_length=32, null=True)
    payment = models.CharField(max_length=64, null=True)
    banks = models.TextField(max_length=1024, null=True)
    roof_height = models.CharField(max_length=20, null=True)
    base_price = models.IntegerField(null=True)
    discount_price = models.IntegerField(null=True)
    floor = models.CharField(max_length=20, null=True)
    plan_img_url = models.CharField(max_length=256, null=True)
    block = models.ForeignKey(Block, on_delete=models.CASCADE, null=True)
    trim_full = models.CharField(max_length=128, null=True)
    trim_short = models.CharField(max_length=128, null=True)
    rooms_full = models.CharField(max_length=32, null=True)
    rooms_short = models.CharField(max_length=32, null=True)
    floor_number = models.IntegerField(null=True)
    floor_count = models.IntegerField(null=True)
    will_done_month = models.CharField(max_length=128, null=True)

    # Создает объект для записи из xls в Plan
    @classmethod
    def create_obj_from_xls(cls, page, string, *args):
        home_id = page['A' + string].value
        block_number = page['C' + string].value
        rooms = rooms_mapping(page['D' + string].value)
        trim = trim_mapping(page['G' + string].value)
        floor_full = page['P' + string].value
        floors = floors_parser(floor_full)
        floor_number = floors[0]
        floor_count = floors[1]
        blocks = args[0][0]

        obj = cls(
            home_id=home_id,
            home_name=page['B' + string].value,
            block_number=block_number,
            rooms=rooms,
            square_total=page['E' + string].value,
            square_kitchen=page['F' + string].value,
            trim=trim,
            agreement=page['H' + string].value,
            payment=page['I' + string].value,
            banks=page['K' + string].value,
            roof_height=page['L' + string].value,
            base_price=page['N' + string].value,
            discount_price=page['O' + string].value,
            floor=floor_full,
            plan_img_url=page['Q' + string].value,
            block_id=(str(page['A' + string].value) + str(page['C' + string].value)),
            trim_full=TRIM_FULL[trim],
            trim_short=TRIM_SHORT[trim],
            rooms_full=ROOM_FULL[rooms],
            rooms_short=ROOM_SHORT[rooms],
            floor_number=floor_number,
            floor_count=floor_count,
            will_done_month=blocks[str(home_id) + str(block_number)],
        )
        return obj

    # Возвращает словарь {Дом: {Тип квартиры: {цена, площадь}}}, для записи в ShortPlan
    @classmethod
    def get_home_rooms_json(cls):
        storage = {}

        # TODO: Переписать покороче
        for plan in cls.objects.all():
            if plan.home_id not in storage:
                storage.update({
                    plan.home_id: {
                        plan.rooms: {
                            'price': [plan.discount_price],
                            'square': [plan.square_total],
                        }
                    }
                })
            else:
                if plan.rooms not in storage[plan.home_id]:
                    storage[plan.home_id].update({
                        plan.rooms: {
                            'price': [plan.discount_price],
                            'square': [plan.square_total],
                        }
                    })
                else:
                    storage[plan.home_id][plan.rooms]['price'].append(plan.discount_price)
                    storage[plan.home_id][plan.rooms]['square'].append(plan.square_total)
        return storage

    # Возвращает словарь {Дом: {Планировка: {trim, pay, price}}}, для записи в Home
    @classmethod
    def get_home_plans_json(cls):
        storage = {}

        # TODO: Переписать покороче
        for plan in cls.objects.all():
            if plan.home_id not in storage:
                storage.update({
                    plan.home_id: {
                        plan.id: {
                            'trim_full': plan.trim_full,
                            'trim_short': plan.trim_short,
                            'payment': plan.payment,
                            'banks': plan.banks,
                            'price': plan.discount_price,
                        }
                    }
                })
            else:
                storage[plan.home_id].update({
                    plan.id: {
                        'trim_full': plan.trim_full,
                        'trim_short': plan.trim_short,
                        'payment': plan.payment,
                        'banks': plan.banks,
                        'price': plan.discount_price,
                    }
                })
        return storage


class ShortPlan(models.Model):
    """
    Модель для типов квартир по каждому жилому комплексу.
    Тип квартиры - это студии, однушки, двушки и т.д.
    Данные вычисляются при парсинге xls-файла.
    Используется для дальнейшего кеширования, чтобы не вычислять данные на лету.
    """

    home = models.ForeignKey(Home, on_delete=models.CASCADE, null=True)
    rooms = models.CharField(max_length=10, null=True)
    price_from = models.IntegerField(null=True)
    price_to = models.IntegerField(null=True)
    square_from = models.FloatField(null=True)
    square_to = models.FloatField(null=True)
    rooms_string = models.CharField(max_length=32, null=True)
    short_price_from = models.FloatField(null=True)
    short_price_to = models.FloatField(null=True)

    # Пишет данные в ShortPlan
    @classmethod
    def write(cls, homes):
        # homes = Plan.get_home_rooms_json()
        objects = []
        for home, rooms in homes.items():
            for room, values in rooms.items():
                obj = cls(
                    home_id=home,
                    rooms=room,
                    price_from=min(values['price']),
                    price_to=max(values['price']),
                    square_from=min(values['square']),
                    square_to=max(values['square']),
                    rooms_string=ROOM_MIDDLE[room],
                    short_price_from=price_to_short(min(values['price'])),
                    short_price_to=price_to_short(max(values['price'])),
                )
                objects.append(obj)
        cls.objects.bulk_create(objects)

    # Возвращает словарь {Дом: {Тип квартиры: {цена от, цена до}}}, для записи в Home
    @classmethod
    def get_price_set(cls):
        storage = {}
        for string in cls.objects.all():
            if string.home_id not in storage:
                storage.update({string.home_id: {string.rooms: string.price_from}})
            else:
                storage[string.home_id].update({string.rooms: string.price_from})
        return storage


class Category(models.Model):
    """
    Модель для категорий домов, которые отображаются на главной странице.
    Модель не содержит домов, а только подкатегории из модели SubCategory.
    Пример категорий - "Популярные запросы", "Популярные локации"
    """

    id = models.IntegerField(primary_key=True, unique=True)
    name = models.CharField(max_length=64, null=True)
    title = models.CharField(max_length=64, null=True)
    sort_order = models.IntegerField(unique=True, null=True)

    # Создает объект для записи из xls в Category
    @classmethod
    def create_obj_from_xls(cls, page, string, *args):
        obj = cls(
            id=page['A' + string].value,
            name=page['B' + string].value,
            title=page['C' + string].value,
            sort_order=page['D' + string].value,
        )
        return obj


class SubCategory(models.Model):
    """
    Модель для подкатегорий домов, которые отображаются на главной странице.
    Модель содержит список домов.
    Пример подкатегорий - "Квартиры с отделкой", "Можно заезжать"
    """

    id = models.IntegerField(primary_key=True, unique=True)
    name = models.CharField(max_length=64, null=True)
    title = models.CharField(max_length=64, null=True)
    mark = models.BooleanField(null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True)
    sort_order = models.IntegerField(unique=True, null=True)
    homes = models.ManyToManyField(Home)

    # Создает объект для записи из xls в SubCategory
    @classmethod
    def create_obj_from_xls(cls, page, string, *args):
        obj = cls(
            id=page['A' + string].value,
            name=page['B' + string].value,
            title=page['C' + string].value,
            mark=page['D' + string].value,
            category_id=page['E' + string].value,
            sort_order=page['F' + string].value,
        )
        return obj


class PhotoGallery(models.Model):
    """Модель фото для галерей жилых комплексов"""

    home = models.ForeignKey(Home, on_delete=models.CASCADE, null=True)
    photo_number = models.IntegerField(null=True)
    full = models.CharField(max_length=1024, null=True)
    resize = models.CharField(max_length=1024, null=True)
    preview_285 = models.CharField(max_length=1024, null=True)
    preview_531 = models.CharField(max_length=1024, null=True)

    # Пишет данные в PhotoGallery
    @classmethod
    def write_photos_url(cls):
        photos = Path(MEDIA_ROOT, 'core/photos/full')
        path_to_save = '{}/media/core/photos/{}/{}/{}'
        storage = []

        for directory in photos.iterdir():
            mapping = set_number_for_photo(directory)

            for file in directory.iterdir():
                obj = cls(
                    home_id=int(directory.name),
                    photo_number=mapping[file.name],
                    full=path_to_save.format(SITE_URL, 'full', directory.name, file.name),
                    resize=path_to_save.format(SITE_URL, 'resize', directory.name, file.name),
                    preview_285=path_to_save.format(SITE_URL, 'preview_285', directory.name, file.name),
                    preview_531=path_to_save.format(SITE_URL, 'preview_531', directory.name, file.name),
                )
                storage.append(obj)
        cls.objects.bulk_create(storage)

    # Очищает галерею
    @classmethod
    def remove_all(cls):
        cursor = connection.cursor()
        cursor.execute('TRUNCATE TABLE `core_photogallery`')


class MetroLine(models.Model):
    """Модель линий метро. Данные парсятся из xls-файла."""

    name = models.CharField(max_length=32)
    color = models.CharField(max_length=16)

    # Создает объект для записи из xls в MetroLine
    @classmethod
    def create_obj_from_xls(cls, page, string, *args):
        obj = cls(
            id=int(page['A' + string].value),
            name=page['B' + string].value,
            color=page['C' + string].value,
        )
        return obj


class MetroStation(models.Model):
    """Модель станций метро. Данные парсятся из xls-файла."""

    name = models.CharField(max_length=64)
    line = models.ForeignKey(MetroLine, on_delete=models.CASCADE, null=True)

    # Создает объект для записи из xls в MetroStation
    @classmethod
    def create_obj_from_xls(cls, page, string, *args):
        obj = cls(
            id=int(page['A' + string].value),
            name=page['B' + string].value,
            line_id=int(page['C' + string].value),
        )
        return obj

    # Возвращает словарь {станция метро: линия}, для записи линии метро в Home
    @classmethod
    def get_metro_lines_mapping(cls):
        mapping = {}
        for station in cls.objects.all():
            mapping.update({station.name: station.line_id})
        return mapping


# TODO: Вынести в отдельное приложение
class Lead(models.Model):
    """Модель заявки на перезвон"""

    page = models.CharField(max_length=128, null=True)
    form_name = models.CharField(max_length=64, null=True)
    phone = models.CharField(max_length=20)
    date = models.DateTimeField(auto_now_add=True)
