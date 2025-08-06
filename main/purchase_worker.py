import random
import uuid
from datetime import datetime
from django.http import HttpResponse
from main.models import ItemsClass, PackagingUnitCode, UnitOfMeasure
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
        if self.conn and self.conn.is_connected():
            self.conn.close()
            print("MySQL connection closed")


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


def get_purchase(request):
    db = Connection("localhost", "root", "root", "_7fb1f4533ec3ac7c")
    if not db.conn or not db.conn.is_connected():
        return HttpResponse("Database connection failed.", status=500)

    cursor = db.conn.cursor()
    inserted_items = []
    purchase_data = GetPurchase().get_purchase_zra_client()
    sale_list = purchase_data.get("saleList", [])
    VAT_CATEGORIES = {
        "A": "StandardRated",
        "B": "Minimum Taxable Value (MTV)",
        "C": "Exports 0%",
        "C1": "RVAT Reverse VAT",
        "C2": "Zero-Rating Local Purchases/Order Transactions 0%",
        "C3": "Zero-Rated by Nature 0%",
        "D": "Exempt No tax charge",
        "E": "Disbursement"
    }

    cursor.execute("SELECT default_payable_account FROM `tabCompany` WHERE name = %s", ("IIS",))
    payable_account_row = cursor.fetchone()
    if not payable_account_row:
        return HttpResponse("No payable account found in company 'IIS'", status=500)

    credit_to = payable_account_row[0]

    for sale in sale_list:
        for item in sale.get("itemList", []):
            item_code = item.get("itemCd", "N / A")
            item_name = item.get("itemNm", "N / A")
            item_class_name = "N / A"
            pkg_name = "N / A"
            qty_uom = item.get("qtyUnitCd", "EA")  # e.g., 'bundle'

            # Validate UOM: fallback to 'Acre' if not found in tabUOM
            cursor.execute("SELECT name FROM `tabUOM` WHERE name = %s", (qty_uom,))
            if cursor.fetchone():
                unit_of_measure_name = qty_uom
            else:
                print(f"Invalid UOM '{qty_uom}' → using fallback 'Acre'")
                unit_of_measure_name = "Acre"

            try:
                cls = ItemsClass.objects.get(itemClsCd=item.get("itemClsCd"))
                item_class_name = cls.itemClsNm or "N / A"
            except:
                pass

            try:
                pkgcode = PackagingUnitCode.objects.get(code=item.get("pkgUnitCd"))
                pkg_name = pkgcode.code_name or "N / A"
            except:
                pass

            vat_code = item.get("vatCatCd", "N / A")
            vat_name = VAT_CATEGORIES.get(vat_code, "Unknown VAT Category")

            # Check if item exists
            cursor.execute("SELECT name FROM tabItem WHERE name = %s", (item_code,))
            if not cursor.fetchone():
                try:
                    cursor.execute("""
                        INSERT INTO tabItem (
                            name, item_group, stock_uom, custom_product_type, item_code, custom_item_class_code, item_name,
                            custom_packaging_unit_code, custom_units_of_measure,
                            opening_stock, standard_rate, custom_vat,
                            custom_ipl_category_code, custom_tourism_levy, custom_excise_tax_category_code
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        item_code, "Products", unit_of_measure_name, "Finished Product",
                        item_code, item_class_name, item_name,
                        pkg_name, unit_of_measure_name,
                        item.get("qty") or 0, item.get("prc") or 0, vat_name,
                        item.get("iplCatCd") or "N / A",
                        item.get("tlCatCd") or "N / A",
                        item.get("exciseTxCatCd") or "N / A"
                    ))
                    db.conn.commit()
                    inserted_items.append(item_name)
                except Error as e:
                    print(f"Item insert error: {e}")
                    db.conn.rollback()

        supplier_name = sale.get("spplrNm")
        supplier_tpin = sale.get("spplrTpin")
        code = datetime.now().strftime("%H%M%S")
        purchase_invoice_name = f"SMART-INVOICE-PURCHASE-{code}-{random.randint(1000,9999)}"
        posting_date = datetime.today().strftime("%Y-%m-%d")
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
                (name, supplier, supplier_name, title, posting_date, bill_date, company, currency,
                 conversion_rate, docstatus, naming_series, credit_to, creation, modified)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 0, %s, %s, NOW(), NOW())
            """, (
                purchase_invoice_name, supplier_name, supplier_name, supplier_name,
                posting_date, posting_date, company_name, currency, conversion_rate,
                "ACC-PINV", credit_to
            ))
            db.conn.commit()
        except Error as e:
            print(f"Purchase invoice insert error: {e}")
            db.conn.rollback()

        idx = 1
        for item in sale.get("itemList", []):
            item_code = item.get("itemCd", "N / A")
            item_name = item.get("itemNm", "N / A")
            qty = item.get("qty") or 0
            rate = item.get("prc") or 0
            amount = qty * rate

            # Use the same UOM fallback logic here
            qty_uom = item.get("qtyUnitCd", "EA")
            cursor.execute("SELECT name FROM `tabUOM` WHERE name = %s", (qty_uom,))
            if cursor.fetchone():
                uom_name = qty_uom
            else:
                uom_name = "Acre"

            try:
                cursor.execute("""
                    INSERT INTO `tabPurchase Invoice Item`
                    (name, parent, parenttype, parentfield, item_code, item_name, qty, uom, stock_uom, rate, amount, creation, modified, idx)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s)
                """, (
                    str(uuid.uuid4()), purchase_invoice_name, "Purchase Invoice", "items",
                    item_code, item_name, qty,
                    uom_name, uom_name,
                    rate, amount, idx
                ))
                db.conn.commit()
                idx += 1
            except Error as e:
                print(f"Purchase invoice item insert error: {e}")
                db.conn.rollback()

    cursor.close()
    db.close()
    return HttpResponse(f"Done! Inserted items: {', '.join(inserted_items)}")
