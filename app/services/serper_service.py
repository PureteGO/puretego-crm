import requests
from flask import current_app
from config.settings import config as default_config

class SerperService:
    def __init__(self, api_key=None):
        self.api_key = api_key or current_app.config.get('SERPER_API_KEY') or default_config.SERPER_API_KEY
        self.base_url = "https://google.serper.dev"
        self.headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }

    def search_places(self, query, location=None, limit=10, country="py"):
        """
        Search for places/businesses. Useful for prospecting.
        """
        endpoint = f"{self.base_url}/places"
        payload = {
            "q": query,
            "gl": country,
            "hl": "es"
        }
        
        if location:
            payload["location"] = location
            
        try:
            response = requests.post(endpoint, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Formatar resultados (Passar objeto completo para Health Check)
            places = []
            for item in data.get('places', [])[:limit]:
                # Garantir campos normalizados essenciais enquanto mantém o raw data
                place_obj = item.copy()
                place_obj.update({
                    'phone': item.get('phoneNumber'),
                    'reviews': item.get('ratingCount'),
                    'place_id': item.get('placeId') or item.get('cid') # Fallback
                })
                places.append(place_obj)
            return {'success': True, 'places': places}
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': str(e)}

    def search_local_pack(self, query, location=None, country="py"):
        """
        Search specifically for Local Pack results.
        Useful for tracking map rankings.
        """
        payload = {
            "q": query,
            "gl": country,
            "hl": "es" 
        }
        
        if location:
            payload["location"] = location
            
        return self._execute_request(payload, endpoint="search")
    
    def search_organic(self, query, location=None, country="py"):
        """
        Standard organic search.
        """
        payload = {
            "q": query,
            "gl": country,
            "hl": "es"
        }
        
        if location:
            payload["location"] = location
            
        return self._execute_request(payload, endpoint="search")

    def _execute_request(self, payload, endpoint="search"):
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}

    def parse_local_rank(self, data, business_name):
        """
        Extracts the ranking position of a business from local pack results.
        Returns: integer position (1-based) or 0 if not found.
        """
        if not data or 'places' not in data:
            return 0
            
        business_normalized = business_name.lower()
        
        for place in data['places']:
            if business_normalized in place.get('title', '').lower():
                return place.get('position', 0)
        
        return 0

    def parse_organic_rank(self, data, target):
        """
        Extracts the ranking position from organic results.
        Target can be a domain (e.g., 'example.com') or a business name.
        Returns: integer position (1-based) or 0 if not found.
        """
        if not data or 'organic' not in data:
            return 0
            
        # Normalize target: remove common URL prefixes if it looks like a URL, otherwise lower case
        target_normalized = target.lower().replace('https://', '').replace('http://', '').replace('www.', '')
        
        for item in data['organic']:
            link = item.get('link', '').lower()
            title = item.get('title', '').lower()
            
            # Check if target is in the link OR in the title
            if target_normalized in link or target_normalized in title:
                return item.get('position', 0)
                
        return 0
