from .models import PackagingUnitCode, UnitOfMeasure, Country, ItemsClass
from django.contrib import admin


admin.site.register(PackagingUnitCode)
admin.site.register(UnitOfMeasure)
admin.site.register(ItemsClass)
admin.site.register(Country)
