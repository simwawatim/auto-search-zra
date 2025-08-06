import uuid
from django.http import HttpResponse
from mysql.connector import Error
from datetime import datetime
import mysql.connector
import requests
import random
import json

from main.models import Country, ItemsClass, PackagingUnitCode, UnitOfMeasure


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


class GetItems:
    def __init__(self):
        self.result_msg = ""
        self.result_dt = ""
        self.item_list = []
        self.current_item = {}
        
    def get_imports(self):
        try:
            response_data = {
                "resultCd": "000",
                "resultMsg": "Success",
                "resultDt": "2024-08-05T00:00:00",
                "data": {
                    "itemList": [
                        {
                            "taskCd": "2239078",
                            "dclDe": "-1",
                            "itemSeq": 1,
                            "dclNo": "C3460-2019-TZDL",
                            "hsCd": "20055900000",
                            "itemNm": "Back Packs",
                            "imptItemsttsCd": "2",
                            "orgnNatCd": "BR",
                            "exptNatCd": "BR",
                            "pkg": 2922,
                            "pkgUnitCd": "WRAP",
                            "qty": 19946,
                            "qtyUnitCd": "EA",
                            "totWt": 19945.57,
                            "netWt": 19945.57,
                            "spplrNm": "ODERICH CONSERVA QUALIDADE\nBRASIL",
                            "agntNm": "BN METRO Ltd",
                            "invcFcurAmt": 296865.6,
                            "invcFcurCd": "USD",
                            "invcFcurExcrt": 929.79
                        }
                    ]
                }
            }

            if response_data.get("resultCd") == "000":
                self.result_msg = response_data.get("resultMsg", "")
                self.result_dt = response_data.get("resultDt", "")
                data = response_data.get("data", {})
                self.item_list = data.get("itemList", [])

                if self.item_list:
                    item = self.item_list[0]

                    self.current_item = {
                        "task_cd": item.get("taskCd", ""),
                        "dcl_de": item.get("dclDe", ""),
                        "item_seq": item.get("itemSeq", ""),
                        "dcl_no": item.get("dclNo", ""),
                        "hs_cd": item.get("hsCd", ""),
                        "item_nm": item.get("itemNm", ""),
                        "impt_itemstts_cd": item.get("imptItemsttsCd", ""),
                        "orgn_nat_cd": item.get("orgnNatCd", ""),
                        "expt_nat_cd": item.get("exptNatCd", ""),
                        "pkg": item.get("pkg", ""),
                        "pkg_unit_cd": item.get("pkgUnitCd") or "PCS",
                        "qty": item.get("qty") or "0",
                        "qty_unit_cd": item.get("qtyUnitCd") or "KGM",
                        "tot_wt": item.get("totWt", ""),
                        "net_wt": item.get("netWt", ""),
                        "spplr_nm": item.get("spplrNm", "").replace('\n', ' '),
                        "agnt_nm": item.get("agntNm", ""),
                        "invc_fcur_amt": item.get("invcFcurAmt", ""),
                        "invc_fcur_cd": item.get("invcFcurCd", ""),
                        "invc_fcur_excrt": item.get("invcFcurExcrt", "")
                    }

                    print("\n--- Current Item Data ---")
                    for key, value in self.current_item.items():
                        print(f"{key}: {value}")

                return {
                    "status": "success",
                    "result_msg": self.result_msg,
                    "result_dt": self.result_dt,
                    "items": self.item_list
                }

            else:
                print("Error fetching imports")
                print(f"Response: {response_data}")
                return None

        except Exception as e:
            print(f"Failed: {e}")
            return None


