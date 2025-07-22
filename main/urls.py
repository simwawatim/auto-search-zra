from django.urls import path

from main import views
urlpatterns = [
    path('unitofmeasure/<str:code_name>/', views.UnitOfMeasureDetailByCodeName.as_view(), name='unitofmeasure-detail-by-codename'),
    path('packaging-unit-code/<str:code_name>/', views.PackagingUnitCodeDetail.as_view(), name='packaging-unit-code-detail'),
    path('country/<str:name>/', views.CountryDetailByName.as_view(), name='country-detail-by-name'),
    path('api/get-item-class-by-name/<str:item_class_name>/', views.ItemsClassView.as_view()),
    path("api/imports", views.Imports.as_view(), name="get_imports"),

]
