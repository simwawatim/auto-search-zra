from decimal import Decimal, InvalidOperation
import random
import uuid
from datetime import datetime
from django.http import HttpResponse
from main.models import ItemsClass, PackagingUnitCode, SupplierInvoice, SupplierInvoiceItem, UnitOfMeasure
import mysql.connector
from mysql.connector import Error


class Connection:
    def __init__(self, host, user, password, database):
        self.conn = None
        try:
            self.conn = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )
            if self.conn.is_connected():
                print("Connected to MySQL database")
        except Error as e:
            print(f"Error connecting to MySQL: {e}")

    def close(self):
        try:
            if self.conn and self.conn.is_connected():
                self.conn.close()
                print("MySQL connection closed")
        except Exception as e:
            print(f"Error closing connection: {e}")


class GetPurchase:
    def get_purchase_zra_client(self):
        return {
            "saleList": [
                {
                    "spplrTpin": "1000000000",
                    "spplrNm": "SMART SUPPLIER",
                    "spplrBhfId": "000",
                    "spplrInvcNo": 45,
                    "rcptTyCd": "S",
                    "pmtTyCd": "01",
                    "cfmDt": "2024-05-08 10:20:10",
                    "salesDt": "20240502",
                    "stockRlsDt": None,
                    "totItemCnt": 1,
                    "totTaxblAmt": 86.2069,
                    "totTaxAmt": 13.7931,
                    "totAmt": 100,
                    "remark": None,
                    "itemList": [
                        {
                            "itemSeq": 1,
                            "itemCd": "20044",
                            "itemClsCd": "23101500",
                            "itemNm": "ChickenWings",
                            "bcd": None,
                            "pkgUnitCd": "BA",
                            "pkg": 0,
                            "qtyUnitCd": "bundle",
                            "qty": 1,
                            "prc": 100,
                            "splyAmt": 100,
                            "dcRt": 0,
                            "dcAmt": 0,
                            "vatCatCd": "A",
                            "iplCatCd": None,
                            "tlCatCd": None,
                            "exciseTxCatCd": None,
                            "vatTaxblAmt": 86.21,
                            "exciseTaxblAmt": 0,
                            "iplTaxblAmt": 0,
                            "tlTaxblAmt": 0,
                            "taxblAmt": 86.21,
                            "vatAmt": 13.79,
                            "iplAmt": 0,
                            "tlAmt": 0,
                            "exciseTxAmt": 0,
                            "totAmt": 100
                        }
                    ]
                }
            ]
        }


def safe_decimal(val, default=Decimal("0")):
    try:
        if val is None:
            return default
        if isinstance(val, Decimal):
            return val
        return Decimal(str(val))
    except (InvalidOperation, ValueError):
        return default


def get_purchase(request):
    db = Connection("localhost", "root", "root", "_7fb1f4533ec3ac7c")
    if not db.conn or not db.conn.is_connected():
        return HttpResponse("Database connection failed.", status=500)

    cursor = db.conn.cursor()
    inserted_items = []
    purchase_invoice_name = None
    try:
        purchase_data = GetPurchase().get_purchase_zra_client()
        sale_list = purchase_data.get("saleList", [])

        cursor.execute("SELECT default_payable_account FROM `tabCompany` WHERE name = %s", ("IIS",))
        payable_account_row = cursor.fetchone()
        if not payable_account_row:
            return HttpResponse("No payable account found in company 'IIS'", status=500)
        credit_to = payable_account_row[0]

        for sale in sale_list:
            supplier_name = sale.get("spplrNm")
            supplier_tpin = sale.get("spplrTpin")
            code = datetime.now().strftime("%H%M%S")
            purchase_invoice_name = f"SMART-INVOICE-PURCHASE-{code}-{random.randint(1000,9999)}"
            posting_date = datetime.today().strftime("%Y-%m-%d")
            sup_purch_no = sale.get("spplrInvcNo")
            company_name = "IIS"
            currency = "ZMW"
            conversion_rate = 1.0

            try:
                cursor.execute("SELECT name FROM tabSupplier WHERE name = %s", (supplier_name,))
                if not cursor.fetchone():
                    cursor.execute(
                        "INSERT INTO tabSupplier (name, custom_supplier_tpin) VALUES (%s, %s)",
                        (supplier_name, supplier_tpin)
                    )
                    db.conn.commit()
            except Error as e:
                print(f"Supplier insert error: {e}")
                db.conn.rollback()

            try:
                cursor.execute("""
                    INSERT INTO `tabPurchase Invoice`
                    (name, supplier, supplier_name, custom_purchase__invoice, title, posting_date, bill_date, company, currency,
                     conversion_rate, docstatus, naming_series, credit_to, creation, modified)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                """, (
                    purchase_invoice_name,
                    supplier_name,
                    sup_purch_no,
                    supplier_name,
                    supplier_name,
                    posting_date,
                    posting_date,
                    company_name,
                    currency,
                    conversion_rate,
                    0,
                    "ACC-PINV",
                    credit_to
                ))
                db.conn.commit()
            except Error as e:
                print(f"Purchase invoice insert error: {e}")
                db.conn.rollback()
                continue

            idx = 1
            for item in sale.get("itemList", []):
                item_code = item.get("itemCd", "N / A")
                item_name = item.get("itemNm", "N / A")
                qty = safe_decimal(item.get("qty"))
                rate = safe_decimal(item.get("prc"))
                amount = qty * rate

                vat_code = item.get("vatCatCd") or None
                ipl_code = item.get("iplCatCd") or None
                tl_code = item.get("tlCatCd") or None
                excise_code = item.get("exciseTxCatCd") or None

                qty_uom = item.get("qtyUnitCd", "EA")
                cursor.execute("SELECT name FROM `tabUOM` WHERE name = %s", (qty_uom,))
                if cursor.fetchone():
                    uom_name = qty_uom
                else:
                    print(f"Invalid UOM '{qty_uom}' → using fallback 'Acre'")
                    uom_name = "Acre"

                try:
                    cursor.execute("""
                        INSERT INTO `tabPurchase Invoice Item`
                        (name, parent, parenttype, parentfield, item_code, item_name, qty, custom_tax_type, custom_ipl, custom_tl, custom_excise, uom, stock_uom, rate, amount, creation, modified, idx)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s)
                    """, (
                        str(uuid.uuid4()),
                        purchase_invoice_name,
                        "Purchase Invoice",
                        "items",
                        item_code,
                        item_name,
                        float(qty),
                        vat_code,
                        ipl_code,
                        tl_code,
                        excise_code,
                        uom_name,
                        uom_name,
                        float(rate),
                        float(amount),
                        idx
                    ))
                    db.conn.commit()
                    idx += 1
                    inserted_items.append(item_name)
                except Error as e:
                    print(f"Purchase invoice item insert error for item '{item_name}': {e}")
                    db.conn.rollback()

    except Exception as e:
        print(f"Unexpected error in get_purchase: {e}")
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        db.close()

    if purchase_invoice_name:
        try:
            create_purchase_and_purchase_items(request, purchase_invoice_name)
        except Exception as e:
            print(f"Error in creating ORM SupplierInvoice records: {e}")

    return HttpResponse(f"Done! Inserted items: {', '.join(inserted_items)}")