class CreateItem(GetItems, Connection):
    def __init__(self, host, user, password, database):
        GetItems.__init__(self)
        Connection.__init__(self, host, user, password, database)
        self.required_fields = [
            'task_cd', 'dcl_de', 'item_nm', 
            'orgn_nat_cd', 'qty', 'pkg_unit_cd', 'qty_unit_cd'
        ]

    def validate_data(self):
        missing_fields = [field for field in self.required_fields 
                         if not self.current_item.get(field)]
        
        if missing_fields:
            print(f"Missing required fields: {missing_fields}")
            return False
        
        try:
            float(self.current_item["qty"])
        except ValueError:
            print(f"Invalid quantity value: {self.current_item['qty']}")
            return False

        return True

    def create(self):
        if not self.current_item:
            print("No item data available. Call get_imports() first.")
            return None
        
        if not self.validate_data():
            return None

        random_num = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        name = f"IMPORT{self.current_item['orgn_nat_cd']}{self.current_item['qty_unit_cd']}{random_num}"
        item_group = "Imports"
        country_zm = "Zambia"
        unit_of_measure_name = "N / A"
        packaging_name = "N / A"       
        country_name = "N / A"          

        try:
            pkgcode = PackagingUnitCode.objects.get(code=self.current_item["pkg_unit_cd"])
            packaging_name = pkgcode.code_name or "N / A"
        except PackagingUnitCode.DoesNotExist:
            print("PackagingUnitCode not found, using default")
        except Exception as e:
            print(f"Error getting packaging code: {e}")

        try:
            unit_measure = UnitOfMeasure.objects.get(code=self.current_item["qty_unit_cd"])
            unit_of_measure_name = unit_measure.code_name or "N / A"
        except UnitOfMeasure.DoesNotExist:
            print("UnitOfMeasure not found, using default")
        except Exception as e:
            print(f"Error getting unit of measure: {e}")

        try:
            origin_country = Country.objects.get(code=self.current_item["orgn_nat_cd"])
            country_name = origin_country.name
        except Country.DoesNotExist:
            print("Country not found, using default")
        except Exception as e:
            print(f"Error getting country code: {e}")

        try:
            cursor = self.conn.cursor()
            for uom in [self.current_item["qty_unit_cd"], self.current_item["pkg_unit_cd"]]:
                cursor.execute("SELECT name FROM `tabUOM` WHERE name = %s", (uom,))
                if not cursor.fetchone():
                    cursor.execute("INSERT INTO `tabUOM` (name, creation, modified) VALUES (%s, NOW(), NOW())", (uom,))
                    print(f"Created missing UOM: {uom}")

            query = """
                INSERT INTO tabItem 
                (name, item_name, opening_stock, stock_uom, country_of_origin,
                 custom_task_cd, custom_dcl__de,
                 custom_origin_place_code, custom_packaging_unit_code, item_group, disabled, custom_imptitemsttscd, custom_hscd)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                name,
                self.current_item["item_nm"],
                float(self.current_item["qty"]),
                "Acre",
                country_zm,
                self.current_item["task_cd"],
                self.current_item["dcl_de"],
                country_name,
                packaging_name,
                item_group,
                1,
                self.current_item["impt_itemstts_cd"],
                self.current_item["hs_cd"],
            )

            cursor.execute(query, values)
            self.conn.commit()

            print(f"\nItem created successfully with name: {name}")
            return name

        except Error as e:
            print(f"Database error: {e}")
            self.conn.rollback()
            return None
        finally:
            if cursor:
                cursor.close()


class CreatePurchase(GetItems, Connection):
    def __init__(self, host, user, password, database):
        GetItems.__init__(self)
        Connection.__init__(self, host, user, password, database)

    def get_random_purchase_invoice_name(self, cursor):
        year = datetime.today().year
        prefix = f"IMPORT-PINV-{year}-" 
        while True:
            random_digits = str(random.randint(0, 99999)).zfill(5)
            candidate = prefix + random_digits
            cursor.execute("SELECT name FROM `tabPurchase Invoice` WHERE name = %s", (candidate,))
            if not cursor.fetchone():
                return candidate

    def create_purchase_invoice(self, item_name):
        cursor = None
        try:
            cursor = self.conn.cursor()
            name = self.get_random_purchase_invoice_name(cursor)
            posting_date = datetime.today().strftime("%Y-%m-%d")
            supplier_name = self.current_item.get("spplr_nm", "Dummy Supplier")

            # Ensure supplier exists
            cursor.execute("SELECT name FROM tabSupplier WHERE name = %s", (supplier_name,))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO tabSupplier (name, supplier_name, creation, modified)
                    VALUES (%s, %s, NOW(), NOW())
                """, (supplier_name, supplier_name))
                print(f"Created new supplier: {supplier_name}")

            # Ensure company exists
            cursor.execute("SELECT name FROM tabCompany LIMIT 1")
            company_row = cursor.fetchone()
            if not company_row:
                print("No company found in tabCompany.")
                return None
            company_name = company_row[0]

            # Ensure UOM exists
            cursor.execute("SELECT name FROM `tabUOM` WHERE name = %s", (self.current_item["qty_unit_cd"],))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO `tabUOM` (name, creation, modified) VALUES (%s, NOW(), NOW())", ("Acre"))
                print(f"Created missing UOM: {self.current_item['qty_unit_cd']}")

            currency = "ZMW"
            conversion_rate = 1.0
            amount = float(self.current_item.get("invc_fcur_amt") or 0.0)
            qty = float(self.current_item.get("qty") or 0.0)
            rate = amount / qty if qty else 0

            cursor.execute("""
                INSERT INTO `tabPurchase Invoice`
                (name, supplier, title, posting_date, bill_date, company, currency, conversion_rate, docstatus, naming_series, creation, modified)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1, %s, NOW(), NOW())
            """, (
                name, supplier_name, supplier_name,  posting_date, posting_date, company_name,
                currency, conversion_rate, "ACC-PINV"
            ))

            cursor.execute("""
                INSERT INTO `tabPurchase Invoice Item`
                (name, parent, parenttype, parentfield, item_code, item_name, qty, uom, stock_uom, rate, amount, creation, modified, idx)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s)
            """, (
                str(uuid.uuid4()), name, "Purchase Invoice", "items",
                item_name, self.current_item["item_nm"],
                qty, self.current_item["qty_unit_cd"], self.current_item["qty_unit_cd"],
                rate, amount, 1
            ))

            self.conn.commit()
            print(f"✅ Purchase Invoice created successfully: {name}")
            return name

        except Error as e:
            print(f"Error creating Purchase Invoice: {e}")
            self.conn.rollback()
            return None
        finally:
            if cursor:
                cursor.close()


# ========== RUN THE SCRIPT ==========

def run_import_process(request):
    host = "localhost"
    user = "root"
    password = "root"
    database = "_7fb1f4533ec3ac7c"

    item_creator = CreateItem(host, user, password, database)
    import_data = item_creator.get_imports()

    if import_data and import_data["status"] == "success":
        created_item_name = item_creator.create()
        if created_item_name:
            purchase_creator = CreatePurchase(host, user, password, database)
            purchase_creator.current_item = item_creator.current_item
            invoice_name = purchase_creator.create_purchase_invoice(created_item_name)
            purchase_creator.close()
            if invoice_name:
                item_creator.close()
                return HttpResponse(f"Success: {created_item_name} & {invoice_name}")
            return HttpResponse("Failed to create purchase invoice")
        else:
            return HttpResponse("Failed to create item")
    else:
        return HttpResponse("Failed to fetch import data")


