from .models import Country, PackagingUnitCode, UnitOfMeasure, ItemsClass
from rest_framework import serializers


class PackagingUnitCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackagingUnitCode
        fields = ['code', 'code_name', 'code_description']

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ['code', 'sort_order', 'name', 'description', 'remark']




class UnitOfMeasureSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitOfMeasure
        fields = ['code', 'code_name', 'code_description']


class itemClassListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemsClass
        fields = ['itemClsCd', 'itemClsNm', 'itemClsLvl', 'useYn']