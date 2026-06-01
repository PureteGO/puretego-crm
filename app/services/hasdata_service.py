import requests
import logging
from flask import current_app

logger = logging.getLogger(__name__)

class HasDataService:
    """
    Serviço para integração com a API HasData (Google Maps Scraper).
    Documentação: https://docs.hasdata.com/apis/google-maps/place
    """
    
    def __init__(self, api_key=None):
        if not api_key:
            try:
                api_key = current_app.config.get('HASDATA_API_KEY')
            except Exception as e:
                logger.warning(f"Could not retrieve HASDATA_API_KEY from current_app config: {e}")
                api_key = None
        
        self.api_key = api_key or ''
        self.base_url = "https://api.hasdata.com/scrape/google-maps"
        self.headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }

    def get_place_details(self, place_id, hl="es"):
        """Busca detalhes detalhados de um local via placeId."""
        try:
            url = f"{self.base_url}/place?placeId={place_id}&hl={hl}"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"HasData Error (PlaceDetails): {str(e)}")
            return None

    def search_places(self, query, gl='py'):
        """Busca locais via query."""
        try:
            url = f"{self.base_url}/search?q={query}&gl={gl}"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get('localResults', [])
        except Exception as e:
            logger.error(f"HasData Error (Search): {str(e)}")
            return []

    def get_reviews(self, place_id=None, data_id=None):
        """Busca avaliações de um local usando placeId ou dataId."""
        try:
            params = {}
            if place_id: params['placeId'] = place_id
            if data_id: params['dataId'] = data_id
            
            if not params:
                return None

            url = "https://api.hasdata.com/scrape/google-maps/reviews"
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 400 and place_id:
                # Tenta formato antigo se falhar
                url = f"{self.base_url}/reviews?placeId={place_id}"
                response = requests.get(url, headers=self.headers, timeout=30)

            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"HasData Error (Reviews): {str(e)}")
            return None

    def get_photos(self, place_id=None, data_id=None):
        """Busca fotos de um local usando place_id ou data_id."""
        try:
            params = {}
            if place_id: params['placeId'] = place_id
            if data_id: params['dataId'] = data_id
            
            if not params:
                return None

            url = "https://api.hasdata.com/scrape/google-maps/photos"
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"HasData Error (Photos): {str(e)}")
            return None