def create_purchase_and_purchase_items(request, purchase_invoice_name):
    purchase_data = GetPurchase().get_purchase_zra_client()
    sale_list = purchase_data.get("saleList", [])

    for sale in sale_list:
        cfm_dt = None
        if sale.get("cfmDt"):
            try:
                cfm_dt = datetime.strptime(sale.get("cfmDt"), "%Y-%m-%d %H:%M:%S")
            except Exception:
                cfm_dt = None

        sales_dt = sale.get("salesDt")
        stock_rls_dt = sale.get("stockRlsDt")
        if stock_rls_dt:
            try:
                stock_rls_dt = datetime.strptime(stock_rls_dt, "%Y-%m-%d %H:%M:%S")
            except Exception:
                stock_rls_dt = None

        tot_taxbl_amt = safe_decimal(sale.get("totTaxblAmt"))
        tot_tax_amt = safe_decimal(sale.get("totTaxAmt"))
        tot_amt = safe_decimal(sale.get("totAmt"))

        invoice = SupplierInvoice.objects.create(
            invoice_name=purchase_invoice_name,
            spplr_tpin=sale.get("spplrTpin"),
            spplr_nm=sale.get("spplrNm"),
            spplr_bhf_id=sale.get("spplrBhfId"),
            spplr_invc_no=str(sale.get("spplrInvcNo")),
            rcpt_ty_cd=sale.get("rcptTyCd"),
            pmt_ty_cd=sale.get("pmtTyCd"),
            cfm_dt=cfm_dt,
            sales_dt=sales_dt,
            stock_rls_dt=stock_rls_dt,
            tot_item_cnt=sale.get("totItemCnt"),
            tot_taxbl_amt=tot_taxbl_amt,
            tot_tax_amt=tot_tax_amt,
            tot_amt=tot_amt,
            remark=sale.get("remark"),
        )

        for item in sale.get("itemList", []):
            SupplierInvoiceItem.objects.create(
                invoice=invoice,
                item_seq=item.get("itemSeq"),
                item_cd=item.get("itemCd"),
                item_cls_cd=item.get("itemClsCd"),
                item_nm=item.get("itemNm"),
                bcd=item.get("bcd"),
                pkg_unit_cd=item.get("pkgUnitCd"),
                pkg=safe_decimal(item.get("pkg")),
                qty_unit_cd=item.get("qtyUnitCd"),
                qty=safe_decimal(item.get("qty")),
                prc=safe_decimal(item.get("prc")),
                sply_amt=safe_decimal(item.get("splyAmt")),
                dc_rt=safe_decimal(item.get("dcRt")),
                dc_amt=safe_decimal(item.get("dcAmt")),
                vat_cat_cd=item.get("vatCatCd"),
                ipl_cat_cd=item.get("iplCatCd"),
                tl_cat_cd=item.get("tlCatCd"),
                excise_tx_cat_cd=item.get("exciseTxCatCd"),
                vat_taxbl_amt=safe_decimal(item.get("vatTaxblAmt")),
                excise_taxbl_amt=safe_decimal(item.get("exciseTaxblAmt")),
                ipl_taxbl_amt=safe_decimal(item.get("iplTaxblAmt")),
                tl_taxbl_amt=safe_decimal(item.get("tlTaxblAmt")),
                taxbl_amt=safe_decimal(item.get("taxblAmt")),
                vat_amt=safe_decimal(item.get("vatAmt")),
                ipl_amt=safe_decimal(item.get("iplAmt")),
                tl_amt=safe_decimal(item.get("tlAmt")),
                excise_tx_amt=safe_decimal(item.get("exciseTxAmt")),
                tot_amt=safe_decimal(item.get("totAmt")),
            )

    return HttpResponse("Supplier invoices and items saved to the database.")
