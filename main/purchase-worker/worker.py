import mysql.connector
from mysql.connector import Error
import requests
import uuid

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
                    item_name, item_code, orgnNatCd, pkg, pkgUnitCd = self.format_item(item)
                    print(f"➡️ Formatted Item -> Name: {item_name}, Code: {item_code}, Origin: {orgnNatCd}, Package: {pkg}, Unit: {pkgUnitCd}")

                    if item_name and item_code and orgnNatCd:
                        item_group = orgnNatCd  # Or your own logic to determine group
                        self.create_item(item_name, item_code, item_group, orgnNatCd, pkgUnitCd)
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
            item_name = item.get("itemNm", "")
            item_code = item.get("hsCd", "")
            item_origin_cd = item.get("orgnNatCd", "")
            item_pkg = item.get("pkg", "")
            item_pkg_unit_cd = item.get("pkgUnitCd", "")
            return item_name, item_code, item_origin_cd, item_pkg, item_pkg_unit_cd
        except Exception as e:
            print(f"❌ Error formatting item: {e}")
            return None, None, None, None, None

    def create_item(self, item_name, item_code, item_group, item_origin_cd, item_pkg_unit_cd):
        try:
            cursor = self.conn.cursor()
            sql = """
            INSERT INTO `tabItem` 
            (name, item_name, item_code, item_group, custom_origin_place_code, custom_packaging_unit_code, creation, modified)
            VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
            """
            name = str(uuid.uuid4())
            values = (name, item_name, item_code, item_group, item_origin_cd, item_pkg_unit_cd)

            cursor.execute(sql, values)
            self.conn.commit()
            print(f"✅ Item created in DB: {name}")
        except Error as e:
            print(f"❌ Error inserting item: {e}")

if __name__ == "__main__":
    db = Connection("localhost", "root", "root", "_19ba3414f40a9844")
    db.get_imports()
