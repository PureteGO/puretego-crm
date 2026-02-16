"""
PURETEGO CRM - Health Check Service
Serviço para realizar auditorias de perfil (Public & Official)
"""

from flask import current_app
from app.models import HealthCheck, Client
from app.services.serper_service import SerperService
from config.database import get_db
import logging

logger = logging.getLogger(__name__)

class HealthCheckService:
    
    @staticmethod
    def perform_public_audit(client_id, query, location=None):
        """
        Realiza uma auditoria baseada em dados públicos (Serper.dev + SerpApi Deep Dive).
        Mapeia os dados para os 17 Critérios oficiais (Config.HEALTH_CHECK_CRITERIA).
        
        Agora utiliza verificação profunda (Reviews, Photos, Posts) para determinar status de verificação
        e métricas reais de engajamento (Reply Rate, Freshness).
        """
        from config.settings import Config
        from app.services.serpapi_service import SerpApiService
        
        # 1. Configurar contexto (País/GL)
        gl = 'py' # Default Paraguay
        if client_id:
            with get_db() as db:
                client = db.query(Client).get(client_id)
                if client and client.address:
                    if 'brasil' in client.address.lower() or 'brazil' in client.address.lower(): gl = 'br'
                    elif 'marketing' in client.address.lower(): gl = 'us' # Exemplo
        
        # 2. Buscar no Serper (Discovery)
        serper = SerperService()
        search_res = serper.search_places(query, limit=1, country=gl)
        
        # Retry logic (clean name, add city)
        if not search_res['success'] or not search_res.get('places'):
            clean_name = query.split("-")[0].split("(")[0].strip()
            # Try with clean name + location hint if available
            location_hint = ""
            if client_id:
                with get_db() as db:
                     client = db.query(Client).get(client_id)
                     if client and (client.city or client.address):
                         location_hint = client.city or client.address.split(',')[0]
            
            if location_hint:
                search_res = serper.search_places(f"{clean_name} {location_hint}", limit=1, country=gl)
            
            if not search_res['success'] or not search_res.get('places'):
                 search_res = serper.search_places(clean_name, limit=1, country=gl)

        if not search_res['success'] or not search_res.get('places'):
            return {'success': False, 'error': 'Empresa não encontrada nos mapas. Tente um nome mais simples.'}
            
        place_data = search_res['places'][0]
        place_id = place_data.get('placeId') or place_data.get('cid')
        
        # --- NOVO: Verificação de Perfil Gerenciado (API Oficial) ---
        # Se o perfil já é nosso cliente e está conectado, usamos a API Oficial com integridade 100%
        official_service = None
        current_location_link = None
        
        # 3. Fetch Details & Media (High-Integrity Public Search)
        from app.services.serpapi_service import SerpApiService
        serpapi = SerpApiService()
        
        # Data containers
        reviews_data = {}
        photos_data = {}
        posts_data = {}
        data_id = place_id
        deep_fetch_error = False
        
        # Use SerpApi for a deeper look at place details (Discovery of data_id)
        details_res = {}
        if place_id:
            details_res = serpapi.get_business_details(place_id)
            if 'search_parameters' in details_res:
                data_id = details_res['search_parameters'].get('data_id')

        # Fallback if no data_id found via place_id
        if not data_id:
            search_term = place_data.get('title')
            if place_data.get('address'): search_term += f" {place_data.get('address')}"
            fallback_res = serpapi.search_business(search_term)
            
            match = fallback_res.get('local_results', [None])[0] or fallback_res.get('place_results')
            if match:
                place_data.update(match)
                data_id = match.get('data_id')
                # Map photo structure
                if 'images' in match: 
                    place_data['photos'] = match['images']
                    if any(i.get('title') == 'Videos' for i in match['images']): 
                        place_data['has_video_indicator'] = True

        # Parallel Deep Scraping (Photos, Reviews, Posts)
        if data_id:
            import concurrent.futures
            try:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    f_revs = executor.submit(serpapi.get_place_reviews, data_id, gl=gl)
                    f_imgs = executor.submit(serpapi.get_place_photos, data_id, gl=gl)
                    f_posts = executor.submit(serpapi.get_place_posts, data_id, gl=gl)
                    
                    reviews_data = f_revs.result(timeout=6)
                    photos_data = f_imgs.result(timeout=6)
                    posts_data = f_posts.result(timeout=6)
            except Exception as e:
                current_app.logger.error(f"HealthCheck: Scraping error for {data_id}: {e}")
                deep_fetch_error = True
        
        # 4. Analysis & Logic (Intelligent Public Auditor)
        
        # A. Reviews Analysis
        reviews_list = reviews_data.get('reviews', [])
        total_reviews_fetched = len(reviews_list)
        reviews_with_response = [r for r in reviews_list if r.get('response')]
        replied_count = len(reviews_with_response)
        unreplied_count = total_reviews_fetched - replied_count
        
        has_owner_response = replied_count > 0 # Strong verification signal
        
        # B. Photos Analysis
        photos_list = photos_data.get('photos', [])
        # Also check local_results photos (mapped from 'images') if deep fetch failed
        if not photos_list and place_data.get('photos'):
            current_app.logger.info(f"HealthCheck: Using mapped 'images' -> 'photos' for {place_data.get('title')}")
            photos_list = place_data.get('photos')

        # Check for Owner Photos
        # Standard Place Photos format: source = 'owner'
        # Search API 'images' format: title = 'By owner'
        has_owner_photos = any(
            (p.get('source', '').lower() == 'owner') or 
            ('owner' in str(p).lower()) or
            (p.get('title') == 'By owner') 
            for p in photos_list
        )
        
        # Check categories directly if available (Standard Place Photos)
        photo_cats = photos_data.get('categories', [])
        has_owner_photos = has_owner_photos or any('owner' in c.get('title', '').lower() for c in photo_cats)
        
        # Check for Videos
        # Standard: video in categories OR video field in photo
        # Search API: title = 'Videos' in images list
        has_video = (
            any('video' in c.get('title', '').lower() for c in photo_cats) or 
            any(p.get('video') for p in photos_list) or
            place_data.get('has_video_indicator') or
            any(p.get('title') == 'Videos' for p in photos_list)
        )
        
        # Photo Freshness check
        last_photo_date = None
        # TODO: Implement get_photo_meta for top photo if needed, strictly speaking we can infer from 'date' field in photos_list if present
        
        # C. Posts Analysis
        posts_list = posts_data.get('posts', []) or posts_data.get('updates', [])
        has_posts = len(posts_list) > 0
        last_post_date = posts_list[0].get('time') if has_posts else None # Check formatting later
        
        # --- Verification Logic ---
        # Se tem resposta do dono, fotos do dono ou posts, consideramos VERIFICADO/Gerenciado
        is_managed = has_owner_response or has_owner_photos or has_posts or place_data.get('verified') or place_data.get('claimed')
        
        # --- Scoring ---
        criteria = Config.HEALTH_CHECK_CRITERIA
        score = 0
        criteria_results = []
        details = []
        positive_points = 0
        moderate_issues = 0
        critical_issues = 0
        
        if deep_fetch_error:
            details.append("Aviso: Falha temporária na API de busca profunda. Algumas métricas (Reviews, Fotos) podem estar incompletas.")
            # moderate_issues += 1 # Optional
            
        for c in criteria:
            cid = c['id']
            passed = False
            status = 'critical'
            res_score = 0
            
            if cid == 1: # Horário
                passed = bool(place_data.get('hours') or place_data.get('openingHours') or place_data.get('operating_hours'))
            elif cid == 2: # Fotos Produtos
                # Buscar especificamente por fotos enviadas pelo proprietário (Imagem 1)
                passed = has_owner_photos or len(photos_list) > 10
            elif cid == 3: # Vídeos
                passed = has_video
            elif cid == 4: # Perfil Verificado
                # Prova definitiva: Se tem 'Updates' ou Respostas (Imagens 3 e 4)
                passed = has_posts or has_owner_response or is_managed
                if passed: 
                     details.append("Perfil Gerenciado (Updates/Posts ativos detectados)")
                else:
                     details.append("Sem indícios de gestão ativa (Faltam Posts/Updates)")
            elif cid == 5: # Site
                website = place_data.get('website', '').lower()
                passed = bool(website)
                if passed:
                    social_domains = ['facebook.com', 'instagram.com', 'tiktok.com', 'linktr.ee', 'linkedin.com', 'twitter.com', 'x.com']
                    if any(domain in website for domain in social_domains):
                        passed = False
                        details.append(f"Site detectado é rede social ({website})")
            elif cid == 6: # Q&A
                passed = bool(place_data.get('questions_and_answers'))
            elif cid == 7: # Posts
                # Seção 'Updates from User' (Imagem 3)
                passed = has_posts
            elif cid == 8: # Descrição
                # Seção 'From the business' (Imagem 3)
                desc = place_data.get('description') or place_data.get('about', {}).get('summary')
                passed = bool(desc and len(str(desc)) > 20)
            elif cid == 9: # Redes Sociais
                passed = bool(place_data.get('profiles')) or has_posts
            elif cid == 10: # Presença Maps
                passed = True
            elif cid == 11: # Fotos Exterior
                # Buscar a aba literal 'Street View' ou 'Exterior' no objeto da SerpApi (Imagem 1)
                passed = any(x in str(c.get('title', '')).lower() for c in photo_cats for x in ['exterior', 'street view', 'outside', 'fachada'])
                if not passed:
                    # Fallback: se o dono postou fotos e o total é alto, é provável que incluiu a fachada
                    passed = has_owner_photos and len(photos_list) > 15
            elif cid == 12: # Fotos Interior
                # Buscar a aba literal 'Interior' ou 'Inside' (Imagem 1)
                passed = any(x in str(c.get('title', '')).lower() for c in photo_cats for x in ['interior', 'inside', 'dentro'])
                if not passed:
                    passed = has_owner_photos and len(photos_list) > 15
            elif cid == 13: # Info Produtos
                # Verificado via seção de Updates ou campos ricos
                passed = bool(place_data.get('menu')) or bool(place_data.get('products')) or has_posts or place_data.get('extensions')
            elif cid == 14: # Avaliações
                rev_count = place_data.get('reviews') or 0
                if rev_count >= 10: 
                    passed = True; res_score = c['weight']
                elif rev_count > 0:
                    passed = True; res_score = c['weight'] // 2; status = 'moderate'
                else: passed = False
            elif cid == 15: # Endereço
                passed = bool(place_data.get('address'))
            elif cid == 16: # Logotipo
                passed = bool(place_data.get('thumbnail')) or bool(place_data.get('logo'))
            elif cid == 17: # Resposta a Avaliações
                passed = has_owner_response
                if passed and unreplied_count > 5:
                    status = 'moderate'
                    res_score = c['weight'] // 2

            if passed:
                if res_score == 0: res_score = c['weight']
                score += res_score
                positive_points += 1
            else:
                if c['type'] == 'critical': critical_issues += 1
                elif c['type'] == 'moderate': moderate_issues += 1
            
            criteria_results.append({
                'id': cid,
                'name_pt': c['name_pt'], 
                'name_es': c['name_es'],
                'passed': passed,
                'weight': c['weight'],
                'type': c.get('type','moderate')
            })
            
        # --- Score Adjustment Logic (Critical Issues) ---
        # 1. Count missing criticals
        # Note: critical_issues variable already counts missing criticals inside the loop
        critical_missing_count = critical_issues
        
        # 2. Determine multiplier (Less aggressive penalty)
        multiplier = 1.0
        if critical_missing_count == 1:
            multiplier = 0.95
        elif critical_missing_count == 2:
            multiplier = 0.85
        elif critical_missing_count >= 3:
            multiplier = 0.7
            
        # 3. Apply multiplier
        score = round(score * multiplier)
        
        # Add explanation if penalized
        if multiplier < 1.0:
            details.append(f"Nota ajustada devido à ausência de {critical_missing_count} fatores críticos fundamentais.")

        # Apply penalty for unverified profile (Cumulative)
        if not is_managed:
            score = round(score * 0.8)

        # Relatório final
        score = min(100, max(0, score))
        
        recommendations = []
        if not is_managed:
            recommendations.append("URGENTE: Reivindique e verifique seu perfil para proteger sua marca.")
        
        if unreplied_count > 0:
            recommendations.append(f"Responda a {unreplied_count} avaliações pendentes para melhorar o ranking.")
            
        if not has_posts:
            recommendations.append("Publique atualizações semanais (Posts) para manter o perfil ativo.")
            
        if not has_video:
            recommendations.append("Adicione vídeos do local/produtos. O Google valoriza muito conteúdo em vídeo.")
            
        for res in criteria_results:
            if not res['passed'] and res['type'] == 'critical':
                 recommendations.append(f"Corrija: {res['name_es']} ausente.")
        
        # Top critical
        top_critical_issues = [{'name': r['name_es'], 'message': 'Ausente'} for r in criteria_results if not r['passed'] and r['type']=='critical']

        report_data = {
            'business_name': place_data.get('title'),
            'source_data': place_data,
            'details': details,
            'criteria_results': criteria_results,
            'top_critical_issues': top_critical_issues,
            'recommendations': recommendations[:5],
            'summary': { 
                'critical_issues_count': critical_issues,
                'moderate_issues_count': moderate_issues,
                'positive_points_count': positive_points,
                'text': f"Score Público: {score}/100"
            },
            'criteria': [
                {
                    'name': res['name_es'],
                    'status': 'Detectado' if res['passed'] else 'Não detectado',
                    'score': 100 if res['passed'] else 0
                } for res in criteria_results
            ]
        }
        
        # --- Radar Metrics Integration (Real Data) ---
        try:
            from app.services.rank_tracker_service import RankTrackerService
            from app.models.local_search import LocalMetricsAggregated
            from datetime import datetime
            from sqlalchemy import func
            
            # 1. Try to get existing metrics for today
            today = datetime.now().date()
            radar_metrics = None
            
            if client_id:
                with get_db() as db:
                    # Use func.date for safe comparison
                    agg = db.query(LocalMetricsAggregated).filter(
                        LocalMetricsAggregated.client_id == client_id,
                        func.date(LocalMetricsAggregated.scan_date) == today
                    ).first()
                    
                    if agg:
                        radar_metrics = {
                            'visibility': agg.visibility_score,
                            'position': agg.avg_position_score,
                            'reviews': agg.reviews_score,
                            'authority': agg.local_authority_score,
                            'market_avg': {
                                'visibility': agg.market_avg_visibility,
                                'position': agg.market_avg_position,
                                'reviews': agg.market_avg_reviews,
                                'authority': agg.market_avg_authority
                            }
                        }
            
            # 2. If no metrics, trigger a scan (Sync for now, could be Async)
            if not radar_metrics and client_id:
                current_app.logger.info(f"No existing metrics for client {client_id} today. Triggering scan.")
                scan_result = RankTrackerService.perform_scan(client_id)
                if scan_result.get('success') and scan_result.get('metrics'):
                     agg = scan_result['metrics']
                     radar_metrics = {
                        'visibility': agg.visibility_score,
                        'position': agg.avg_position_score,
                        'reviews': agg.reviews_score,
                        'authority': agg.local_authority_score,
                        'market_avg': {
                            'visibility': agg.market_avg_visibility,
                            'position': agg.market_avg_position,
                            'reviews': agg.market_avg_reviews,
                            'authority': agg.market_avg_authority
                        }
                     }
            
            # 3. Add to report_data
            if radar_metrics:
                report_data['radar_metrics'] = radar_metrics
                # Update score description if authority is low?
                report_data['summary']['text'] += f" | Autoridade Local: {int(radar_metrics['authority'])}"
                
        except Exception as e:
            current_app.logger.error(f"Failed to integrate RankTracker metrics: {str(e)}")
            import traceback
            current_app.logger.error(traceback.format_exc())

        # --- AI Quick Summary Generation ---
        try:
             from app.services.gemini_service import GeminiService
             gemini = GeminiService()
             
             if gemini.model:
                 # 1. Detect site type
                 website_url = place_data.get('website')
                 site_type = HealthCheckService._detect_site_type(website_url)
                 
                 # 2. Prepare Input Data
                 input_data = {
                     'business_name': place_data.get('title'),
                     'language': 'pt', # Default to PT for Quick Check or use gl/client preference? 
                     # Quick Check is often for prospecting, so PT or ES might depend on target region.
                     # The prompt handles languages. Let's pass 'pt' or 'es' based on `gl` context?
                     # Method has `gl` variable. 'py' -> 'es', 'br' -> 'pt'.
                     'language': 'pt' if gl == 'br' else 'es',
                     'criteria_results': criteria_results,
                     'summary': {
                         'score_publico': score,
                         'critical_issues_count': critical_issues,
                         'moderate_issues_count': moderate_issues,
                         'positive_points_count': positive_points
                     },
                     'details': details,
                     'recommendations': recommendations,
                     'site_type': site_type,
                     'site_url': website_url
                 }
                 
                 # Call AI
                 ai_summary = gemini.generate_quick_check_summary(input_data)
                 report_data['ai_summary'] = ai_summary
                 
        except Exception as e: 
             current_app.logger.error(f"AI Generation failed for Public Audit: {e}")
             # Non-blocking

        check_id = None
        if client_id:
            with get_db() as db:
                health_check = HealthCheck(
                    client_id=client_id,
                    score=score,
                    report_data=report_data
                )
                health_check.source = 'public'
                health_check.origin_id = place_data.get('placeId') or place_data.get('cid')
                
                db.add(health_check)
                db.commit()
                check_id = health_check.id
            
        return {
            'success': True, 
            'check_id': check_id, 
            'score': score,
            'report': report_data 
        }

    @staticmethod
    def perform_official_audit(client_id, location_link_id=None):
        """
        Realiza auditoria usando dados OFICIAIS da API do Google Business Profile.
        Requer que o cliente tenha um perfil vinculado.
        """
        from app.services.google_business_service import get_service_for_client
        from app.models import GMBLocationLink
        
        # 1. Obter Serviço e Link
        service = get_service_for_client(client_id, location_link_id)
        if not service:
             return {'success': False, 'error': 'Cliente não possui perfil do Google vinculado ou o perfil especificado não foi encontrado.'}
        
        with get_db() as db:
             if location_link_id:
                 link = db.query(GMBLocationLink).filter(
                    GMBLocationLink.id == location_link_id,
                    GMBLocationLink.client_id == client_id
                 ).first()
             else:
                 link = db.query(GMBLocationLink).filter(
                    GMBLocationLink.client_id == client_id,
                    GMBLocationLink.is_primary == True
                 ).first()
                 if not link:
                     link = db.query(GMBLocationLink).filter(
                        GMBLocationLink.client_id == client_id
                     ).first()
                     
             if not link:
                 return {'success': False, 'error': 'Vínculo de perfil não encontrado.'}
             location_name = link.gmb_location_name
             
        # 2. Buscar Dados Reais (API)
        try:
            loc_details = service.get_location_details(location_name)
            summary_v4 = service.get_location_summary_v4(location_name)
            reviews = service.list_reviews(location_name, page_size=50)
            media_items = service.list_media(location_name)
            vcom_state = service.get_voice_of_merchant_state(location_name)
            verifications = service.list_verifications(location_name)
            
            # Integrar dados globais do sumário v4
            loc_details['averageRating'] = summary_v4.get('averageRating', 0)
            loc_details['totalReviewCount'] = summary_v4.get('totalReviewCount', 0)
            
        except Exception as e:
             return {'success': False, 'error': f'Erro de API Google: {str(e)}'}

        # 3. Calcular Score (Rigoroso)
        score = 0
        details = []
        positive_points = 0
        moderate_issues = 0
        critical_issues = 0
        
        # --- A. Verificação Básica (Max 35) ---
        if loc_details.get('title'):
            score += 5
            positive_points += 1
            
        # Status de Verificação (Voice of Merchant)
        is_verified = vcom_state.get('hasVoiceOfMerchant', False)
        vcom_error = vcom_state.get('error')
        gain_vcom = vcom_state.get('gainVoiceOfMerchant', {})
        
        if vcom_error:
            # API Error - Do not penalize heavily, just warn
            details.append(f"Erro na verificação de status (API): {vcom_error}")
            moderate_issues += 1
            # Assume verified for scoring to give benefit of doubt if it's an API config issue
            # Or at least don't apply the 0.8 multiple later
            verification_status_unknown = True
        else:
            verification_status_unknown = False

        if is_verified:
            score += 15 # Aumentado para 15
            positive_points += 1
            details.append("Perfil Verificado e Gerenciado (Confirmado via Google)")
        elif not verification_status_unknown:
            # Only go into details if we are sure it's NOT verified
            # Analisar motivo da não-verificação
            msg = "Perfil não verificado ou requer ação manual no Google Business Profile."
            if 'resolveOwnershipConflict' in gain_vcom:
                msg = "Conflito de Propriedade: Outra pessoa já verificou este local no Google."
            elif 'complyWithGuidelines' in gain_vcom:
                 msg = "Perfil Suspenso ou Fora das Diretrizes: Requer regularização imediata com o suporte do Google."
            elif 'verify' in gain_vcom:
                 # Verificar se já existe algo em andamento
                 has_pending = any(v.get('state') != 'COMPLETED' for v in verifications)
                 if has_pending:
                     msg = "Verificação em Andamento: O processo foi iniciado mas ainda não foi concluído no Google."
                 else:
                     msg = "Perfil não Verificado: Requer iniciar o processo de verificação oficial."
            
            details.append(msg)
            critical_issues += 1
        
        # Categoria (Metadata ou Profile)
        # A API v1 retorna categories dentro de 'profile' ou 'storefrontAddress'?? 
        # Na verdade categories é uma chamada separada ou parte de 'categories' se usar readMask correto.
        # O get_location_details usa readMask='name,title,storefrontAddress,phoneNumbers,websiteUri,regularHours,profile,metadata'
        # 'profile' costuma conter categoria? Vamos checar. Se não, assumimos ok por ser verificado.
        # Vamos focar no que temos certeza: Telefone, Site, Horário.
        
        if loc_details.get('phoneNumbers'):
            score += 5
            positive_points += 1
        else:
            details.append("Sem telefone cadastrado.")
            critical_issues += 1
            
        if loc_details.get('websiteUri'):
            score += 5
            positive_points += 1
        else:
            details.append("Sem website vinculado.")
            moderate_issues += 1
            
        if loc_details.get('regularHours'):
             score += 5
             positive_points += 1
        else:
             # Check if it's 24 hours or just missing?
             # API returns regularHours as {periods: []} or None?
             details.append("Sem horário de funcionamento.")
             moderate_issues += 1

        # --- B. Imagem e Conteúdo (Max 30) ---
        # Fotos (Verificadas via API Media)
        photo_count = len(media_items)
        
        # Check for potential API failure in Media
        if photo_count == 0:
            details.append("Não foi possível detectar fotos (Pode ser erro de Permissão da API ou Perfil vazio).")
        
        has_logo = any(m.get('locationAssociation') == 'LOGO' for m in media_items)
        has_interior = any(m.get('locationAssociation') == 'INTERIOR' for m in media_items)
        
        if photo_count > 10:
            score += 15
            positive_points += 1
            details.append(f"Bom volume de fotos ({photo_count}).")
        elif photo_count > 0:
            score += 5
            moderate_issues += 1
            details.append(f"Poucas fotos ({photo_count}). Ideal > 10.")
        else:
            critical_issues += 1
            # details.append("Sem fotos publicadas.") # Already added above

        if has_logo:
            score += 5
            positive_points += 1
        else:
            details.append("Logo não identificado.")
            moderate_issues += 1
            
        if has_interior:
            score += 10
            positive_points += 1
            details.append("Fotos do interior identificadas.")
        else:
            details.append("Sem fotos do interior/loja.") # Não penaliza tanto, mas não pontua.

        # reviews usando dados globais (v4 summary)
        avg_rating = loc_details.get('averageRating', 0)
        review_count = loc_details.get('totalReviewCount', 0)
        
        # Fallback: Se API v4 falhar ou retornar zero, tentar usar os reviews em cache
        if (avg_rating or 0) == 0:
            with get_db() as db:
                from app.models import GMBReview
                # Nota: link.id deve estar disponível do passo 1
                cached_reviews = db.query(GMBReview).filter(GMBReview.location_link_id == link.id).all()
                if cached_reviews:
                    review_count = len(cached_reviews)
                    avg_rating = sum([r.star_rating for r in cached_reviews]) / review_count
        
        # Taxa de Resposta (estimada pelas últimas 50)
        recent_reviews_count = len(reviews)
        replied_count = sum([1 for r in reviews if r.get('hasReply')])
        reply_rate = (replied_count / recent_reviews_count) * 100 if recent_reviews_count > 0 else 0
        
        if (review_count or 0) > 0:
            if (avg_rating or 0) >= 4.5:
                score += 15
                positive_points += 1
                details.append(f"Excelente avaliação média ({(avg_rating or 0):.1f} estrelas).")
            elif (avg_rating or 0) >= 4.0:
                 score += 10
                 details.append(f"Boa avaliação média ({(avg_rating or 0):.1f} estrelas).")
                 moderate_issues += 1
            else:
                 details.append(f"Avaliação média baixa ({(avg_rating or 0):.1f} estrelas).")
                 critical_issues += 1
                 
            # Reply Rate importa muito para gestão
            if reply_rate >= 90:
                score += 15
                positive_points += 1
                details.append("Excelente taxa de resposta recente.")
            elif reply_rate >= 50:
                score += 5
                moderate_issues += 1
                details.append(f"Taxa de resposta recente moderada ({reply_rate:.0f}%).")
            else:
                critical_issues += 1
                details.append(f"Baixa taxa de resposta recente ({reply_rate:.0f}%).")
                
            # Penalidade extra se review count for alto mas reply rate for 0
            if (review_count or 0) > 20 and (reply_rate or 0) < 10:
                 score -= 10
                 details.append("Alerta: Alto volume de avaliações sem resposta!")
                 critical_issues += 1
        else:
            details.append("Sem avaliações no perfil.")
            critical_issues += 1

        # --- Montar Relatório ---
        top_critical_issues = []
        recommendations = []
        
        for detail in details:
            if any(x in detail.lower() for x in ["pendente", "conflito", "suspenso", "não verificado", "sem", "baixa", "alerta"]):
                top_critical_issues.append({'name': 'Atenção Corretiva', 'message': detail})
                recommendations.append(f"Ação Corretiva: {detail}")
            else:
                 recommendations.append(f"Ponto Positivo: {detail}")

        # Apply penalty for unverified profile (Official)
        # We need to re-verify the variable 'is_verified' scope or use 'critical_issues' analysis?
        # 'is_verified' var corresponds to Voice of Merchant check from line 543.
        # Apply penalty for unverified profile (Official)
        if not is_verified and not verification_status_unknown:
            score = score * 0.8
            # Explicitly add critical issue if not already added?
            # It was added in the block above

        # Relatório final formatado
        score = min(100, max(0, score))
        
        # Prepare report data
        # Ensure ID is available at root for header
        if loc_details and loc_details.get('metadata'):
            loc_details['place_id'] = loc_details['metadata'].get('placeId')
            loc_details['placeId'] = loc_details['metadata'].get('placeId')

        report_data = {
            'business_name': loc_details.get('title'),
            'source_data': loc_details,
            'details': details,
            'top_critical_issues': top_critical_issues,
            'recommendations': recommendations,
            'summary': { 
                'critical_issues_count': critical_issues,
                'moderate_issues_count': moderate_issues,
                'positive_points_count': positive_points,
                'text': f"Auditoria Oficial: {score}/100"
            },
            'criteria': [
                {
                    'name': d.split(':')[0],
                    'status': d.split(':')[1].strip() if ':' in d else d,
                    'score': 100 if 'ok' in d.lower() or 'excelente' in d.lower() or 'bom' in d.lower() else 50
                } for d in details
            ]
        }
        
        # --- Radar Metrics Integration (Real Data) ---
        try:
            from app.services.rank_tracker_service import RankTrackerService
            from app.models.local_search import LocalMetricsAggregated
            from datetime import datetime
            
            # 1. Try to get existing metrics for today
            today = datetime.now().date()
            radar_metrics = None
            
            if client_id:
                with get_db() as db:
                    agg = db.query(LocalMetricsAggregated).filter_by(
                        client_id=client_id, 
                        scan_date=today
                    ).first()
                    
                    if agg:
                        radar_metrics = {
                            'visibility': agg.visibility_score,
                            'position': agg.avg_position_score,
                            'reviews': agg.reviews_score,
                            'authority': agg.local_authority_score,
                            'market_avg': {
                                'visibility': agg.market_avg_visibility,
                                'position': agg.market_avg_position,
                                'reviews': agg.market_avg_reviews,
                                'authority': agg.market_avg_authority
                            }
                        }
            
            # 2. If no metrics, trigger a scan (Sync for now, could be Async)
            if not radar_metrics and client_id:
                scan_result = RankTrackerService.perform_scan(client_id)
                if scan_result.get('success') and scan_result.get('metrics'):
                     agg = scan_result['metrics']
                     radar_metrics = {
                        'visibility': agg.visibility_score,
                        'position': agg.avg_position_score,
                        'reviews': agg.reviews_score,
                        'authority': agg.local_authority_score,
                        'market_avg': {
                            'visibility': agg.market_avg_visibility,
                            'position': agg.market_avg_position,
                            'reviews': agg.market_avg_reviews,
                            'authority': agg.market_avg_authority
                        }
                     }
            
            # 3. Add to report_data
            if radar_metrics:
                report_data['radar_metrics'] = radar_metrics
                # Update score description if authority is low?
                report_data['summary']['text'] += f" | Autoridade Local: {int(radar_metrics['authority'])}"
                
        except Exception as e:
            current_app.logger.error(f"Failed to integrate RankTracker metrics in Official Audit: {str(e)}")
            # Fallback to mock/calculated structure if needed or just leave empty
            pass
        
        # --- AI Internal Analysis Generation ---
        try:
             from app.services.gemini_service import GeminiService
             gemini = GeminiService()
             
             if gemini.model:
                 # 1. Detect site type
                 website_url = loc_details.get('websiteUri')
                 site_type = HealthCheckService._detect_site_type(website_url)
                 
                 # 2. Prepare Input Data
                 input_data = {
                     'business_name': loc_details.get('title'),
                     'language': 'es', # Default to Spanish for internal/official audit or make configurable
                     'criteria_results': report_data['criteria'], # Note: report_data['criteria'] format is simplified (name, status, score). We need report_data['criteria_details']?
                     # Wait, report_data assigned 'criteria' at line 675 with simplified format.
                     # We need the rich 'criteria_results' which was NOT created in perform_official_audit (it uses 'details' list).
                     # We must construct a compatible criteria_results list from 'details' or mapped IDs.
                     # Since official audit logic is different, we'll map details to a "mock" criteria structure or pass 'details' directly.
                     # The prompt uses 'criteria_results' with 'type' and 'passed'. Official audit logic didn't build this structured list.
                     # We will pass 'details' and a constructed 'criteria_results' based on critical/moderate counts logic implicitly?
                     # Let's verify prompt: "criteria_results (array of objects): id, name_pt, passed, type, weight".
                     # perform_official_audit logic (lines 498-641) calculates `details` and counts directly.
                     # We should reconstruct a minimal criteria list for the AI to understand the structure.
                     
                     # RE-PLAN: Adapt prompt input or data.
                     # The prompt logic relies on 'criteria_results' to count critical misses.
                     # In Official Audit, we already counted 'critical_issues'. We can pass that summary directly?
                     # The prompt RE-CALCULATES critical_missing_count. So it needs the raw items.
                     # Since Official Audit code is unstructured (just `details.append`), we can't easily rebuild the exact criteria list without refactoring.
                     # HOWEVER, we can stick to passing the `details` text and letting the AI parse it?
                     # No, prompt says "INPUT (JSON)... criteria_results".
                     # Let's create a synthetic list from the `details` + hardcoded knowledge of official check criteria.
                     
                     # OR simpler: Use the `quick_check` logic (public audit) structure since prompt is shared?
                     # But `perform_official_audit` is different.
                     
                     # Let's pass the 'details' text as 'criteria_results' for now? No, type mismatch.
                     # Let's pass an empty criteria_results and rely on 'summary' counts? 
                     # Prompt Logic Step 1: "count how many such items exist".
                     # So if we pass empty, it counts 0.
                     # We need to pass the actual failures.
                     # Since we can't easily map back, let's skip AI generation for Official Audit OR refactor Official Audit to use structured criteria.
                     # Refactoring Official Audit to use structured criteria like Public Audit is better but risky/large change.
                     
                     # ALTERNATIVE: Since User asked for "Health Check na ficha do cliente" (Client Sheet Health Check),
                     # which usually refers to the internal view.
                     # The prompt "HEALTH CHECK INTERNO" expects the same structure.
                     # I will do my best to map the `details` to `criteria_results`.
                     
                     # Mapping based on text in details
                     'criteria_results': [], # Populated below
                     'summary': {
                         'score_publico': score,
                         'critical_issues_count': critical_issues,
                         'moderate_issues_count': moderate_issues,
                         'positive_points_count': positive_points
                     },
                     'details': details,
                     'recommendations': recommendations,
                     'site_type': site_type,
                     'site_url': website_url
                 }
                 
                 # Reconstruct criteria_results from details (Best Effort)
                 # We know which are critical in general logic.
                 # Critical: Verification, Website (if missing), Phone?
                 
                 # Let's iterate details and try to assign to a generic criteria list
                 # This is hacky. 
                 # Maybe we just pass the `critical_issues` count and ask AI to trust it?
                 # But Prompt Step 3 recalculates it.
                 
                 # Let's just create "Dummy" criteria entries for the detected failures.
                 for detail in details:
                     is_failure = any(x in detail.lower() for x in ["sem ", "não ", "poucas", "baixa", "pendente"])
                     severity = 'critical' if any(x in detail.lower() for x in ["verificado", "site", "telefone", "suspenso"]) else 'moderate'
                     if "logo" in detail.lower() or "interior" in detail.lower(): severity = 'moderate'
                     
                     if is_failure:
                         input_data['criteria_results'].append({
                             'id': 99,
                             'name_pt': detail,
                             'name_es': detail,
                             'passed': False,
                             'type': severity,
                             'weight': 5
                         })
                 
                 # Call AI
                 ai_summary = gemini.generate_internal_audit_summary(input_data)
                 report_data['ai_internal_analysis'] = ai_summary
                 
        except Exception as e:
             current_app.logger.error(f"AI Generation failed for Official Audit: {e}")
             # Non-blocking
        
        # Salvar auditoria
        with get_db() as db:
            health_check = HealthCheck(
                client_id=client_id,
                score=score,
                report_data=report_data
            )
            health_check.source = 'official'
            health_check.origin_id = location_name
            
            db.add(health_check)
            db.commit()
            
            check_id = health_check.id
            
        return {
            'success': True, 
            'check_id': check_id, 
            'score': score,
            'report': report_data 
        }

    @staticmethod
    def _detect_site_type(url):
        """
        Detecta o tipo de site baseado na URL.
        Returns: 'website_real', 'social_profile', 'link_hub', 'none'
        """
        if not url:
            return 'none'
        
        url_lower = url.lower()
        
        social_domains = ['facebook.com', 'instagram.com', 'twitter.com', 'linkedin.com', 'tiktok.com', 'pinterest.com', 'youtube.com']
        link_hubs = ['linktr.ee', 'bio.site', 'campsite.bio', 'beacons.ai', 'solo.to', 'hopp.co']
        
        if any(d in url_lower for d in social_domains):
            return 'social_profile'
            
        if any(d in url_lower for d in link_hubs):
            return 'link_hub'
            
        return 'website_real'
