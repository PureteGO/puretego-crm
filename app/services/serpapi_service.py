"""
PURETEGO CRM - SerpApi Service
Serviço de integração com SerpApi para análise do Google Meu Negócio
"""

import requests
from config.settings import config


class SerpApiService:
    """Serviço para buscar informações do Google Meu Negócio via SerpApi"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or config.SERPAPI_KEY
        self.base_url = "https://serpapi.com/search"
    
    def search_business(self, business_name, location="Paraguay"):
        """
        Busca informações de um negócio no Google Maps
        
        Args:
            business_name: Nome do negócio para buscar
            location: Localização para a busca (padrão: Paraguay)
            
        Returns:
            dict: Dados do negócio encontrado ou None
        """
        try:
            params = {
                "engine": "google_maps",
                "q": business_name,
                "ll": "@-25.2637,57.5759,14z",  # Coordenadas de Asunción, Paraguay
                "type": "search",
                "api_key": self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Retornar o primeiro resultado local
            if "local_results" in data and len(data["local_results"]) > 0:
                return data["local_results"][0]
            
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"Erro ao buscar negócio: {e}")
            return None
    
    def get_business_details(self, place_id):
        """
        Obtém detalhes completos de um negócio pelo place_id
        
        Args:
            place_id: ID do lugar no Google Maps
            
        Returns:
            dict: Detalhes completos do negócio
        """
        try:
            params = {
                "engine": "google_maps",
                "type": "place",
                "place_id": place_id,
                "api_key": self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Erro ao obter detalhes do negócio: {e}")
            return None
    
    def analyze_gmb_profile(self, business_name):
        """
        Analisa o perfil GMB de um negócio e retorna pontuação e relatório
        
        Args:
            business_name: Nome do negócio para analisar
            
        Returns:
            dict: {
                'score': int (0-100),
                'report': dict com detalhes da análise,
                'raw_data': dados brutos da API
            }
        """
        # Buscar o negócio
        business = self.search_business(business_name)
        
        if not business:
            return {
                'score': 0,
                'report': {'error': 'Negócio não encontrado'},
                'raw_data': None
            }
        
        # Obter detalhes completos se tiver place_id
        details = None
        if 'place_id' in business:
            details = self.get_business_details(business['place_id'])
        
        # Analisar os critérios
        criteria_results = self._evaluate_criteria(business, details)
        
        # Calcular pontuação total
        total_score = sum(item['score'] for item in criteria_results)
        
        return {
            'score': total_score,
            'report': {
                'business_name': business.get('title', business_name),
                'criteria': criteria_results,
                'summary': self._generate_summary(criteria_results)
            },
            'raw_data': {
                'business': business,
                'details': details
            }
        }
    
    def _evaluate_criteria(self, business, details):
        """
        Avalia cada critério do Health Check
        
        Args:
            business: Dados básicos do negócio
            details: Detalhes completos do negócio
            
        Returns:
            list: Lista de dicionários com resultado de cada critério
        """
        criteria = config.HEALTH_CHECK_CRITERIA
        results = []
        
        for criterion in criteria:
            result = {
                'id': criterion['id'],
                'name_pt': criterion['name_pt'],
                'name_es': criterion['name_es'],
                'weight': criterion['weight'],
                'type': criterion['type'],
                'score': 0,
                'status': 'critical',
                'message': ''
            }
            
            # Avaliar cada critério
            if criterion['id'] == 1:  # Horário de funcionamento
                if business.get('hours') or (details and details.get('hours')):
                    result['score'] = criterion['weight']
                    result['status'] = 'positive'
                    result['message'] = 'Horário configurado'
                else:
                    result['message'] = 'Horário não configurado'
            
            elif criterion['id'] == 2:  # Fotos dos produtos/serviços
                photos = business.get('photos', [])
                if len(photos) >= 10:
                    result['score'] = criterion['weight']
                    result['status'] = 'positive'
                    result['message'] = f'{len(photos)} fotos encontradas'
                elif len(photos) > 0:
                    result['score'] = criterion['weight'] // 2
                    result['status'] = 'moderate'
                    result['message'] = f'Apenas {len(photos)} fotos encontradas'
                else:
                    result['message'] = 'Sem fotos de produtos/serviços'
            
            elif criterion['id'] == 3:  # Vídeos
                if details and details.get('videos'):
                    result['score'] = criterion['weight']
                    result['status'] = 'positive'
                    result['message'] = 'Possui vídeos'
                else:
                    result['message'] = 'Sem vídeos'
            
            elif criterion['id'] == 4:  # Perfil verificado
                if business.get('verified') or (details and details.get('verified')):
                    result['score'] = criterion['weight']
                    result['status'] = 'positive'
                    result['message'] = 'Perfil verificado'
                else:
                    result['message'] = 'Perfil não verificado'
            
            elif criterion['id'] == 5:  # Possui site
                if business.get('website') or (details and details.get('website')):
                    result['score'] = criterion['weight']
                    result['status'] = 'positive'
                    result['message'] = 'Possui website'
                else:
                    result['message'] = 'Sem website'
            
            elif criterion['id'] == 6:  # Perguntas e respostas
                if details and details.get('questions_and_answers'):
                    result['score'] = criterion['weight']
                    result['status'] = 'positive'
                    result['message'] = 'Possui Q&A'
                else:
                    result['message'] = 'Sem perguntas e respostas'
            
            elif criterion['id'] == 7:  # Posts/Publicações
                if details and details.get('posts'):
                    result['score'] = criterion['weight']
                    result['status'] = 'positive'
                    result['message'] = 'Possui publicações'
                else:
                    result['message'] = 'Sem publicações'
            
            elif criterion['id'] == 8:  # Descrição do negócio
                description = business.get('description') or (details and details.get('description'))
                if description and len(description) > 100:
                    result['score'] = criterion['weight']
                    result['status'] = 'positive'
                    result['message'] = 'Descrição completa'
                elif description:
                    result['score'] = criterion['weight'] // 2
                    result['status'] = 'moderate'
                    result['message'] = 'Descrição incompleta'
                else:
                    result['message'] = 'Sem descrição'
            
            elif criterion['id'] == 9:  # Presença nas redes sociais
                social_links = 0
                if details:
                    for key in ['facebook', 'instagram', 'twitter', 'linkedin']:
                        if details.get(key):
                            social_links += 1
                
                if social_links >= 3:
                    result['score'] = criterion['weight']
                    result['status'] = 'positive'
                    result['message'] = f'{social_links} redes sociais'
                elif social_links > 0:
                    result['score'] = criterion['weight'] // 2
                    result['status'] = 'moderate'
                    result['message'] = f'Apenas {social_links} redes sociais'
                else:
                    result['message'] = 'Sem redes sociais'
            
            elif criterion['id'] == 10:  # Presença no Google Maps
                if business.get('gps_coordinates'):
                    result['score'] = criterion['weight']
                    result['status'] = 'positive'
                    result['message'] = 'Localização no Maps'
                else:
                    result['message'] = 'Sem localização no Maps'
            
            elif criterion['id'] == 11:  # Fotos do exterior
                exterior_photos = [p for p in business.get('photos', []) if 'exterior' in p.get('category', '').lower()]
                if len(exterior_photos) > 0:
                    result['score'] = criterion['weight']
                    result['status'] = 'positive'
                    result['message'] = 'Possui fotos do exterior'
                else:
                    result['message'] = 'Sem fotos do exterior'
            
            elif criterion['id'] == 12:  # Fotos do interior
                interior_photos = [p for p in business.get('photos', []) if 'interior' in p.get('category', '').lower()]
                if len(interior_photos) > 0:
                    result['score'] = criterion['weight']
                    result['status'] = 'positive'
                    result['message'] = 'Possui fotos do interior'
                else:
                    result['message'] = 'Sem fotos do interior'
            
            elif criterion['id'] == 13:  # Informações de produtos e serviços
                if business.get('service_options') or (details and details.get('products')):
                    result['score'] = criterion['weight']
                    result['status'] = 'positive'
                    result['message'] = 'Produtos/serviços cadastrados'
                else:
                    result['message'] = 'Sem informações de produtos/serviços'
            
            elif criterion['id'] == 14:  # Possui avaliações
                reviews_count = business.get('reviews', 0)
                if reviews_count >= 20:
                    result['score'] = criterion['weight']
                    result['status'] = 'positive'
                    result['message'] = f'{reviews_count} avaliações'
                elif reviews_count > 0:
                    result['score'] = criterion['weight'] // 2
                    result['status'] = 'moderate'
                    result['message'] = f'Apenas {reviews_count} avaliações'
                else:
                    result['message'] = 'Sem avaliações'
            
            elif criterion['id'] == 15:  # Endereço configurado
                if business.get('address'):
                    result['score'] = criterion['weight']
                    result['status'] = 'positive'
                    result['message'] = 'Endereço configurado'
                else:
                    result['message'] = 'Sem endereço'
            
            elif criterion['id'] == 16:  # Possui logotipo
                if business.get('thumbnail') or (details and details.get('logo')):
                    result['score'] = criterion['weight']
                    result['status'] = 'positive'
                    result['message'] = 'Possui logotipo'
                else:
                    result['message'] = 'Sem logotipo'
            
            elif criterion['id'] == 17:  # Resposta a avaliações
                if details and details.get('owner_responses'):
                    result['score'] = criterion['weight']
                    result['status'] = 'positive'
                    result['message'] = 'Responde avaliações'
                else:
                    result['message'] = 'Não responde avaliações'
            
            results.append(result)
        
        return results
    
    def _generate_summary(self, criteria_results):
        """
        Gera um resumo da análise
        
        Args:
            criteria_results: Lista de resultados dos critérios
            
        Returns:
            dict: Resumo com principais problemas e pontos positivos
        """
        critical_issues = [c for c in criteria_results if c['status'] == 'critical']
        moderate_issues = [c for c in criteria_results if c['status'] == 'moderate']
        positive_points = [c for c in criteria_results if c['status'] == 'positive']
        
        return {
            'critical_issues_count': len(critical_issues),
            'moderate_issues_count': len(moderate_issues),
            'positive_points_count': len(positive_points),
            'top_critical_issues': [
                {'name': c['name_es'], 'message': c['message']} 
                for c in critical_issues[:5]
            ],
            'recommendations': self._generate_recommendations(critical_issues, moderate_issues)
        }
    
    def _generate_recommendations(self, critical_issues, moderate_issues):
        """
        Gera recomendações baseadas nos problemas encontrados
        
        Args:
            critical_issues: Lista de problemas críticos
            moderate_issues: Lista de problemas moderados
            
        Returns:
            list: Lista de recomendações
        """
        recommendations = []
        
        if len(critical_issues) > 5:
            recommendations.append("Perfil GMB necessita de otimização urgente")
        
        for issue in critical_issues[:3]:
            recommendations.append(f"Prioridade: {issue['message']}")
        
        return recommendations
