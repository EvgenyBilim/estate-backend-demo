from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from core.management import PhotoManager, UploadManager
from core.storage import MediaStorage


class PanelView(LoginRequiredMixin, View):
    """Панель управления загрузками xls-файлов из админки"""

    login_url = '/admin/'
    redirect_field_name = 'redirect_to'
    template = 'core/uploads_panel.html'

    def get(self, request):
        delete = request.GET.get('delete')

        func_mapping = {
            'homes': UploadManager().delete_homes,
            'metro': UploadManager().delete_metro,
            'photos': PhotoManager().remove_gallery,
        }

        if delete:
            try:
                func = func_mapping[delete]
                func()
            except KeyError:
                pass

        return render(request, self.template, {
            'menu_uploads': ' menu__item_active',
        })


class UploadView(LoginRequiredMixin, View):
    """Страница загрузки xls-файла на сервер из админки"""

    login_url = '/admin/'
    redirect_field_name = 'redirect_to'
    template = 'core/upload.html'

    def get(self, request, **kwargs):
        kind = self.kwargs.get('kind')

        mapping = {
            'homes': 'Дома',
            'plans': 'Планировки',
            'category': 'Категории',
            'photos': 'Фото',
            'metro': 'Метро',
        }

        try:
            title = mapping[kind]
        except KeyError:
            title = '*'

        return render(request, self.template, {
            'menu_uploads': ' menu__item_active',
            'title': title,
        })

    def post(self, request, **kwargs):
        kind = self.kwargs.get('kind')
        file_url = MediaStorage.save_file(request)
        load_status = 'ok'

        func_mapping = {
            'homes': UploadManager().upload_homes,
            'plans': UploadManager().upload_plans,
            'category': UploadManager().upload_category,
            'metro': UploadManager().upload_metro,
            'photos': PhotoManager().upload_photos,
        }

        try:
            func = func_mapping[kind]
            func(file_url)
        except KeyError:
            load_status = 'error'

        return JsonResponse(data={'load': load_status})


class MakeArchiveView(LoginRequiredMixin, View):
    """
    Страница, которая отдает zip-архив с пустыми папками, соответствующие
    названиям домов на сайте. В эти папки потом заливаются фото и грузятся
    обратно на сайт.
    """

    login_url = '/admin/'
    redirect_field_name = 'redirect_to'
    template = 'core/download_archive.html'

    def get(self, request):
        zip_url = PhotoManager().create_empty_photo_archive()

        return render(request, self.template, {
            'menu_uploads': ' menu__item_active',
            'archive_url': zip_url,
        })
