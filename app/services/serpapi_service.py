import requests
from flask import current_app
from config.settings import config as default_config

class SerpApiService:
    def __init__(self, api_key=None):
        try:
            self.api_key = api_key or current_app.config.get('SERPAPI_KEY') or default_config.SERPAPI_KEY
        except:
            self.api_key = api_key or default_config.SERPAPI_KEY
        self.base_url = "https://serpapi.com/search"
    
    def _execute_request(self, params):
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except:
            # Fallback SSL e tratamento silencioso de erro
            try:
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                response = requests.get(self.base_url, params=params, timeout=30, verify=False)
                response.raise_for_status()
                return response.json()
            except:
                return {'error': "Falha de conexão"}

    def search_business(self, business_name, location=None):
        params = {
            "engine": "google_maps",
            "q": business_name,
            "type": "search",
            "api_key": self.api_key
        }
        if location:
            params["q"] += f", {location}"
        else:
            params["ll"] = "@-25.2637,57.5759,14z"
        return self._execute_request(params)

    def get_business_details(self, place_id):
        params = {
            "engine": "google_maps",
            "type": "place",
            "place_id": place_id,
            "api_key": self.api_key
        }
        return self._execute_request(params)

    def analyze_gmb_profile(self, business_name, location=None):
        raw_response = self.search_business(business_name, location)
        
        if not raw_response or 'error' in raw_response:
            return {'score': 0, 'report': {'error': 'Not found'}, 'raw_data': None}
        
        # SerpApi google_maps results are often in local_results list
        business = {}
        if 'local_results' in raw_response and len(raw_response['local_results']) > 0:
            business = raw_response['local_results'][0]
        elif 'place_results' in raw_response:
            business = raw_response['place_results']
        else:
            # Fallback to root if it contains common GMB fields
            business = raw_response
            
        if not business or 'title' not in business:
             return {'score': 0, 'report': {'error': 'Negative match'}, 'raw_data': None}

        details = business if ('operating_hours' in business and 'address' in business) else None
        if not details and 'place_id' in business:
            details = self.get_business_details(business['place_id'])
        
        results = self._evaluate_criteria(business, details)
        total_score = sum(item['score'] for item in results)
        
        # Gerar recomendações e problemas críticos
        critical_items = [r for r in results if r['status'] == 'critical']
        top_critical = [{'name': r['name_es'], 'message': r['message']} for r in critical_items[:3]]
        
        recommendations = []
        for item in critical_items:
            if item['id'] == 1: recommendations.append("Configurar los horarios de atención para no perder clientes potenciales.")
            elif item['id'] == 2: recommendations.append("Subir al menos 10 fotos de alta calidad de sus productos o servicios.")
            elif item['id'] == 4: recommendations.append("Completar el proceso de verificación de Google para ganar confianza y autoridad.")
            elif item['id'] == 5: recommendations.append("Vincular un sitio web profesional para mejorar la conversión.")
            elif item['id'] == 8: recommendations.append("Escribir una descripción detallada del negocio con palabras clave relevantes.")
            elif item['id'] == 14: recommendations.append("Solicitar nuevas reseñas a sus clientes actuales para mejorar el ranking.")

        # Recomendações genéricas se houver poucas específicas
        if len(recommendations) < 3:
            recommendations.append("Mantener el perfil actualizado con publicaciones semanais.")
            recommendations.append("Responder a todas las reseñas, tanto positivas como negativas.")
        
        return {
            'score': total_score,
            'report': {
                'business_name': business.get('title', business_name),
                'address': business.get('address'),
                'summary': {
                    'critical_issues_count': len(critical_items),
                    'moderate_issues_count': len([r for r in results if r['status'] == 'moderate']),
                    'positive_points_count': len([r for r in results if r['status'] == 'positive'])
                },
                'top_critical_issues': top_critical,
                'recommendations': recommendations[:5], # Máximo 5 recomendações
                'criteria': results
            }
        }

    def _evaluate_criteria(self, business, details):
        try:
            criteria = current_app.config.get('HEALTH_CHECK_CRITERIA') or default_config.HEALTH_CHECK_CRITERIA
        except:
            criteria = default_config.HEALTH_CHECK_CRITERIA
            
        # Combine data for easier lookup
        data = {**business}
        if details:
            data.update(details)
            
        results = []
        for cr in criteria:
            cid = cr['id']
            res = {
                'id': cid,
                'name_pt': cr['name_pt'],
                'name_es': cr['name_es'],
                'weight': cr['weight'],
                'type': cr['type'],
                'score': 0,
                'status': 'critical',
                'message': 'No encontrado'
            }
            
            found = False
            
            # Implementation for all 17 criteria
            if cid == 1: # Horário de Funcionamento
                found = bool(data.get('operating_hours'))
            elif cid == 2: # Fotos dos Produtos/Serviços
                photos = data.get('photos', [])
                count = len(photos) if isinstance(photos, list) else 0
                if count >= 10: 
                    found = True; res['score'] = cr['weight']
                elif count > 0: 
                    found = True; res['score'] = cr['weight'] // 2; res['status'] = 'moderate'
            elif cid == 3: # Vídeos
                # SerpApi doesn't always explicitly list videos, but sometimes they are in photos
                # We'll check for any video-like indicators or just mark social media indicators
                found = 'videos' in data or 'video_count' in data
            elif cid == 4: # Perfil Verificado
                found = data.get('verified', False)
            elif cid == 5: # Possui Site
                found = bool(data.get('website'))
            elif cid == 6: # Perguntas e Respostas
                found = bool(data.get('questions_and_answers')) or data.get('questions_count', 0) > 0
            elif cid == 7: # Posts/Publicações
                found = bool(data.get('posts')) or bool(data.get('updates'))
            elif cid == 8: # Descrição do Negócio
                desc = data.get('description', '')
                found = len(desc) > 50
            elif cid == 9: # Presença nas Redes Sociais
                found = any(x in str(data.get('website', '')) for x in ['facebook', 'instagram', 'linkedin'])
            elif cid == 10: # Presença no Google Maps
                found = bool(data.get('place_id')) or bool(data.get('gps_coordinates'))
            elif cid == 11: # Fotos do Exterior
                # Approximation: check if any photo tags mention exterior
                found = any('exterior' in str(p).lower() for p in data.get('photos', []))
            elif cid == 12: # Fotos do Interior
                found = any('interior' in str(p).lower() for p in data.get('photos', []))
            elif cid == 13: # Informações de Produtos e Serviços
                found = bool(data.get('menu')) or bool(data.get('products')) or bool(data.get('services'))
            elif cid == 14: # Possui Avaliações
                revs = data.get('reviews', 0)
                if revs >= 10: 
                    found = True; res['score'] = cr['weight']
                elif revs > 0:
                    found = True; res['score'] = cr['weight'] // 2; res['status'] = 'moderate'
            elif cid == 15: # Endereço Configurado
                found = bool(data.get('address'))
            elif cid == 16: # Possui Logotipo
                found = bool(data.get('thumbnail'))
            elif cid == 17: # Resposta a Avaliações
                # Advanced check: requires looking into individual reviews
                found = 'review_responses' in data or 'answered_reviews' in data

            # Finalize score and status
            if found:
                if res['score'] == 0:
                    res['score'] = cr['weight']
                
                if res['status'] == 'critical': # If wasn't already set to moderate
                    res['status'] = 'positive'
                    res['message'] = 'Encontrado'
                elif res['status'] == 'moderate':
                    res['message'] = 'Parcialmente encontrado'
            
            results.append(res)
            
        return results
