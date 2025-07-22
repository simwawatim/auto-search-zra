from django.db import models


class ItemsClass(models.Model):
    itemClsCd = models.CharField(max_length=10, unique=True)
    itemClsNm = models.CharField(max_length=100)
    itemClsLvl = models.CharField(max_length=100)
    useYn = models.BooleanField(default=True) 

    def __str__(self):
        return self.itemClsCd
    
    
class PackagingUnitCode(models.Model):
    code = models.CharField(max_length=10, unique=True)
    code_name = models.CharField(max_length=100)
    code_description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.code} - {self.code_name}"
    

class UnitOfMeasure(models.Model):
    code = models.CharField(max_length=10, unique=True)
    code_name = models.CharField(max_length=100)
    code_description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.code} - {self.code_name}"
    

class Country(models.Model):
    code = models.CharField(max_length=10, unique=True)
    sort_order = models.IntegerField()
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    remark = models.TextField(blank=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

