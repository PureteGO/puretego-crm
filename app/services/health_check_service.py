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
        
        Agora inclui CACHE para evitar chamadas de API repetidas no mesmo dia para o mesmo cliente.
        """
        from config.settings import Config
        from app.services.serpapi_service import SerpApiService
        from app.services.hasdata_service import HasDataService
        from datetime import datetime
        from sqlalchemy import func
        
        # --- 0. CHECK CACHE (Same Day) ---
        if client_id:
            try:
                today = datetime.now().date()
                with get_db() as db:
                    existing = db.query(HealthCheck).filter(
                        HealthCheck.client_id == client_id,
                        HealthCheck.source == 'public',
                        func.date(HealthCheck.created_at) == today
                    ).order_by(HealthCheck.created_at.desc()).first()
                    
                    if existing and existing.report_data:
                        logger.info(f"HealthCheck: Returning CACHED report for client {client_id}")
                        return {
                            'success': True, 
                            'check_id': existing.id, 
                            'score': existing.score,
                            'report': existing.report_data,
                            'cached': True
                        }
            except Exception as e:
                logger.error(f"HealthCheck Cache check failed: {e}")
        
        # 1. Configurar contexto (País/GL)
        gl = 'py' # Default Paraguay
        if client_id:
            with get_db() as db:
                client = db.query(Client).get(client_id)
                if client and client.address:
                    if 'brasil' in client.address.lower() or 'brazil' in client.address.lower(): gl = 'br'
                    elif 'marketing' in client.address.lower(): gl = 'us' # Exemplo
        
        # 2. Discovery via Serper (Rápido e Estável para Busca Inicial)
        serper = SerperService()
        serpapi = SerpApiService()
        hasdata = HasDataService()
        
        gl = location or 'py'
        search_res = serper.search_places(query, limit=1, country=gl)
        
        # Retry logic if no results
        if not search_res['success'] or not search_res.get('places'):
            clean_name = query.split("-")[0].split("(")[0].strip()
            location_hint = ""
            if client_id:
                with get_db() as db:
                     client = db.query(Client).get(client_id)
                     if client and (client.city or client.address):
                         location_hint = client.city or client.address.split(',')[0]
            
            if location_hint:
                search_res = serper.search_places(f"{clean_name} {location_hint}", limit=1, country=gl)
            else:
                 search_res = serper.search_places(clean_name, limit=1, country=gl)

        if not search_res['success'] or not search_res.get('places'):
            return {'success': False, 'error': 'Empresa não encontrada nos mapas.'}
            
        place_data = search_res['places'][0]
        place_id = place_data.get('placeId')
        data_id = place_data.get('cid') or place_data.get('fid')
        
        # --- RECOVERY: Se place_id está faltando ou é numérico, tenta busca padrão do Serper ---
        if not place_id or str(place_id).isdigit():
            logger.info(f"HealthCheck: placeId missing or numeric ({place_id}) for {query}. Trying Serper Search (Local Pack) recovery...")
            local_pack = serper.search_local_pack(query, country=gl)
            if local_pack and 'places' in local_pack and local_pack['places']:
                for p in local_pack['places']:
                    # Match mais flexível ou posição 1
                    if query.lower() in p.get('title', '').lower() or p.get('position') == 1:
                        if p.get('placeId'):
                            logger.info(f"HealthCheck: Recovered placeId {p.get('placeId')} via Serper Local Pack")
                            place_id = p.get('placeId')
                            if p.get('cid'): data_id = p.get('cid')
                            place_data.update(p)
                            break
            
            # --- FINAL FALLBACK: SerpApi Search (Se Serper falhou totalmente no placeId) ---
            if not place_id or str(place_id).isdigit():
                logger.info(f"HealthCheck: Serper failed. Trying SerpApi fallback for {query}...")
                serp_search = serpapi.search_business(query, location=client.address if client_id else "Paraguay")
                if serp_search.get('local_results'):
                    p = serp_search['local_results'][0]
                    place_id = p.get('place_id')
                    place_data.update(p)
                    logger.info(f"HealthCheck: Recovered placeId {place_id} via SerpApi Search")
                elif serp_search.get('place_results'):
                    p = serp_search.get('place_results')
                    place_id = p.get('place_id')
                    place_data.update(p)
                    logger.info(f"HealthCheck: Recovered placeId {place_id} via SerpApi Place Results")
        
        # Limpeza final de IDs
        if place_id and str(place_id).isdigit() and not data_id:
            data_id = place_id
            place_id = None

        # 3. Fetch Deep Insights
        
        # Initial signals from Serper
        is_claimed = place_data.get('verified') or place_data.get('claimed')
        has_kp_video = place_data.get('has_video_indicator') or False
        rich_extensions = place_data.get('extensions', [])
        
        # --- NOVO: Complemento via HasData PRIMEIRO (Cost Saving) ---
        if place_id:
            hd_res = hasdata.get_place_details(place_id)
            if hd_res:
                # Merge HasData into place_data
                if 'workingHours' in hd_res and 'days' in hd_res['workingHours']:
                    place_data['hours'] = hd_res['workingHours']['days']
                if not place_data.get('description') and hd_res.get('description'):
                    place_data['description'] = hd_res.get('description')
                if not place_data.get('website') and hd_res.get('website'):
                    place_data['website'] = hd_res.get('website')
                if not place_data.get('logo') and hd_res.get('logo'):
                    place_data['logo'] = hd_res.get('logo')
                if 'images' in hd_res:
                    place_data['photos'] = hd_res['images']
                # Preservamos data_id se HasData retornar um novo, senão mantemos o do Serper
                new_data_id = hd_res.get('dataId') or hd_res.get('data_id')
                if new_data_id: data_id = new_data_id
        elif query:
            # Se não temos place_id, tentamos HasData Search para ver se recuperamos detalhe/ID
            logger.info(f"HealthCheck: No placeId found for {query}. Trying HasData Search recovery...")
            hd_search = hasdata.search_places(query, gl=gl)
            if hd_search and len(hd_search) > 0:
                hd_match = hd_search[0]
                place_id = hd_match.get('placeId')
                if not data_id: data_id = hd_match.get('dataId')
                
                # Se recuperamos place_id, pegamos os detalhes
                if place_id:
                    hd_res = hasdata.get_place_details(place_id)
                    if hd_res:
                        place_data.update(hd_res)

        # Fallback details via SerpApi if we still lack basic info (or to get more data_id)
        if place_id or data_id:
            # Se ainda não temos data_id mas temos place_id, SerpApi Details pode nos dar o CID
            if not data_id and place_id:
                details_res = serpapi.get_business_details(place_id)
                if details_res:
                    if 'place_results' in details_res:
                        # Soft merge: prioritize Serper/HasData basic fields if already present
                        for k, v in details_res['place_results'].items():
                            if k not in place_data or not place_data[k]:
                                place_data[k] = v
                    
                    if 'search_parameters' in details_res:
                        data_id = details_res['search_parameters'].get('data_id')
    
        # Deep Data Containers
        reviews_data = {}
        photos_data = {}
        posts_data = {}
    
        if data_id or place_id:
            import concurrent.futures
            try:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    # PRIORIDADE 1: HasData (Economia de Custo)
                    # Passamos ambos place_id e data_id (CID) para maximizar chance de sucesso
                    f_hd_revs = executor.submit(hasdata.get_reviews, place_id=place_id, data_id=data_id)
                    f_hd_imgs = executor.submit(hasdata.get_photos, place_id=place_id, data_id=data_id)
                    f_posts = executor.submit(serpapi.get_place_posts, data_id or place_id, gl=gl)
                    
                    reviews_data = f_hd_revs.result(timeout=15) or {}
                    photos_data = f_hd_imgs.result(timeout=15) or {}
                    posts_data = f_posts.result(timeout=15) or {}
                    
                    # FALLBACK: Se HasData falhar em reviews/fotos, tenta SerpApi
                    if not reviews_data and data_id:
                        logger.info(f"HealthCheck: Falling back to SerpApi for reviews ({data_id})")
                        reviews_data = serpapi.get_place_reviews(data_id, gl=gl) or {}
                        
                    if not photos_data and data_id:
                        logger.info(f"HealthCheck: Falling back to SerpApi for photos ({data_id})")
                        photos_data = serpapi.get_place_photos(data_id, gl=gl) or {}
                        
            except Exception as e:
                logger.error(f"HealthCheck: Deep fetch error {place_id}: {e}")
    
        # --- SIGNAL ANALYSIS ---
        # 1. Review Signals
        reviews_list = reviews_data.get('reviews', [])
        total_revs = len(reviews_list) or place_data.get('reviewsCount', 0)
        owner_replied = any(r.get('response') for r in reviews_list)
        
        # 2. Visual Signals
        photos_list = photos_data.get('photos', [])
        # HasData photos are in 'images'
        photo_cats = photos_data.get('categories', [])
        has_owner_photos = any('owner' in str(c.get('title', '')).lower() for c in photo_cats) or \
                           any('owner' in str(p.get('source', '')).lower() for p in photos_list)
        
        has_video = has_kp_video or \
                    any('video' in str(c.get('title', '')).lower() for c in photo_cats) or \
                    any(p.get('video') for p in photos_list)

        has_interior = any(x in str(c.get('title', '')).lower() for x in photo_cats for x in ['interior', 'inside', 'dentro'])
        has_exterior = any(x in str(c.get('title', '')).lower() for x in photo_cats for x in ['exterior', 'street view', 'outside', 'fachada'])

        # 3. Post/Update Signals
        posts_list = posts_data.get('posts', []) or posts_data.get('updates', [])
        has_posts = len(posts_list) > 0
        
        # --- VERIFICATION STATUS ---
        is_claimed = place_data.get('verified') or place_data.get('claimed')
        is_managed = owner_replied or has_owner_photos or has_posts or is_claimed

        # --- CRITERIA EVALUATION (17 points) ---
        criteria = Config.HEALTH_CHECK_CRITERIA
        score = 0
        criteria_results = []
        details = []
        
        # Metrics for AI Summary
        replied_count = sum(1 for r in reviews_list if r.get('response'))
        unreplied_count = total_revs - replied_count
        positive_points = 0
        moderate_issues = 0
        critical_issues = 0
        
        for c in criteria:
            cid = c['id']
            passed = False
            status = 'critical'
            res_score = 0
            
            if cid == 1: # Hours
                passed = bool(place_data.get('hours') or place_data.get('operating_hours'))
            elif cid == 2: # Product Photos
                passed = has_owner_photos or len(photos_list) > 10 or len(place_data.get('photos', [])) > 5
            elif cid == 3: # Videos
                passed = has_video
            elif cid == 4: # Verified
                passed = is_managed
                if passed: details.append("Perfil Gerenciado (Sinais ativos detectados)")
            elif cid == 5: # Website
                ws = place_data.get('website', '').lower()
                passed = bool(ws)
                if passed and any(d in ws for d in ['facebook.com', 'instagram.com', 'linktr.ee']):
                    passed = False; details.append(f"Site detectado é rede social ({ws})")
            elif cid == 6: # Q&A
                passed = bool(place_data.get('questions_and_answers'))
                if not passed and (is_managed and len(rich_extensions) > 0): passed = True
            elif cid == 7: # Posts
                passed = has_posts
            elif cid == 8: # Description
                desc = place_data.get('description') or place_data.get('about', {}).get('summary')
                if not desc and has_posts: desc = posts_list[0].get('description')
                passed = bool(desc and len(str(desc)) > 15)
            elif cid == 9: # Social Presence
                passed = bool(place_data.get('profiles')) or has_posts
            elif cid == 10: # Maps Presence
                passed = True
            elif cid == 11: # Exterior
                passed = has_exterior or (has_owner_photos and len(photos_list) > 15)
            elif cid == 12: # Interior
                passed = has_interior or (has_owner_photos and len(photos_list) > 15)
            elif cid == 13: # Rich Info
                passed = bool(place_data.get('menu')) or bool(place_data.get('products')) or \
                         len(rich_extensions) > 0 or has_posts
            elif cid == 14: # Reviews Presence
                rc = place_data.get('reviews') or 0
                passed = rc >= 5
            elif cid == 15: # Address
                passed = bool(place_data.get('address'))
            elif cid == 16: # Logo
                passed = bool(place_data.get('thumbnail') or place_data.get('logo'))
            elif cid == 17: # Review Response
                passed = owner_replied
            
            if passed: 
                status = 'positive'; res_score = c['weight']
                positive_points += 1
            else:
                if c['type'] == 'critical': critical_issues += 1
                else: moderate_issues += 1
            
            score += res_score
            criteria_results.append({
                'id': cid, 'name_pt': c['name_pt'], 'name_es': c['name_es'],
                'passed': passed, 'weight': c['weight'], 'type': c['type']
            })

        # --- SCORE NORMALIZATION ---
        if is_managed:
            if score < 95 and score > 80: score = 95
            elif score <= 80 and score > 60: score += 10
        
        score = min(max(score, 0), 100)

        # Relatório final
        # recommendations calculation
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
                logger.info(f"No existing metrics for client {client_id} today. Triggering scan.")
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
            logger.error(f"Failed to integrate RankTracker metrics: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

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
             logger.error(f"AI Generation failed for Public Audit: {e}")
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
            verification_status_unknown = True
        else:
            verification_status_unknown = False

        if is_verified:
            score += 15
            positive_points += 1
            details.append("Perfil Verificado e Gerenciado (Confirmado via Google)")
        elif not verification_status_unknown:
            msg = "Perfil não verificado ou requer ação manual no Google Business Profile."
            if 'resolveOwnershipConflict' in gain_vcom:
                msg = "Conflito de Propriedade: Outra pessoa já verificou este local no Google."
            elif 'complyWithGuidelines' in gain_vcom:
                 msg = "Perfil Suspenso ou Fora das Diretrizes: Requer regularização imediata com o suporte do Google."
            elif 'verify' in gain_vcom:
                 has_pending = any(v.get('state') != 'COMPLETED' for v in verifications)
                 if has_pending:
                     msg = "Verificação em Andamento: O processo foi iniciado mas ainda não foi concluído no Google."
                 else:
                     msg = "Perfil não Verificado: Requer iniciar o processo de verificação oficial."
            
            details.append(msg)
            critical_issues += 1
        
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
             details.append("Sem horário de funcionamento.")
             moderate_issues += 1

        # --- B. Imagem e Conteúdo (Max 30) ---
        photo_count = len(media_items)
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
            details.append("Sem fotos do interior/loja.")

        # reviews usando dados globais (v4 summary)
        avg_rating = loc_details.get('averageRating', 0)
        review_count = loc_details.get('totalReviewCount', 0)
        
        if (avg_rating or 0) == 0:
            with get_db() as db:
                from app.models import GMBReview
                cached_reviews = db.query(GMBReview).filter(GMBReview.location_link_id == link.id).all()
                if cached_reviews:
                    review_count = len(cached_reviews)
                    avg_rating = sum([r.star_rating for r in cached_reviews]) / review_count
        
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

        if not is_verified and not verification_status_unknown:
            score = score * 0.8

        score = min(100, max(0, score))
        
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
            
            if radar_metrics:
                report_data['radar_metrics'] = radar_metrics
                report_data['summary']['text'] += f" | Autoridade Local: {int(radar_metrics['authority'])}"
                
        except Exception as e:
            current_app.logger.error(f"Failed to integrate RankTracker metrics in Official Audit: {str(e)}")
            pass
        
        # --- AI Internal Analysis Generation ---
        try:
             from app.services.gemini_service import GeminiService
             gemini = GeminiService()
             
             if gemini.model:
                 website_url = loc_details.get('websiteUri')
                 site_type = HealthCheckService._detect_site_type(website_url)
                 
                 input_data = {
                     'business_name': loc_details.get('title'),
                     'language': 'es',
                     'criteria_results': [],
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
                 
                 ai_summary = gemini.generate_internal_audit_summary(input_data)
                 report_data['ai_internal_analysis'] = ai_summary
                 
        except Exception as e:
             current_app.logger.error(f"AI Generation failed for Official Audit: {e}")
        
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
