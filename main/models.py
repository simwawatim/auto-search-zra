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
    

class SupplierInvoice(models.Model):
    invoice_name = models.CharField(max_length=100, null=True, blank=True) 
    spplr_tpin = models.CharField(max_length=20)
    spplr_nm = models.CharField(max_length=255)
    spplr_bhf_id = models.CharField(max_length=10)
    spplr_invc_no = models.CharField(max_length=50)
    rcpt_ty_cd = models.CharField(max_length=5)
    pmt_ty_cd = models.CharField(max_length=5)
    cfm_dt = models.DateTimeField()
    sales_dt = models.CharField(max_length=8) 
    stock_rls_dt = models.DateTimeField(null=True, blank=True)
    tot_item_cnt = models.PositiveIntegerField()
    tot_taxbl_amt = models.DecimalField(max_digits=15, decimal_places=4)
    tot_tax_amt = models.DecimalField(max_digits=15, decimal_places=4)
    tot_amt = models.DecimalField(max_digits=15, decimal_places=2)
    remark = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Invoice #{self.spplr_invc_no} - {self.spplr_nm}"


class SupplierInvoiceItem(models.Model):
    invoice = models.ForeignKey(SupplierInvoice, related_name='item_list', on_delete=models.CASCADE)
    item_seq = models.PositiveIntegerField()
    item_cd = models.CharField(max_length=50)
    item_cls_cd = models.CharField(max_length=20)
    item_nm = models.CharField(max_length=255)
    bcd = models.CharField(max_length=50, null=True, blank=True)
    pkg_unit_cd = models.CharField(max_length=10)
    pkg = models.DecimalField(max_digits=10, decimal_places=2)
    qty_unit_cd = models.CharField(max_length=20)
    qty = models.DecimalField(max_digits=10, decimal_places=2)
    prc = models.DecimalField(max_digits=15, decimal_places=2)
    sply_amt = models.DecimalField(max_digits=15, decimal_places=2)
    dc_rt = models.DecimalField(max_digits=5, decimal_places=2)
    dc_amt = models.DecimalField(max_digits=15, decimal_places=2)
    vat_cat_cd = models.CharField(max_length=5)
    ipl_cat_cd = models.CharField(max_length=10, null=True, blank=True)
    tl_cat_cd = models.CharField(max_length=10, null=True, blank=True)
    excise_tx_cat_cd = models.CharField(max_length=10, null=True, blank=True)
    vat_taxbl_amt = models.DecimalField(max_digits=15, decimal_places=2)
    excise_taxbl_amt = models.DecimalField(max_digits=15, decimal_places=2)
    ipl_taxbl_amt = models.DecimalField(max_digits=15, decimal_places=2)
    tl_taxbl_amt = models.DecimalField(max_digits=15, decimal_places=2)
    taxbl_amt = models.DecimalField(max_digits=15, decimal_places=2)
    vat_amt = models.DecimalField(max_digits=15, decimal_places=2)
    ipl_amt = models.DecimalField(max_digits=15, decimal_places=2)
    tl_amt = models.DecimalField(max_digits=15, decimal_places=2)
    excise_tx_amt = models.DecimalField(max_digits=15, decimal_places=2)
    tot_amt = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self):
        return f"{self.item_nm} (Seq: {self.item_seq})"



