"""
PURETEGO CRM - Health Check Service
Serviço para realizar auditorias de perfil (Public & Official)
"""

from app.models import HealthCheck, Client
from app.services.serper_service import SerperService
from config.database import get_db
import logging

logger = logging.getLogger(__name__)

class HealthCheckService:
    
    @staticmethod
    def perform_public_audit(client_id, query, location=None):
        """
        Realiza uma auditoria baseada em dados públicos (Serper.dev).
        Mapeia os dados para os 17 Critérios oficiais (Config.HEALTH_CHECK_CRITERIA).
        
        Nota: Em auditoria PÚBLICA, muitos itens retornam False (Vídeos, Posts, Q&A)
        pois não são visíveis sem API oficial. Isso gera um score baixo (~40-50)
        que motiva o cliente a conectar a conta.
        """
        from config.settings import Config
        # 1. Buscar no Serper (Maps)
        serper = SerperService()
        search_res = serper.search_places(query, limit=1)
        
        # Se não encontrou, tenta ser mais flexível com o nome
        if not search_res['success'] or not search_res.get('places'):
            # 1. Tentar limpar o nome (remover o que vem após hífen ou parênteses)
            clean_name = query.split("-")[0].split("(")[0].strip()
            
            # 2. Tentar buscar com o nome limpo + cidade para ser mais específico
            from app.models import Client
            with get_db() as db:
                client = db.query(Client).get(client_id)
                query = clean_name
                if client and (client.city or client.address):
                    location_hint = client.city or client.address.split(',')[0]
                    query = f"{clean_name} {location_hint}"
                
                search_res = serper.search_places(query, limit=1)
                
            # 3. Fallback: Se ainda falhar, tenta apenas o nome limpo
            if (not search_res['success'] or not search_res.get('places')) and clean_name != query:
                search_res = serper.search_places(clean_name, limit=1)

        if not search_res['success'] or not search_res.get('places'):
            return {'success': False, 'error': 'Empresa não encontrada nos mapas. Tente um nome mais simples (ex: apenas Universidad Autonoma San Sebastián).'}
            
        place_data = search_res['places'][0]
        criteria = Config.HEALTH_CHECK_CRITERIA
        
        score = 0
        criteria_results = []
        details = []
        positive_points = 0
        moderate_issues = 0
        critical_issues = 0
        
        # Avaliar cada critério
        for c in criteria:
            cid = c['id']
            passed = False
            name = c['name_pt']
            
            # --- Mapeamento Serper -> Critérios ---
            # --- Mapeamento Serper -> Critérios ---
            if cid == 1: # Horário
                passed = bool(place_data.get('hours') or place_data.get('openingHours'))
            elif cid == 2: # Fotos Produtos
                # Inferir: Se tem foto de capa, provavelmente tem produtos/serviços visíveis
                passed = bool(place_data.get('thumbnail') or place_data.get('image'))
            elif cid == 3: # Vídeos
                # Impossível detectar publicamente via Serper simples
                passed = False
            elif cid == 4: # Verificado
                # Inferir: Se tem CID, Telefone e Reviews, é altamente provável que seja gerenciado/verificado
                has_id = bool(place_data.get('cid') or place_data.get('placeId'))
                has_phone = bool(place_data.get('phone') or place_data.get('phoneNumber'))
                has_reviews = (place_data.get('reviews') or 0) > 0 or (place_data.get('ratingCount') or 0) > 0
                passed = (has_id and has_phone and has_reviews)
            elif cid == 5: # Site
                passed = bool(place_data.get('website'))
            elif cid == 6: # Q&A
                passed = False
            elif cid == 7: # Posts
                passed = False
            elif cid == 8: # Descrição
                passed = bool(place_data.get('description') or place_data.get('snippet'))
            elif cid == 9: # Redes Sociais
                # Às vezes serper traz 'profiles'
                passed = bool(place_data.get('profiles')) 
            elif cid == 10: # Presença Maps
                passed = bool(place_data.get('cid') or place_data.get('placeId'))
            elif cid == 11: # Fotos Exterior (Usamos thumbnail como proxy)
                passed = bool(place_data.get('thumbnail') or place_data.get('image'))
            elif cid == 12: # Fotos Interior
                # Inferir: Mesmo da regra de produtos
                passed = bool(place_data.get('thumbnail') or place_data.get('image'))
            elif cid == 13: # Info Produtos (Categoria)
                passed = bool(place_data.get('category'))
            elif cid == 14: # Avaliações
                passed = ((place_data.get('reviews') or 0) > 0 or (place_data.get('ratingCount') or 0) > 0)
            elif cid == 15: # Endereço
                passed = bool(place_data.get('address'))
            elif cid == 16: # Logotipo
                # Inferir: Se tem thumbnail, assumimos que tem logo ou foto principal
                passed = bool(place_data.get('thumbnail') or place_data.get('image'))
            elif cid == 17: # Resposta
                passed = False

            # Contabilizar
            if passed:
                score += c['weight']
                positive_points += 1
                details.append(f"{name}: OK")
            else:
                if c['type'] == 'critical':
                    critical_issues += 1
                    details.append(f"{name}: Ausente/Não detectado")
                elif c['type'] == 'moderate':
                    moderate_issues += 1
                
            criteria_results.append({
                'id': cid,
                'name_pt': c['name_pt'],
                'name_es': c['name_es'],
                'passed': passed,
                'weight': c['weight'],
                'type': c['type']
            })

        # Relatório final
        score = min(100, max(0, score))
        
        # Recomendações baseadas nas falhas
        recommendations = []
        for res in criteria_results:
            if not res['passed']:
                recommendations.append(f"Faltante: {res['name_es']} ({res['weight']} pts)")
                
        if score < 50:
             is_already_linked = False
             if client_id:
                 with get_db() as db:
                     from app.models import GMBLocationLink
                     is_already_linked = db.query(GMBLocationLink).filter(GMBLocationLink.client_id == client_id).first() is not None
             
             if not is_already_linked:
                 recommendations.insert(0, "URGENTE: Conecte sua conta do Google para análise completa e verificada.")

        # Top critical issues para o card
        top_critical_issues = []
        for res in criteria_results:
             if not res['passed'] and res['type'] == 'critical':
                  top_critical_issues.append({
                      'name': res['name_es'],
                      'message': 'Não detectado publicamente.'
                  })
        
        report_data = {
            'business_name': place_data.get('title'),
            'source_data': place_data,
            'details': details,
            'criteria_results': criteria_results, # NOVA CHAVE COM OS 17 PONTOS
            'top_critical_issues': top_critical_issues,
            'recommendations': recommendations[:5], # Top 5 dicas
            'summary': { 
                'critical_issues_count': critical_issues,
                'moderate_issues_count': moderate_issues,
                'positive_points_count': positive_points,
                'text': f"Score Público: {score}/100"
            }
        }
        
        check_id = None
        if client_id:
            with get_db() as db:
                health_check = HealthCheck(
                    client_id=client_id,
                    score=score,
                    report_data=report_data
                )
                health_check.source = 'public'
                health_check.origin_id = place_data.get('cid') or place_data.get('placeId')
                
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
    def perform_official_audit(client_id):
        """
        Realiza auditoria usando dados OFICIAIS da API do Google Business Profile.
        Requer que o cliente tenha um perfil vinculado.
        """
        from app.services.google_business_service import get_service_for_client
        from app.models import GMBLocationLink
        
        # 1. Obter Serviço e Link
        service = get_service_for_client(client_id)
        if not service:
             return {'success': False, 'error': 'Cliente não possui perfil do Google vinculado.'}
        
        with get_db() as db:
             link = db.query(GMBLocationLink).filter(
                GMBLocationLink.client_id == client_id,
                GMBLocationLink.is_primary == True
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
        gain_vcom = vcom_state.get('gainVoiceOfMerchant', {})
        
        if is_verified:
            score += 15 # Aumentado para 15
            positive_points += 1
            details.append("Perfil Verificado e Gerenciado (Confirmado via Google)")
        else:
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
             details.append("Sem horário de funcionamento.")
             moderate_issues += 1

        # --- B. Imagem e Conteúdo (Max 30) ---
        # Fotos (Verificadas via API Media)
        photo_count = len(media_items)
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
            details.append("Sem fotos publicadas.")
            
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

        # --- C. Reputação (Max 35) ---
        # Reviews usando dados globais (v4 summary)
        avg_rating = loc_details.get('averageRating', 0)
        review_count = loc_details.get('totalReviewCount', 0)
        
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

        # Relatório final formatado
        score = min(100, max(0, score))
        
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
            }
        }
        
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
