import requests
import json
from django.db import transaction
from django.db import models
from models import ItemsClass



def get_item_code():
    url = "http://localhost:8080/sandboxvsdc1.0.8.0/itemClass/selectItemsClass"
    
    try:
        # Make HTTP request
        response = requests.get(url)
        response.raise_for_status()
        
        # Parse JSON
        data = response.json()
        item_cls_list = data.get('data', {}).get('itemClsList', [])
        
        # Save to database
        with transaction.atomic():
            for item_data in item_cls_list:
                ItemsClass.objects.update_or_create(
                    itemClsCd=item_data.get('itemClsCd'),
                    defaults={
                        'itemClsNm': item_data.get('itemClsNm'),
                        'itemClsLvl': str(item_data.get('itemClsLvl')),
                    }
                )
        
        print(f"Successfully saved {len(item_cls_list)} items")
        
    except Exception as e:
        print(f"Error: {str(e)}")

# Run the function
if __name__ == "__main__":
    get_item_code()