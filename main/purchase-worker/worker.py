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

                for item in item_list:
                    item_data = self.format_item(item)

                    if item_data:
                        item_id = self.create_item(*item_data)
                        if item_id:
                            self.link_to_purchase(item_id, item)
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
            return name
        except Error as e:
            print(f"❌ Error inserting item: {e}")
            return None

    def link_to_purchase(self, item_id, item):
        try:
            cursor = self.conn.cursor()
            purchase_id = str(uuid.uuid4())  # Create or fetch existing purchase ID

            sql = """
            INSERT INTO `tabPurchaseItem` 
            (name, parent, item_code, qty, uom, rate, amount, creation, modified)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """
            qty = item.get("qty", 0)
            uom = item.get("qtyUnitCd", "Unit")
            rate = round(item.get("invcFcurAmt", 0) / qty, 2) if qty else 0
            amount = item.get("invcFcurAmt", 0)

            values = (
                str(uuid.uuid4()),
                purchase_id,  # You may want to relate to a real `tabPurchase` record
                item_id,
                qty,
                uom,
                rate,
                amount
            )

            cursor.execute(sql, values)
            self.conn.commit()
            print(f"🔗 Linked item to purchase: {item_id} → {purchase_id}")
        except Error as e:
            print(f"❌ Error linking item to purchase: {e}")

if __name__ == "__main__":
    db = Connection("localhost", "root", "root", "_19ba3414f40a9844")
    db.get_imports()
