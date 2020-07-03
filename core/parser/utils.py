from PIL import Image
import re


# PhotoParser - ресайзит и кропает фото для превью
def resize_to_preview(photo, name, multiplier, crop_w, crop_h):
    try:
        img = Image.open(photo)
        img = img.convert('RGB')
        if (img.width / img.height) > multiplier:
            img.thumbnail((crop_w * 10, crop_h))
        elif (img.width / img.height) < multiplier:
            img.thumbnail((crop_w, crop_h * 10))
        else:
            img.thumbnail((crop_w, crop_h))
        if img.width > crop_w:
            width = (img.width - crop_w) / 2
        else:
            width = 0
        if img.height > crop_h:
            height = (img.height - crop_h) / 2
        else:
            height = 0
        img = img.crop((width, height, crop_w + width, crop_h + height))
        img.save(name, 'JPEG', quality=100)
    except OSError:
        pass
    return name


# PhotoParser - ресайзит фото без кропа
def resize_to_gallery(photo, name, gallery_height=440):
    try:
        img = Image.open(photo)
        img = img.convert('RGB')
        w, h = img.size
        scale = gallery_height / h

        if h > gallery_height:
            img = img.resize((int(w * scale), int(h * scale)))
        img.save(name, 'JPEG', quality=85)
    except OSError:
        pass
    return name


# PhotoParser - сохраняет фото без изменения размера
def save_full_size(photo, name):
    try:
        img = Image.open(photo)
        img = img.convert('RGB')
        img.save(name, 'JPEG', quality=85)
    except OSError:
        pass
    return name


# PhotoParser - получает id дома из названия его директории: ART-Квартал(299) -> 299
def get_id_from_name(name):
    home_id = re.search(r'[(]\d+[)]', name)
    home_id = re.search(r'(\d+)', home_id.group(0))
    return home_id.group(0)


# PhotoParser - заменяет пробелы на нижние подчеркивания в названиях фото
def delete_space_in_name(name):
    name = str(name)
    result = ''
    for s in name:
        if s == ' ':
            s = '_'
        result += s
    return result
