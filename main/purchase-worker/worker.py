from mysql.connector import Error
from datetime import datetime
import mysql.connector
import requests
import random
import uuid
import json

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
        url = "http://0.0.0.0:7000/api/imports?last_request_date=2024-01-01T00:00:00"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            response_data = response.json()
            
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
                        "pkg_unit_cd": item.get("pkgUnitCd") or "PCS",       # Default
                        "qty": item.get("qty") or "0",                       # Default
                        "qty_unit_cd": item.get("qtyUnitCd") or "KGM",      # Default
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
                print(f"Response: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Invalid JSON response: {e}")
            if 'response' in locals():
                print(f"Raw response: {response.text}")
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
        """Validate that all required fields have values"""
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
        
        try:
            cursor = self.conn.cursor()
            
            query = """
                INSERT INTO tabItem 
                (name, item_name, opening_stock, stock_uom, country_of_origin,
                 custom_task_cd, custom_dcl__de, 
                 custom_origin_place_code, custom_packaging_unit_code, item_group, disabled)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                name,
                self.current_item["item_nm"],
                float(self.current_item["qty"]),
                self.current_item["qty_unit_cd"],
                self.current_item["orgn_nat_cd"],
                self.current_item["task_cd"],
                self.current_item["dcl_de"],
                self.current_item["orgn_nat_cd"],
                self.current_item["pkg_unit_cd"],
                item_group,
                1
            )

            print("\n--- Executing Query ---")
            print("Query:", query)
            print("Values:", values)

            cursor.execute(query, values)
            self.conn.commit()
            
            print(f"\n✅ Item created successfully with name: {name}")
            
            cursor.execute("SELECT * FROM tabItem WHERE name = %s", (name,))
            inserted_item = cursor.fetchone()
            
            if inserted_item:
                print("\n--- Inserted Item Details ---")
                print(f"Name: {inserted_item[0]}")
                print(f"Item Name: {inserted_item[9]}")
                print(f"Opening Stock: {inserted_item[15]}")
                print(f"Custom Task CD: {inserted_item[77]}")
                print(f"Custom DCL DE: {inserted_item[78]}")
                print(f"Custom Origin Place: {inserted_item[76]}")
                print(f"Custom Packaging Unit: {inserted_item[77]}")
            else:
                print("⚠️ Item was inserted but could not be retrieved for verification")
            
            return name

        except Error as e:
            print(f"⛔ Database error: {e}")
            self.conn.rollback()
            return None
        finally:
            if cursor:
                cursor.close()


if __name__ == "__main__":
    # Initialize with your database credentials
    item_creator = CreateItem(
        host="localhost",
        user="root",
        password="root",
        database="_7fb1f4533ec3ac7c"
    )
    
    print("\n=== Fetching Import Data ===")
    import_data = item_creator.get_imports()
    
    if import_data and import_data["status"] == "success":
        print("\n=== Creating Item ===")
        created_item = item_creator.create()
        
        if not created_item:
            print("Failed to create item")
    else:
        print("Failed to fetch import data")
    
    item_creator.close()
