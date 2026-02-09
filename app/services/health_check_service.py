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
        Lógica DE PONTUAÇÃO RIGOROSA (Estilo Perplexity/Auditores Reais).
        """
        serper = SerperService()
        result = serper.search_places(query, location=location, limit=1)
        
        if not result.get('success') or not result.get('places'):
            return {'success': False, 'error': 'Empresa não encontrada nos mapas.'}
            
        place_data = result['places'][0]
        
        # --- Lógica de Pontuação Rigorosa ---
        # Objetivo: Um perfil "médio" deve ter nota ~40-50.
        # Um perfil "bom" ~70-80.
        # Perfeito ~95-100.
        
        score = 0
        details = []
        positive_points = 0
        moderate_issues = 0
        critical_issues = 0
        
        # --- 1. Fundamentos Digitais (Max 30) ---
        # Nome e Categoria (Básico do Básico)
        if place_data.get('title') and place_data.get('category'):
            score += 5
            positive_points += 1
            details.append(f"Identidade básica: {place_data.get('category')}")
        else:
            details.append("Categoria ou nome mal definidos.")
            moderate_issues += 1

        # Website (CRÍTICO - Grande diferencial)
        if place_data.get('website'):
            score += 15
            positive_points += 1
            details.append("Website vinculado (Autoridade +15).")
        else:
            # Penalidade Severa implícita (perde 15 pontos possíveis)
            details.append("Sem website vinculado (Perda crítica de tráfego/autoridade).")
            critical_issues += 1
            
        # Endereço Físico Validado
        if place_data.get('address'):
            score += 5
            positive_points += 1
        else:
            details.append("Endereço não listado claramente.")
            moderate_issues += 1
            
        # CID/Place ID
        if place_data.get('cid') or place_data.get('placeId'):
            score += 5 # Apenas ter o ID não é mérito, é obrigação.
            positive_points += 1
            
        # --- 2. Contato e Acessibilidade (Max 20) ---
        # Telefone
        phone = place_data.get('phone') or place_data.get('phoneNumber')
        if phone:
            score += 10
            positive_points += 1
            details.append("Telefone disponível.")
        else:
            details.append("Sem telefone de contato (Perda crítica de leads).")
            critical_issues += 1
            
        # Horário de Funcionamento (Indica perfil ativo)
        # Serper retorna 'hours' ou 'openingHours' muitas vezes como texto ou lista
        if place_data.get('hours') or place_data.get('openingHours'):
            score += 10
            positive_points += 1
            details.append("Horário de funcionamento cadastrado.")
        else:
            details.append("Sem horário de funcionamento (Clientes não sabem quando ir).")
            moderate_issues += 1

        # --- 3. Reputação e Prova Social (Max 35) ---
        rating = place_data.get('rating', 0)
        reviews = place_data.get('reviews', 0) or place_data.get('user_ratings_total', 0)
        
        # Avaliação (Qualidade)
        if reviews > 0:
            if rating >= 4.8:
                score += 15
                details.append(f"Avaliação Excepcional ({rating}).")
            elif rating >= 4.4:
                score += 10
                details.append(f"Boa Avaliação ({rating}).")
            elif rating >= 4.0:
                score += 5
                details.append(f"Avaliação aceitável ({rating}).")
            else:
                score -= 5 # Penalidade por nota ruim
                details.append(f"Avaliação baixa ({rating}). Alerta de reputação!")
                critical_issues += 1
        else:
            # Sem reviews = Sem prova social
            details.append("Zero avaliações. Perfil invisível socialmente.")
            critical_issues += 1
            
        # Volume (Quantidade gera relevância)
        if reviews > 100:
            score += 20
            positive_points += 1
            details.append(f"Autoridade estabelecida ({reviews} reviews).")
        elif reviews > 50:
            score += 15
            positive_points += 1
        elif reviews > 20:
            score += 10
        elif reviews > 5:
            score += 5
        else:
             details.append(f"Poucos reviews ({reviews}). Baixa relevância.")
             moderate_issues += 1

        # --- 4. Conteúdo Visual (Max 15) ---
        # Serper geralmente retorna 'thumbnail' ou 'imageUrl' se tiver foto
        if place_data.get('thumbnail') or place_data.get('imageUrl') or place_data.get('image'):
            score += 15
            positive_points += 1
            details.append("Presença visual detectada (Capa/Fotos).")
        else:
            details.append("Sem fotos de destaque aparentes.")
            moderate_issues += 1
            
        # --- Ajustes Finais ---
        score = min(100, max(0, score)) # Clamp entre 0 e 100
        
        # Mapeando para o formato detalhado do relatório
        top_critical_issues = []
        recommendations = []
        
        for detail in details:
            if any(x in detail.lower() for x in ["crítica", "sem website", "sem telefone", "zero", "baixa"]):
                top_critical_issues.append({
                    'name': 'Ponto Crítico',
                    'message': detail
                })
                recommendations.append(f"Prioridade: {detail}")
            elif "melhorar" in detail.lower() or "poucos" in detail.lower():
                 recommendations.append(f"Oportunidade: {detail}")
            else:
                 recommendations.append(f"Manter: {detail}")
                 
        if score < 40:
             recommendations.append("URGENTE: Este perfil precisa de uma revitalização completa.")
        elif score < 70:
             recommendations.append("Melhoria: Foque em conseguir mais reviews e adicionar fotos.")

        report_data = {
            'business_name': place_data.get('title'),
            'source_data': place_data,
            'details': details,
            'top_critical_issues': top_critical_issues,
            'recommendations': recommendations,
            'summary': { 
                'critical_issues_count': critical_issues,
                'moderate_issues_count': moderate_issues,
                'positive_points_count': positive_points,
                'text': f"Score Rigoroso: {score}/100 - {critical_issues} alertas críticos."
            }
        }
        
        # Salvar no banco (se houver client_id)
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
            'details': details,
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
            reviews = service.list_reviews(location_name, page_size=50)
            media_items = service.list_media(location_name)
        except Exception as e:
             return {'success': False, 'error': f'Erro de API Google: {str(e)}'}

        # 3. Calcular Score (Rigoroso)
        score = 0
        details = []
        positive_points = 0
        moderate_issues = 0
        critical_issues = 0
        
        # --- A. Verificação Básica (Max 30) ---
        if loc_details.get('title'):
            score += 5
            positive_points += 1
        
        # Categoria (Metadata ou Profile)
        # A API v1 retorna categories dentro de 'profile' ou 'storefrontAddress'?? 
        # Na verdade categories é uma chamada separada ou parte de 'categories' se usar readMask correto.
        # O get_location_details usa readMask='name,title,storefrontAddress,phoneNumbers,websiteUri,regularHours,profile,metadata'
        # 'profile' costuma conter categoria? Vamos checar. Se não, assumimos ok por ser verificado.
        # Vamos focar no que temos certeza: Telefone, Site, Horário.
        
        if loc_details.get('phoneNumbers'):
            score += 10
            positive_points += 1
        else:
            details.append("Sem telefone cadastrado.")
            critical_issues += 1
            
        if loc_details.get('websiteUri'):
            score += 10
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

        # --- C. Reputação (Max 40) ---
        # Reviews
        review_count = len(reviews)
        total_rating = sum([r.get('starRating', 0) for r in reviews])
        avg_rating = (total_rating / review_count) if review_count > 0 else 0
        
        # Taxa de Resposta
        replied_count = sum([1 for r in reviews if r.get('hasReply')])
        reply_rate = (replied_count / review_count) * 100 if review_count > 0 else 0
        
        if review_count > 0:
            if avg_rating >= 4.5:
                score += 15
                positive_points += 1
                details.append(f"Excelente avaliação ({avg_rating:.1f}).")
            elif avg_rating >= 4.0:
                 score += 10
                 moderate_issues += 1
            else:
                 details.append(f"Avaliação baixa ({avg_rating:.1f}).")
                 critical_issues += 1
                 
            # Reply Rate importa muito para gestão
            if reply_rate >= 90:
                score += 15
                positive_points += 1
                details.append("Excelente taxa de resposta.")
            elif reply_rate >= 50:
                score += 5
                moderate_issues += 1
                details.append(f"Taxa de resposta média ({reply_rate:.0f}%).")
            else:
                critical_issues += 1
                details.append(f"Baixa taxa de resposta ({reply_rate:.0f}%).")
        else:
            details.append("Sem avaliações.")
            critical_issues += 1
            
        # Penalidade extra se review count for alto mas reply rate for 0
        if review_count > 20 and reply_rate < 10:
             score -= 10
             details.append("Alerta: Muitas avaliações sem resposta!")
             critical_issues += 1

        # --- Montar Relatório ---
        top_critical_issues = []
        recommendations = []
        
        for detail in details:
            if "crítico" in detail.lower() or "sem" in detail.lower() or "baixa" in detail.lower():
                top_critical_issues.append({'name': 'Atenção', 'message': detail})
                recommendations.append(f"Ação: {detail}")
            else:
                 recommendations.append(f"Manter: {detail}")

        report_data = {
            'business_name': loc_details.get('title'),
            'source_data': loc_details, # Dados brutos
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
            health_check.source = 'official' # Oficial!
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
