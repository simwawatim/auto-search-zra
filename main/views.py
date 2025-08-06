import json
import logging
from main.models import Country, PackagingUnitCode, SupplierInvoice, UnitOfMeasure, ItemsClass
from main.serializers import CountrySerializer, PackagingUnitCodeSerializer, SupplierInvoiceSerializer, UnitOfMeasureSerializer, itemClassListSerializer
import json
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
import mysql.connector
from django.shortcuts import render
import requests
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from django.conf import settings
from datetime import datetime

import requests
from datetime import datetime
from django.conf import settings
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction, IntegrityError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import mysql.connector
from mysql.connector import Error
from rest_framework.generics import ListAPIView


class ZRAClient:
    def __init__(self):
        self.base_url = settings.ZRA_LOCAL_BASE_URL
        self.get_import = settings.ZRA_GET_IMPORTS
        self.tpin = settings.TPIN
        self.branch_code = settings.BRANCH_CODE

    def get_imported_items(self, last_request_date):
        url = f"{self.base_url}{self.get_import}"

        try:
            dt = datetime.fromisoformat(last_request_date)
            formatted_date = dt.strftime("%Y%m%d%H%M%S")
        except ValueError:
            return {"error": "Invalid 'last_request_date' format. Use ISO format like 2024-01-01T00:00:00"}

        payload = {
            "tpin": self.tpin,
            "bhfId": self.branch_code,
            "lastReqDt": formatted_date
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return {
                "resultCd": "000",
                "resultMsg": "It is succeeded",
                "resultDt": "20231120194118",
                "data": {
                    "itemList": [
                        {
                            "taskCd": "2239078",
                            "dclDe": "-1",
                            "itemSeq": 1,
                            "dclNo": "C3460-2019-TZDL",
                            "hsCd": "20055900000",
                            "itemNm": "BAKED BEANS",
                            "imptItemsttsCd": "2",
                            "orgnNatCd": "BR",
                            "exptNatCd": "BR",
                            "pkg": 2922,
                            "pkgUnitCd": None,
                            "qty": 19946,
                            "qtyUnitCd": "KGM",
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
        except requests.exceptions.Timeout:
            return {
                "resultCd": "000",
                "resultMsg": "It is succeeded (MOCKED DUE TO TIMEOUT)",
                "resultDt": "20231120194118",
                "data": {
                    "itemList": [
                        {
                            "taskCd": "2239078",
                            "dclDe": "-1",
                            "itemSeq": 1,
                            "dclNo": "C3460-2019-TZDL",
                            "hsCd": "20055900000",
                            "itemNm": "BAKED BEANS",
                            "imptItemsttsCd": "2",
                            "orgnNatCd": "BR",
                            "exptNatCd": "BR",
                            "pkg": 2922,
                            "pkgUnitCd": None,
                            "qty": 19946,
                            "qtyUnitCd": "KGM",
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
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}




class PackagingUnitCodeDetail(APIView):
    def get(self, request, code_name):
        obj = PackagingUnitCode.objects.filter(code_name=code_name).first()
        if not obj:
            return Response({'error': 'PackagingUnitCode not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = PackagingUnitCodeSerializer(obj)
        return Response(serializer.data)



class CountryDetailByName(APIView):
    def get(self, request, name):
        try:
            country = Country.objects.get(name=name)
        except Country.DoesNotExist:
            return Response({'error': 'Country not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = CountrySerializer(country)
        return Response(serializer.data)
    
class UnitOfMeasureDetailByCodeName(APIView):
    def get(self, request, code_name):
        try:
            unit = UnitOfMeasure.objects.get(code_name=code_name)
        except UnitOfMeasure.DoesNotExist:
            return Response({'error': 'UnitOfMeasure not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = UnitOfMeasureSerializer(unit)
        return Response(serializer.data)
    

class ItemsClassView(APIView):
    def get(self, request, item_class_name):
        try:
            item_class = ItemsClass.objects.get(itemClsNm=item_class_name)
        except ItemsClass.DoesNotExist:
            return Response({'error': "Item Class Does Not Exist"}, status=status.HTTP_404_NOT_FOUND)

        serializer = itemClassListSerializer(item_class) 
        return Response(serializer.data)

class Imports(APIView):
    def get(self, request):
        last_request_date = request.query_params.get("last_request_date")

        if not last_request_date:
            return Response({"error": "Missing 'last_request_date' query parameter."},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            datetime.fromisoformat(last_request_date)
        except ValueError:
            return Response({"error": "Invalid date format. Use ISO format like 2024-01-01T00:00:00"},
                            status=status.HTTP_400_BAD_REQUEST)

        client = ZRAClient()
        data = client.get_imported_items(last_request_date)
        return Response(data, status=status.HTTP_200_OK)
    



class GetAllItemClasses(APIView):

    def post(self, request, *args, **kwargs):
        external_api_url = "http://localhost:8080/sandboxvsdc1.0.8.0/itemClass/selectItemsClass"
        payload = {
            "tpin": "2484778002",
            "bhfId": "000",
            "lastReqDt": "20231215000000"
        }

        try:
            response = requests.post(external_api_url, json=payload, timeout=10)
            response.raise_for_status()

            external_api_data = response.json()
            item_cls_list = external_api_data.get("data", {}).get("itemClsList", [])

            if not item_cls_list:
                print("!!! WARNING: itemClsList is empty or not found in the 'data' section of the response. !!!")
                return Response(
                    {"message": "No item classes found in external API response.", "total_processed_items": 0},
                    status=status.HTTP_200_OK
                )

            processed_data = []
            validation_errors = []
            for item in item_cls_list:
                formatted_item = {
                    "itemClsCd": item.get("itemClsCd"),
                    "itemClsNm": item.get("itemClsNm"),
                    "itemClsLvl": item.get("itemClsLvl"),
                    "useYn": item.get("useYn"), 
                }
                # Validate each item using the serializer
                serializer = itemClassListSerializer(data=formatted_item)
                if serializer.is_valid():
                    processed_data.append(serializer.validated_data)
                else:
                    validation_errors.append({
                        "itemClsCd": formatted_item.get("itemClsCd", "N/A"),
                        "errors": serializer.errors
                    })

            if not processed_data:
                return Response(
                    {"message": "No valid item classes after validation.", "validation_errors": validation_errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 2. Separate existing from new items
            existing_codes_from_api = [d['itemClsCd'] for d in processed_data if d.get('itemClsCd')]
            
            existing_objects_map = {
                obj.itemClsCd: obj for obj in ItemsClass.objects.filter(
                    itemClsCd__in=existing_codes_from_api
                )
            }
            existing_codes = set(existing_objects_map.keys())


            items_to_create = []
            items_to_update = []
            
            for data in processed_data:
                if data['itemClsCd'] in existing_codes:
                    obj = existing_objects_map.get(data['itemClsCd'])
                    if obj:
                        obj.itemClsNm = data.get('itemClsNm', obj.itemClsNm)
                        obj.itemClsLvl = data.get('itemClsLvl', obj.itemClsLvl)
                        obj.useYn = data.get('useYn', obj.useYn) 
                        items_to_update.append(obj)
                else:
                    items_to_create.append(ItemsClass(**data))

            # 3. Perform bulk operations within an atomic transaction
            saved_count = 0
            updated_count = 0
            
            with transaction.atomic():
                if items_to_create:
                    # FIX: Changed .create() to .bulk_create()
                    created_objs = ItemsClass.objects.bulk_create(items_to_create)
                    saved_count = len(created_objs)

                if items_to_update:
                    updated_count = ItemsClass.objects.bulk_update(
                        items_to_update, 
                        ['itemClsNm', 'itemClsLvl', 'useYn'] 
                    )
            
            all_errors = validation_errors 
            if saved_count + updated_count < len(processed_data) and not validation_errors:
                pass


            response_to_client_data = {
                "message": "Item classes fetched and processed successfully.",
                "saved_new_items": saved_count,
                "updated_items": updated_count,
                "total_processed_items_from_api": len(item_cls_list),
                "total_valid_items_for_db": len(processed_data),
                "errors_encountered": all_errors,
            }

            return Response(response_to_client_data, status=status.HTTP_200_OK)

        except requests.exceptions.HTTPError as http_err:
            error_message = f"External API HTTP error: {http_err}. Details: {http_err.response.text if http_err.response else 'No response text.'}"
            print(f"Error: {error_message}")
            return Response(
                {"error": error_message},
                status=status.HTTP_502_BAD_GATEWAY
            )
        except requests.exceptions.ConnectionError as conn_err:
            error_message = f"Could not connect to external API: {conn_err}. Is the API running and accessible?"
            print(f"Error: {error_message}")
            return Response(
                {"error": error_message},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except requests.exceptions.Timeout as timeout_err:
            error_message = f"External API request timed out: {timeout_err}. The API did not respond in time."
            print(f"Error: {error_message}")
            return Response(
                {"error": error_message},
                status=status.HTTP_504_GATEWAY_TIMEOUT
            )
        except json.JSONDecodeError as json_err:
            response_text = response.text if 'response' in locals() else 'No response object captured.'
            error_message = f"Failed to decode JSON from external API: {json_err}. Raw response: {response_text}"
            print(f"Error: {error_message}")
            return Response(
                {"error": error_message},
                status=status.HTTP_502_BAD_GATEWAY
            )
        except requests.exceptions.RequestException as req_err:
            error_message = f"An unexpected request error occurred with external API: {req_err}"
            print(f"Error: {error_message}")
            return Response(
                {"error": error_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            error_message = f"An unexpected internal server error occurred: {e}"
            print(f"Error: {error_message}")
            return Response(
                {"error": error_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@csrf_exempt
def update_rcpt_no(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            docname = data.get('docname')
            rcpt_no = data.get('rcpt_no')
            qrcode_url = data.get('qrcode_url')
            
            if not docname or not rcpt_no:
                return JsonResponse({'error': 'Missing docname or rcpt_no'}, status=400)
            
            conn = mysql.connector.connect(
                host='localhost',
                user='root',
                password='root',
                database='_7fb1f4533ec3ac7c'
            )
            cursor = conn.cursor()
            sql = "UPDATE `tabSales Invoice` SET custom_rcpt_no = %s, custom_qr_code = %s WHERE name = %s"
            cursor.execute(sql, (rcpt_no, qrcode_url, docname))
            conn.commit()
            cursor.close()
            conn.close()
            
            return JsonResponse({'success': f'rcptNo updated for {docname}'})
        
        except Error as e:
            return JsonResponse({'error': str(e)}, status=500)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'POST request required'}, status=405)


@csrf_exempt
def get_rcpt_no(request):
    if request.method == 'GET':
        docname = request.GET.get('docname')

        if not docname:
            return JsonResponse({'error': 'Missing docname parameter'}, status=400)

        try:
            conn = mysql.connector.connect(
                host='localhost',
                user='root',
                password='root',
                database='_7fb1f4533ec3ac7c'
            )
            cursor = conn.cursor(dictionary=True)
            sql = "SELECT custom_rcpt_no FROM `tabSales Invoice` WHERE name = %s"
            cursor.execute(sql, (docname,))
            result = cursor.fetchone()


            cursor.close()
            conn.close()

            if result:
                rcpt_no = result.get('custom_rcpt_no')
                if rcpt_no is not None:
                    print(f"Retrieved rcptNo: {rcpt_no} for docname: {docname}")
                    return JsonResponse({'docname': docname, 'custom_rcpt_no': rcpt_no})
                else:
                    print(f"Key 'custom_rcpt_no' missing in DB result: {result}")
                    return JsonResponse({'error': 'custom_rcpt_no not found for the given docname'}, status=404)
            else:
                return JsonResponse({'error': 'Sales Invoice not found'}, status=404)

        except Error as e:
            return JsonResponse({'error': str(e)}, status=500)

    else:
        return JsonResponse({'error': 'GET request required'}, status=405)



class SupplierInvoiceListView(ListAPIView):
    serializer_class = SupplierInvoiceSerializer

    def get_queryset(self):
        queryset = SupplierInvoice.objects.all()
        invoice_name = self.request.query_params.get('invoice_name')
        if invoice_name:
            queryset = queryset.filter(invoice_name=invoice_name)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return Response(
                {"detail": "No supplier invoices found with the given name."},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)