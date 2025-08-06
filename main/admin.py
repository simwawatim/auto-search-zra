from .models import PackagingUnitCode, UnitOfMeasure, Country, ItemsClass, SupplierInvoice, SupplierInvoiceItem
from django.contrib import admin

admin.site.register(SupplierInvoiceItem)
admin.site.register(SupplierInvoice)
admin.site.register(PackagingUnitCode)
admin.site.register(UnitOfMeasure)
admin.site.register(ItemsClass)
admin.site.register(Country)
