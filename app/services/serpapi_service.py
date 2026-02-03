"""
PURETEGO CRM - SerpApi Service
Serviço de integração com SerpApi para análise do Google Meu Negócio
"""

import requests
import logging
from flask import current_app
from config.settings import config as default_config

# Configuração de log básica
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SerpApiService:
    """Serviço para buscar informações do Google Meu Negócio via SerpApi"""
    
    def __init__(self, api_key=None):
        # Tenta pegar da config do Flask (current_app) se estiver em um context
        try:
            self.api_key = api_key or current_app.config.get('SERPAPI_KEY') or default_config.SERPAPI_KEY
        except RuntimeError:
            # Fora do context do Flask
            self.api_key = api_key or default_config.SERPAPI_KEY
            
        self.base_url = "https://serpapi.com/search"
    
    def _execute_request(self, params):
        """Executa a requisição com tratamento de erros robusto"""
        try:
            # Tentar primeira vez normalmente
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.SSLError as e:
            logger.warning(f"SSL Error detected: {e}. Attempting fallback without verification...")
            # Fallback para servidores com CA bundles desatualizados (comum em cPanel compartilhado)
            try:
                # Disable warning for this specific fallback to not clutter logs
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                
                response = requests.get(self.base_url, params=params, timeout=30, verify=False)
                response.raise_for_status()
                return response.json()
            except Exception as e2:
                logger.error(f"Fallback SSL request failed: {e2}")
                return {'error': f"SSL Connection Error: {str(e2)}"}
        except requests.exceptions.RequestException as e:
            logger.error(f"Request Error: {e}")
            return {'error': str(e)}

    def search_business(self, business_name, location=None):
        """
        Busca informações de um negócio no Google Maps
        
        Args:
            business_name: Nome do negócio para buscar
            location: Localização para a busca (opcional)
            
        Returns:
            dict: Dados do negócio encontrado ou dicionário com erro
        """
        params = {
            "engine": "google_maps",
            "q": business_name,
            "type": "search",
            "api_key": self.api_key
        }
        
        # Se tiver localização, adicionar à busca para contextualizar
        if location:
            params["q"] += f", {location}"
        else:
            # Se não tiver, focar em Assunção/Paraguay como fallback
            params["ll"] = "@-25.2637,57.5759,14z"
        
        logger.info(f"Buscando negócio: {params['q']}")
        
        data = self._execute_request(params)
        
        if not data or 'error' in data:
            return data
            
        # Retornar o primeiro resultado local
        if "local_results" in data and len(data["local_results"]) > 0:
            logger.info(f"Encontrado (Local Results): {data['local_results'][0].get('title')}")
            return data["local_results"][0]
        
        # Verificar se é um resultado direto (Place Results)
        if "place_results" in data:
            logger.info(f"Encontrado (Place Results): {data['place_results'].get('title')}")
            return data["place_results"]
        
        # Verificar sugestão ortográfica se não encontrar nada
        spelling_fix = data.get("search_information", {}).get("spelling_fix")
        
        logger.warning("Nenhum resultado local encontrado.")
        if spelling_fix:
            logger.info(f"Sugestão encontrada: {spelling_fix}")
            return {'error': 'not_found', 'suggestion': spelling_fix}
            
        return {'error': 'not_found'}
    
    def get_business_details(self, place_id):
        """
        Obtém detalhes completos de um negócio pelo place_id
        
        Args:
            place_id: ID do lugar no Google Maps
            
        Returns:
            dict: Detalhes completos do negócio ou dicionário com erro
        """
        params = {
            "engine": "google_maps",
            "type": "place",
            "place_id": place_id,
            "api_key": self.api_key
        }
        
        logger.info(f"Buscando detalhes do place_id: {place_id}")
        return self._execute_request(params)
    
    def analyze_gmb_profile(self, business_name, location=None):
        """
        Analisa o perfil GMB de um negócio e retorna pontuação e relatório
        
        Args:
            business_name: Nome do negócio para analisar
            location: Localização do negócio (opcional)
            
        Returns:
            dict: {
                'score': int (0-100),
                'report': dict com detalhes da análise,
                'raw_data': dados brutos da API
            }
        """
        # Buscar o negócio
        business = self.search_business(business_name, location)
        
        if not business or 'error' in business:
            api_error = business.get('error') if isinstance(business, dict) else None
            suggestion = business.get('suggestion') if isinstance(business, dict) else None
            
            if api_error == 'not_found':
                error_msg = 'Negócio não encontrado'
            elif api_error:
                error_msg = f'Erro: {api_error}'
            else:
                error_msg = 'Erro inesperado ao buscar negócio'
                
            if suggestion:
                error_msg += f'. Você quis dizer: "{suggestion}"?'
            
            return {
                'score': 0,
                'report': {'error': error_msg},
                'raw_data': None
            }
        
        # OTIMIZAÇÃO DE CRÉDITOS:
        # Se o resultado da busca já for rico (ex: Place Results ou Local Result completo), 
        # usamos ele mesmo como detalhes para economizar 1 chamada de API.
        details = None
        
        # Heurística: Se tem horário E endereço, provavelmente é um resultado rico o suficiente
        is_rich_result = 'hours' in business and 'address' in business
        
        if is_rich_result:
            print("Otimização: Usando resultado da busca como detalhes (economizando 1 crédito)")
            details = business
        elif 'place_id' in business:
            # Apenas faz a segunda chamada se o resultado for pobre (apenas resumo)
            print("Resultado básico: Buscando detalhes adicionais (gasta +1 crédito)")
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
        try:
            criteria = current_app.config.get('HEALTH_CHECK_CRITERIA') or default_config.HEALTH_CHECK_CRITERIA
        except RuntimeError:
            criteria = default_config.HEALTH_CHECK_CRITERIA
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
