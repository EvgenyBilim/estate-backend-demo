from core.utils.mapping import METRO_LINE_COLOR, YEAR_MONTH, YEAR_PART, TRIM_SHORT, TRIM_FULL
import datetime
import re


# Home - оборачивает текст описания в теги <p>
def wrap_homes_description(text):
    result = ''
    lines = text.splitlines()

    for i in lines:
        result += '<p>' + i + '</p>'
    return result


# Home - переводит дистанцию до метро в читаемый вид
def details_metro_distance(distance):
    minute = ''
    result = ''

    for symbol in distance:
        if symbol.isdigit():
            minute += symbol
        if symbol.upper() == 'П':
            result = minute + ' мин. пешком'
        if symbol.upper() == 'Т':
            result = minute + ' мин. на машине'
    return result


# Home - считает индекс для сортировки по расстоянию до метро
def calc_sort_metro_distance(distance):
    minute = ''
    result = None
    multiplier = 5

    for symbol in distance:
        if symbol.isdigit():
            minute += symbol
        if symbol.upper() == 'П':
            result = int(minute)
        if symbol.upper() == 'Т':
            result = int(minute) * multiplier
    return result


# Home - url для картинки метро
def get_metro_line(metro_lines, home_metro, site_url):
    try:
        line = metro_lines[home_metro]
        color = METRO_LINE_COLOR[line]
    except KeyError:
        color = 'plug'
    return color


# Block - переводит одну дату в текстовый вид
def delivery_date_to_string(delivery_date):
    now = datetime.datetime.today()

    if delivery_date <= now:
        return 'Сдан'
    elif delivery_date > now:
        month = YEAR_MONTH[delivery_date.month]
        year = str(delivery_date.year)
        return '{} {}'.format(month, year).capitalize()
    else:
        return ''


# Plan - переводит квартиры-студии в цифровой вид
def rooms_mapping(room):
    if room == 'C':
        room = '0'
    return room


# Plan - маппинг отделки при загрузке xls
def trim_mapping(trim):
    result = ''
    trim_set = {
        'Без отделки': 'НЕТ',
        'Подчистовая': 'ПРЕД',
        'Чистовая': 'ПОЛН',
        'С ремонтом': 'ПОЛН',
        'С мебелью': 'ПОЛН',
    }
    try:
        result = trim_set[trim]
    except KeyError:
        pass

    return result


# Plan - делит этажи на "этаж" и "всего этажей"
def floors_parser(floors):
    floor_number = ''
    floors_count = ''

    # TODO: Переписать на регулярках
    slash = False
    for symbol in floors:
        if slash is False:
            if symbol.isdigit():
                floor_number += symbol
            if symbol == '/':
                slash = True
        if slash is True:
            if symbol.isdigit():
                floors_count += symbol
    floor_number = int(floor_number)
    floors_count = int(floors_count)

    return floor_number, floors_count


# ShortPlan - переводит цену в короткий
def price_to_short(price):
    return round(price / 1_000_000, 2)


# Home (calc) - переводит несколько дат в текстовый вид, напрмер: Начало 2021 - конец 2022
def details_delivery(blocks, home_id, param):

    # Возвращает часть года в текстовом виде
    def part_of_year(dates, param):
        month = dates.month
        year = str(dates.year)

        if param == 'part':
            part = YEAR_PART[month]
        else:
            part = YEAR_MONTH[month]
        return part + ' ' + year

    try:
        blocks = blocks[home_id]
    except KeyError:
        return None

    now = datetime.date.today()
    date_from = min(blocks)
    date_to = max(blocks)

    if date_to > now:
        if date_from == date_to:
            # срок такой-то
            return part_of_year(date_from, param).capitalize()
        else:
            if date_from > now:
                # начало - конец
                f = part_of_year(date_from, param)
                t = part_of_year(date_to, param)
                return '{} – {}'.format(f, t).capitalize()
            else:
                # срок, есть сданные
                p = part_of_year(date_to, param).capitalize()
                return '{}, есть сданные'.format(p).capitalize()
    elif date_to < now:
        # сдан
        return 'Дом сдан'


# Home (calc) - вычисляет саммый ранний срок сдачи из нескольких
def calc_min_date(blocks, home_id):
    min_date = None
    try:
        home_blocks = blocks[home_id]
        min_date = min(home_blocks)
    except KeyError:
        pass

    return min_date


