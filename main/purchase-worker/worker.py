import mysql.connector
from mysql.connector import Error
import requests
import uuid
from datetime import datetime
import random

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

    def get_imports(self):
        url = "http://0.0.0.0:7000/api/imports?last_request_date=2024-01-01T00:00:00"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                print("Imports fetched successfully")

                item_list = data.get("data", {}).get("itemList", [])
                print(f"Number of items fetched: {len(item_list)}")

                for idx, item in enumerate(item_list, start=1):
                    task_cd = item.get("taskCd")
                    dcl_de_raw = item.get("dclDe", "")
                    dcl_de = self.format_date_safe(dcl_de_raw)
                    if dcl_de is None:
                        print(f"Invalid declaration date: {dcl_de_raw}. Using fallback date 1900-01-01.")
                        dcl_de = datetime(1900, 1, 1).date()

                    purchase_order_id = self.create_purchase_order(task_cd, dcl_de)
                    if not purchase_order_id:
                        print("Failed to create Purchase Order. Skipping item.")
                        continue

                    item_data = self.format_item(item)
                    if item_data:
                        item_name, item_code, item_group, origin_code, pkg_unit = item_data
                        item_internal_name = self.create_item(item_name, item_code, item_group, origin_code, pkg_unit)
                        if item_internal_name:
                            qty = item.get("qty", 0)
                            uom = "Acre"
                            self.link_to_purchase_order(purchase_order_id, item_internal_name, item_name, uom, item, qty, idx)
                    else:
                        print("Skipping item due to missing required fields.")
                return item_list
            else:
                print(f"Failed to fetch imports: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error fetching imports: {e}")
            return []

    def format_date_safe(self, dcl_de):
        try:
            if dcl_de and len(dcl_de) == 8 and dcl_de.isdigit():
                return datetime.strptime(dcl_de, "%Y%m%d").date()
        except Exception:
            pass
        return None

    def format_item(self, item):
        try:
            item_name = item.get("itemNm", "").strip()
            item_code = item.get("hsCd", "").strip()
            item_group = item.get("orgnNatCd", "").strip()
            origin_code = item.get("orgnNatCd", "").strip()
            pkg_unit = item.get("pkgUnitCd", "")
            if not item_name or not item_code or not origin_code:
                return None
            return item_name, item_code, item_group, origin_code, pkg_unit
        except Exception as e:
            print(f"Error formatting item: {e}")
            return None

    def create_item(self, item_name, item_code, item_group, origin_code, pkg_unit):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM tabItem WHERE item_code = %s", (item_code,))
            result = cursor.fetchone()
            if result:
                print(f"Item already exists: {item_name} → {result[0]}")
                return result[0]

            name = str(uuid.uuid4())
            item_group = "Products"
            sql = """
            INSERT INTO `tabItem` 
            (name, item_name, item_code, item_group, custom_origin_place_code, custom_packaging_unit_code, creation, modified)
            VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
            """
            values = (name, item_name, item_code, item_group, origin_code, pkg_unit)
            cursor.execute(sql, values)
            self.conn.commit()
            print(f"Item created: {item_name} → {name}")
            return name
        except Error as e:
            print(f"Error inserting item: {e}")
            return None

    def get_random_purchase_order_name(self, cursor):
        year = datetime.today().year
        prefix = f"PUR-ORD-{year}-"
        while True:
            random_digits = str(random.randint(0, 99999)).zfill(5)
            candidate = prefix + random_digits
            cursor.execute("SELECT name FROM `tabPurchase Order` WHERE name = %s", (candidate,))
            if not cursor.fetchone():
                return candidate

    def create_purchase_order(self, task_cd=None, dcl_de=None):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM tabSupplier WHERE name = 'Dummy Supplier'")
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO tabSupplier (name, supplier_name, creation, modified)
                    VALUES ('Dummy Supplier', 'Dummy Supplier', NOW(), NOW())
                """)
                print("Dummy Supplier created")

            cursor.execute("SELECT name FROM tabCompany LIMIT 1")
            company_row = cursor.fetchone()
            if not company_row:
                print("No company found in tabCompany. Cannot proceed.")
                return None

            company_name = company_row[0]
            name = self.get_random_purchase_order_name(cursor)
            naming_series_value = "PUR-ORD"

            sql = """
            INSERT INTO `tabPurchase Order` 
            (name, supplier, transaction_date, company, currency, docstatus, naming_series, 
             custom_custom_import, custom_taskcd, custom_dclde, creation, modified)
            VALUES (%s, %s, %s, %s, %s, 0, %s, %s, %s, %s, NOW(), NOW())
            """
            dcl_de_str = dcl_de.strftime("%Y-%m-%d") if dcl_de else None
            values = (
                name,
                "Dummy Supplier",
                datetime.today().date(),
                company_name,
                "ZMW",
                naming_series_value,
                1,          # custom_import
                task_cd,    # custom_taskcd
                dcl_de_str  # custom_dclde as string in 'YYYY-MM-DD' format
            )
            cursor.execute(sql, values)
            self.conn.commit()
            print(f"Purchase Order created: {name} | taskCd: {task_cd} | dclDe: {dcl_de_str}")
            return name
        except Error as e:
            print(f"Error creating Purchase Order: {e}")
            return None

    def link_to_purchase_order(self, purchase_order_id, item_internal_name, item_name, uom, item, qty, nos):
        try:
            cursor = self.conn.cursor()
            invcFcurAmt = item.get("invcFcurAmt", 0)
            rate = round(invcFcurAmt / qty, 2) if qty else 0
            amount = invcFcurAmt
            stock_uom = uom
            sql = """
            INSERT INTO `tabPurchase Order Item` 
            (name, parent, parenttype, parentfield, item_code, item_name, qty, uom, stock_uom, rate, amount, creation, modified, idx)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s)
            """
            values = (
                str(uuid.uuid4()),
                purchase_order_id,
                "Purchase Order",
                "items",
                item_internal_name,
                item_name,
                qty,
                uom,
                stock_uom,
                rate,
                amount,
                nos
            )
            cursor.execute(sql, values)
            self.conn.commit()
            print(f"Linked item to Purchase Order [{nos}]: {item_internal_name} → {purchase_order_id}")
        except Error as e:
            print(f"Error linking item to Purchase Order: {e}")

if __name__ == "__main__":
    db = Connection("localhost", "root", "root", "_7fb1f4533ec3ac7c")
    db.get_imports()
