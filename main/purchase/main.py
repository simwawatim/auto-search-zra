import uuid
from mysql.connector import Error
from datetime import datetime
import mysql.connector
import requests
import random
import json
import re


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

class GetPurchase():
    def get_purchase_zra_client(self):
        purchase_data = {
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
                    "stockRlsDt": "null",
                    "totItemCnt": 1,
                    "totTaxblAmt": 86.2069,
                    "totTaxAmt": 13.7931,
                    "totAmt": 100,
                    "remark": "null",
                    "itemList": [
                        {
                        "itemSeq": 1,
                        "itemCd": "20044",
                        "itemClsCd": "50102517",
                        "itemNm": "ChickenWings",
                        "bcd": "null",
                        "pkgUnitCd": "BA",
                        "pkg": 0,
                        "qtyUnitCd": "BE",
                        "qty": 1,
                        "prc": 100,
                        "splyAmt": 100,
                        "dcRt": 0,
                        "dcAmt": 0,
                        "vatCatCd": "A",
                        "iplCatCd": "null",
                        "tlCatCd": "null",
                        "exciseTxCatCd": "null",
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
                    ],
                    "resultCd": "000",
                    "resultMsg": "It is succeeded",
                    "resultDt": "20240510103403",
                    "data": "null"
                    }
        return purchase_data
    
class CreateItem(GetPurchase):
    def __init__(self):
        super().__init__()
        self.db_connection = Connection("localhost", "root", "root", "_7fb1f4533ec3ac7c")

    def create_item(self):
        items_data = self.get_purchase_zra_client()
        first_sale = items_data["saleList"][0] 
        formated_item = first_sale["itemList"]
        return formated_item

    def insert_item(self):
        items_to_insert = self.create_item()

        if self.db_connection.conn and self.db_connection.conn.is_connected():
            cursor = self.db_connection.conn.cursor()
            
            sql = """INSERT INTO purchase_items 
                     (item_seq, item_cd, item_cls_cd, item_nm, bcd, pkg_unit_cd, pkg, qty_unit_cd, qty, prc, sply_amt, dc_rt, dc_amt, vat_cat_cd, ipl_cat_cd, tl_cat_cd, excise_tx_cat_cd, vat_taxbl_amt, excise_taxbl_amt, ipl_taxbl_amt, tl_taxbl_amt, taxbl_amt, vat_amt, ipl_amt, tl_amt, excise_tx_amt, tot_amt) 
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            
            for item in items_to_insert:
                values = (
                    item.get("itemSeq"),
                    item.get("itemCd"),
                    item.get("itemClsCd"),
                    item.get("itemNm"),
                    item.get("bcd"),
                    item.get("pkgUnitCd"),
                    item.get("pkg"),
                    item.get("qtyUnitCd"),
                    item.get("qty"),
                    item.get("prc"),
                    item.get("splyAmt"),
                    item.get("dcRt"),
                    item.get("dcAmt"),
                    item.get("vatCatCd"),
                    item.get("iplCatCd"),
                    item.get("tlCatCd"),
                    item.get("exciseTxCatCd"),
                    item.get("vatTaxblAmt"),
                    item.get("exciseTaxblAmt"),
                    item.get("iplTaxblAmt"),
                    item.get("tlTaxblAmt"),
                    item.get("taxblAmt"),
                    item.get("vatAmt"),
                    item.get("iplAmt"),
                    item.get("tlAmt"),
                    item.get("exciseTxAmt"),
                    item.get("totAmt")
                )
                try:
                    cursor.execute(sql, values)
                    self.db_connection.conn.commit()
                    print(f"Record inserted successfully for item: {item.get('itemNm')}")
                except Error as e:
                    print(f"Error inserting record: {e}")
                    self.db_connection.conn.rollback()

            cursor.close()
            self.db_connection.close()
        else:
            print("Database connection not established. Cannot insert data.")


obj = CreateItem()
obj.insert_item()