# Home (calc) - склоняет слово "квартира"
def get_text_plans_count(storage, home_id):
    try:
        count = len(storage[home_id])
    except KeyError:
        count = 0

    if count % 10 == 1:
        quarter = 'квартира'
    elif count % 10 == 2 or count % 10 == 3 or count % 10 == 4:
        quarter = 'квартиры'
    else:
        quarter = 'квартир'

    if (count - 11) % 100 == 0 \
            or (count - 12) % 100 == 0 \
            or (count - 13) % 100 == 0 \
            or (count - 14) % 100 == 0:
        quarter = 'квартир'

    # Разделяет число на разряды: 12345 -> '12 345'
    count = '{:,}'.format(count).replace(',', ' ')

    return count + ' ' + quarter


# Home (calc) - склоняет слово "корпус"
def get_text_blocks_count(storage, home_id):
    try:
        count = len(storage[home_id])
    except KeyError:
        count = 0

    if count % 10 == 1:
        block = 'корпус'
    elif count % 10 == 2 or count % 10 == 3 or count % 10 == 4:
        block = 'корпуса'
    else:
        block = 'корпусов'

    if (count - 11) % 100 == 0 \
            or (count - 12) % 100 == 0 \
            or (count - 13) % 100 == 0 \
            or (count - 14) % 100 == 0:
        block = 'корпусов'

    # Разделяет число на разряды: 12345 -> '12 345'
    count = '{:,}'.format(count).replace(',', ' ')

    return count + ' ' + block


# Home (calc) - возвращает список всех типов отделки для одного дома
def trim_details(plans, home_id, param, default_trim):
    try:
        plans = plans[home_id]
    except KeyError:
        try:
            if param == 'trim_full':
                return TRIM_FULL[default_trim]
            else:
                return TRIM_SHORT[default_trim]
        except KeyError:
            return None

    storage = []

    for plan, values in plans.items():
        trim = values[param]
        if trim not in storage:
            storage.append(trim)
    storage.sort()

    return ', '.join(storage)


# Home (calc) - возвращает список всех типов оплаты для одного дома
def get_payment(plans, home_id):
    try:
        plans = plans[home_id]
    except KeyError:
        return None

    for plan, values in plans.items():
        return values['payment']


# Home (calc) - возвращает список всех банков для одного дома
def get_banks(plans, home_id):
    try:
        plans = plans[home_id]
    except KeyError:
        return None

    for plan, values in plans.items():
        return values['banks']


# Home (calc) - возвращает цену самой дешевой/дорогой квартиры для одного дома
def min_max_price(plans, home_id, param):
    try:
        plans = plans[home_id]
    except KeyError:
        return None

    storage = []

    for plan, value in plans.items():
        price = value['price']
        storage.append(price)

    if param == 'min':
        return min(storage)
    if param == 'max':
        return max(storage)


# Home (calc) - возвращает список с минимальными ценами на каждый тип квартиры у дома
def get_price_set(short_plans, home_id):
    rooms = ['0', '1', '2', '3', '4']
    prices = []

    for room in rooms:
        try:
            price = short_plans[home_id][room]
            price = '{:,}'.format(price).replace(',', ' ')
            prices.append(price + ' р.')
        except KeyError:
            prices.append('нет в продаже')

    return repr(prices)


# Home - возвращает url заглушки для превью фото
def get_preview_plug_url(size, site_url):
    plugs_path = '{}/static/core/img/plugs/{}.jpg'.format(site_url, size)
    return plugs_path


# Home (preview) - возвращает url для картинки превью
def get_preview_photo_url(gallery, home_id, size, site_url):
    path_to_plug = '{}/static/core/img/plugs/{}.jpg'.format(site_url, size)
    try:
        gallery = gallery.objects.get(home_id=home_id, photo_number=1)
        if size == '285':
            return gallery.preview_285
        if size == '531':
            return gallery.preview_531
    except gallery.DoesNotExist:
        pass
    return path_to_plug


# PhotoGallery - присваивает номер фоткам внутри директорий с домами
def set_number_for_photo(directory):
    names = []
    counter = {}
    for f in directory.iterdir():
        names.append(f.name)
    names = sorted_alphanumeric(names)
    count = 1
    for name in names:
        counter.update({name: count})
        count += 1
    return counter


# PhotoGallery - сортирует названия фото в директории: 1, 10, 2 -> 1, 2, 10
def sorted_alphanumeric(data):
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(data, key=alphanum_key)
