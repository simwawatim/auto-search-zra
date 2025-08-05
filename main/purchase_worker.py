import random
import uuid
from datetime import datetime
from django.http import HttpResponse
from main.models import ItemsClass, PackagingUnitCode, UnitOfMeasure
import mysql.connector
from mysql.connector import Error


# ---------------- Connection Class ----------------
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


# ---------------- Purchase Fetcher ----------------
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
                            "qtyUnitCd": "BE",
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


# ---------------- Unified Purchase Execution View ----------------
def get_purchase(request):
    db = Connection("localhost", "root", "root", "_7fb1f4533ec3ac7c")
    if not db.conn or not db.conn.is_connected():
        return HttpResponse("Database connection failed.", status=500)

    cursor = db.conn.cursor()
    inserted_items = []

    insert_item_sql = """
        INSERT INTO tabItem (
            name, item_group, stock_uom, custom_product_type, item_code, custom_item_class_code, item_name,
            custom_packaging_unit_code, custom_units_of_measure,
            opening_stock, standard_rate, custom_vat,
            custom_ipl_category_code, custom_tourism_levy, custom_excise_tax_category_code
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

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
    for sale in sale_list:
        for item in sale.get("itemList", []):
            code = datetime.now().strftime("%H%M%S")
            name = f"PURCHASEITEM-{code}-{random.randint(1000,9999)}"
            item_class_name = "N / A"
            pkg_name = "N / A"
            unit_of_measure_name = "N / A"
            try:
                cls = ItemsClass.objects.get(itemClsCd=item.get("itemClsCd"))
                item_class_name = cls.itemClsNm or "N / A"
            except ItemsClass.DoesNotExist:
                pass
            except Exception as e:
                print(f"Error getting item class: {e}")

            try:
                pkgcode = PackagingUnitCode.objects.get(code=item.get("pkgUnitCd"))
                pkg_name = pkgcode.code_name or "N / A"
            except PackagingUnitCode.DoesNotExist:
                pass
            except Exception as e:
                print(f"Error getting packaging code: {e}")
            try:
                unit_measure = UnitOfMeasure.objects.get(code=item.get("qtyUnitCd"))
                unit_of_measure_name = unit_measure.code_name or "N / A"
            except UnitOfMeasure.DoesNotExist:
                pass
            except Exception as e:
                print(f"Error getting unit of measure: {e}")

            vat_code = item.get("vatCatCd", "N / A")
            vat_name = VAT_CATEGORIES.get(vat_code, "Unknown VAT Category")

            values = (
                name,
                "Products",
                "KGM",
                "Finished Product",
                item.get("itemCd", "N / A"),
                item_class_name,
                item.get("itemNm", "N / A"),
                pkg_name,
                unit_of_measure_name,
                item.get("qty") or 0,
                item.get("prc") or 0,
                vat_name,
                item.get("iplCatCd") or "N / A",
                item.get("tlCatCd") or "N / A",
                item.get("exciseTxCatCd") or "N / A"
            )

            try:
                cursor.execute(insert_item_sql, values)
                db.conn.commit()
                inserted_items.append(item.get("itemNm", "Unnamed Item"))
                print(f"Inserted item: {item.get('itemNm')}")
            except Error as e:
                print(f"Item insert error: {e}")
                db.conn.rollback()

    # Optional: Insert purchase invoice
    if sale_list:
        first_sale = sale_list[0]
        supplier_name = first_sale.get("spplrNm")
        supplier_tpin = first_sale.get("spplrTpin")
        code = datetime.now().strftime("%H%M%S")
        purchase_invoice_name = f"PURCHASEINVOICE-{code}-{random.randint(1000,9999)}"
        posting_date = datetime.today().strftime("%Y-%m-%d")
        currency = "ZMW"
        conversion_rate = 1.0
        company_name = "IIS"

        if supplier_name:
            try:
                cursor.execute("SELECT name FROM tabSupplier WHERE name = %s", (supplier_name,))
                if not cursor.fetchone():
                    cursor.execute(
                        "INSERT INTO tabSupplier (name, custom_supplier_tpin) VALUES (%s, %s)",
                        (supplier_name, supplier_tpin)
                    )
                    db.conn.commit()
                    print(f"Inserted new supplier: {supplier_name}")
                else:
                    print(f"ℹSupplier '{supplier_name}' already exists.")
            except Error as e:
                print(f"Supplier insert error: {e}")
                db.conn.rollback()

            try:
                cursor.execute("""
                    INSERT INTO `tabPurchase Invoice`
                    (name, supplier, supplier_name, title, posting_date, bill_date, company, currency, conversion_rate, docstatus, naming_series, creation, modified)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 0, %s, NOW(), NOW())
                """, (
                    purchase_invoice_name, supplier_name, supplier_name, supplier_name, posting_date, posting_date,
                    company_name, currency, conversion_rate, "ACC-PINV"
                ))
                db.conn.commit()
                print(f"Inserted purchase invoice {purchase_invoice_name}")
            except Error as e:
                print(f"Purchase invoice insert error: {e}")
                db.conn.rollback()

            idx = 1
            for item in first_sale.get("itemList", []):
                item_code = item.get("itemCd", "N / A")
                item_name = item.get("itemNm", "N / A")
                qty = item.get("qty") or 0
                rate = item.get("prc") or 0
                amount = qty * rate

                try:
                    cursor.execute("""
                        INSERT INTO `tabPurchase Invoice Item`
                        (name, parent, parenttype, parentfield, item_code, item_name, qty, stock_uom, rate, amount, creation, modified, idx)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s)
                    """, (
                        str(uuid.uuid4()), purchase_invoice_name, "Purchase Invoice", "items",
                        item_code, item_name,
                        qty, item.get("qtyUnitCd") or "Acre", rate, amount, idx
                    ))

                    db.conn.commit()
                    print(f"Inserted invoice item: {item_name}")
                    idx += 1
                except Error as e:
                    print(f"Purchase invoice item insert error: {e}")
                    db.conn.rollback()

    cursor.close()
    db.close()
    return HttpResponse(f"✅ Done! Inserted items: {', '.join(inserted_items)}")
