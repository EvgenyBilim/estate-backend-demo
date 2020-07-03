from django.contrib import admin
from core.models import Home, Block, Plan, PhotoGallery, ShortPlan


@admin.register(Home, Block, Plan, ShortPlan, PhotoGallery)
class HomesAdmin(admin.ModelAdmin):
    pass
