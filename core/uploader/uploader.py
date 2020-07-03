import openpyxl


class Uploader:
    """Loads data on database from xls file"""

    def __init__(self, class_name, file_url, page, start_string=2, *args):
        self.class_name = class_name
        self.file = openpyxl.load_workbook(filename=file_url)
        self.page = self.file[page]
        self.start_string = start_string
        self.args = args

    # Загружает данные из xls в таблицы с Foreign Key
    def upload(self):
        def create_objects():
            class_name = self.class_name
            page = self.page
            number = self.start_string
            cell = page['A2']
            storage = []

            while cell.value is not None:
                string = str(number)
                obj = class_name.create_obj_from_xls(page, string, self.args)
                number += 1
                cell = page['A' + str(number)]
                storage.append(obj)
                if not number % 5_000:
                    yield storage
                    storage = []
            if storage:
                yield storage

        for object_set in create_objects():
            self.class_name.objects.bulk_create(object_set)

    # Загружает данные из xls в таблицы Many To Many
    def upload_many(self):
        master_class = self.class_name
        slave_class = self.args[0]
        page = self.page
        number = self.start_string
        cell = page['A2']

        while cell.value is not None:
            string = str(number)
            master = master_class.objects.get(id=page['B' + string].value)
            slave = slave_class.objects.get(id=page['C' + string].value)

            master.homes.add(slave)

            number += 1
            cell = page['A' + str(number)]
