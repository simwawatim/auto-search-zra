import mysql.connector
from mysql.connector import Error
import requests
import uuid
from datetime import datetime

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
                print("✅ Connected to MySQL database")
        except Error as e:
            print(f"❌ Error connecting to MySQL: {e}")

    def get_imports(self):
        url = "http://0.0.0.0:7000/api/imports?last_request_date=2024-01-01T00:00:00"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                print("📦 Imports fetched successfully")

                item_list = data.get("data", {}).get("itemList", [])
                print(f"🔢 Number of items fetched: {len(item_list)}")

                # Create one purchase order per batch
                purchase_order_id = self.create_purchase_order()
                if not purchase_order_id:
                    print("❌ Failed to create Purchase Order. Aborting.")
                    return []

                for item in item_list:
                    item_data = self.format_item(item)

                    if item_data:
                        item_code = self.create_item(*item_data)
                        if item_code:
                            self.link_to_purchase_order(purchase_order_id, item_code, item)
                    else:
                        print("⚠️ Skipping item due to missing required fields.")
                return item_list
            else:
                print(f"❌ Failed to fetch imports: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Error fetching imports: {e}")
            return []

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
            print(f"❌ Error formatting item: {e}")
            return None

    def create_item(self, item_name, item_code, item_group, origin_code, pkg_unit):
        try:
            cursor = self.conn.cursor()

            # Check if item already exists
            cursor.execute("SELECT name FROM tabItem WHERE item_code = %s", (item_code,))
            result = cursor.fetchone()
            if result:
                print(f"✅ Item already exists: {item_name} → {result[0]}")
                return item_code  # Use item_code for linking

            name = str(uuid.uuid4())
            sql = """
            INSERT INTO `tabItem` 
            (name, item_name, item_code, item_group, custom_origin_place_code, custom_packaging_unit_code, creation, modified)
            VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
            """
            values = (name, item_name, item_code, item_group, origin_code, pkg_unit)
            cursor.execute(sql, values)
            self.conn.commit()
            print(f"✅ Item created: {item_name} → {name}")
            return item_code
        except Error as e:
            print(f"❌ Error inserting item: {e}")
            return None

    def create_purchase_order(self):
        try:
            cursor = self.conn.cursor()
            name = f"PO-{str(uuid.uuid4())[:8]}"
            sql = """
            INSERT INTO `tabPurchase Order` 
            (name, supplier, transaction_date, company, currency, docstatus, creation, modified)
            VALUES (%s, %s, %s, %s, %s, 0, NOW(), NOW())
            """
            values = (name, "Dummy Supplier", datetime.today().date(), "Dummy Company", "USD")
            cursor.execute(sql, values)
            self.conn.commit()
            print(f"📄 Purchase Order created: {name}")
            return name
        except Error as e:
            print(f"❌ Error creating Purchase Order: {e}")
            return None

    def link_to_purchase_order(self, purchase_order_id, item_code, item):
        try:
            cursor = self.conn.cursor()

            sql = """
            INSERT INTO `tabPurchase Order Item` 
            (name, parent, parenttype, parentfield, item_code, qty, uom, rate, amount, creation, modified)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """
            qty = item.get("qty", 0)
            uom = item.get("qtyUnitCd", "Unit")
            invcFcurAmt = item.get("invcFcurAmt", 0)
            rate = round(invcFcurAmt / qty, 2) if qty else 0
            amount = invcFcurAmt

            values = (
                str(uuid.uuid4()),    # name of Purchase Order Item record
                purchase_order_id,    # parent (Purchase Order name)
                "Purchase Order",     # parenttype
                "items",              # parentfield - child table fieldname in Purchase Order
                item_code,
                qty,
                uom,
                rate,
                amount
            )

            cursor.execute(sql, values)
            self.conn.commit()
            print(f"🔗 Linked item to Purchase Order: {item_code} → {purchase_order_id}")
        except Error as e:
            print(f"❌ Error linking item to Purchase Order: {e}")

if __name__ == "__main__":
    db = Connection("localhost", "root", "root", "_19ba3414f40a9844")
    db.get_imports()
