"""
PURETEGO CRM - GBP Scan Service
Parseia HTML bruto do Google Search/Maps para extrair dados de perfil GBP.
Zero custo de API — dados extraídos via DOM scraping pelo bookmarklet/extensão.
"""

import re
import json
import logging
import requests
from datetime import datetime
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class GBPScanService:
    """
    Service que recebe HTML estruturado (já extraído pelo bookmarklet/extensão)
    e gera um relatório de Health Check compatível com o formato existente.
    """

    # User-Agent para simular navegador real
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'es-PY,es;q=0.9,pt-BR;q=0.8,pt;q=0.7,en;q=0.6',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }

    @staticmethod
    def perform_direct_scan(business_name, location=''):
        """
        Scan direto: busca o negócio usando Serper Places API (1 API call = 1 crédito).
        Muito mais confiável que scraping e usa apenas 1 crédito vs 3-6 do Quick Health Check.
        
        Args:
            business_name: Nome do negócio a pesquisar
            location: Localização opcional (cidade, país)
            
        Returns:
            dict com dados extraídos no formato scan_data (compatível com perform_scan_audit)
        """
        try:
            from app.services.serper_service import SerperService
            
            serper = SerperService()
            query = business_name
            if location:
                query += f' {location}'

            # 1 API call via Serper Places
            result = serper.search_places(query, location=location, limit=1)
            
            if not result.get('success') or not result.get('places'):
                return {
                    'business_name': business_name,
                    'scan_type': 'direct',
                    'error': 'Negócio não encontrado. Tente ser mais específico no nome.'
                }

            place = result['places'][0]

            # Map Serper place data to scan_data format
            scan_data = {
                'page_type': 'serper_places',
                'scan_type': 'direct',
                'url': f"https://www.google.com/maps/place/?q=place_id:{place.get('placeId', '')}",
                'business_name': place.get('title', business_name),
                'address': place.get('address', ''),
                'phone': place.get('phoneNumber', '') or place.get('phone', ''),
                'website': place.get('website', ''),
                'rating': place.get('rating'),
                'reviews_count': place.get('ratingCount', 0) or place.get('reviews', 0),
                'hours': None,  # Serper places doesn't always return hours
                'categories': [place.get('category', '')] if place.get('category') else [],
                'description': '',
                'has_posts': False,
                'has_photos': bool(place.get('thumbnailUrl')),
                'photo_count': 1 if place.get('thumbnailUrl') else 0,
                'has_videos': False,
                'has_logo': bool(place.get('thumbnailUrl')),
                'has_q_and_a': False,
                'is_verified': False,
                'has_owner_photos': False,
                'has_review_responses': False,
                'has_interior_photos': False,
                'has_exterior_photos': False,
                'has_social_profiles': False,
                'has_products_services': False,
                'cid': place.get('cid', ''),
                'place_id': place.get('placeId', '') or place.get('place_id', ''),
                'coordinates': None,
            }

            # Parse hours if available
            opening_hours = place.get('openingHours') or place.get('hours')
            if opening_hours:
                scan_data['hours'] = str(opening_hours)

            # Detect website type
            ws = scan_data['website'].lower()
            if ws:
                is_social = any(d in ws for d in ['facebook.com', 'instagram.com', 'linktr.ee', 'tiktok.com'])
                scan_data['has_social_profiles'] = is_social

            # Coordinates
            lat = place.get('latitude')
            lng = place.get('longitude')
            if lat and lng:
                scan_data['coordinates'] = {'lat': lat, 'lng': lng}

            # Heuristics from available data
            reviews_count = scan_data['reviews_count'] or 0
            if reviews_count > 0:
                scan_data['is_verified'] = True  # Businesses with reviews are typically verified

            return scan_data

        except Exception as e:
            logger.exception(f"Direct scan failed for {business_name}: {e}")
            return {'business_name': business_name, 'scan_type': 'direct', 'error': str(e)}

    @staticmethod
    def _extract_from_serp(soup, url):
        """Extrai dados do Knowledge Panel da SERP do Google."""
        data = {
            'page_type': 'search',
            'business_name': '',
            'address': '',
            'phone': '',
            'website': '',
            'rating': None,
            'reviews_count': 0,
            'hours': None,
            'categories': [],
            'description': '',
            'has_posts': False,
            'has_photos': False,
            'photo_count': 0,
            'has_videos': False,
            'has_logo': False,
            'has_q_and_a': False,
            'is_verified': False,
            'has_owner_photos': False,
            'has_review_responses': False,
            'has_interior_photos': False,
            'has_exterior_photos': False,
            'has_social_profiles': False,
            'has_products_services': False,
            'cid': '',
            'place_id': '',
            'coordinates': None,
        }

        text = soup.get_text(' ', strip=True).lower()

        # Business name from KP
        for sel in ['[data-attrid="title"] span', '.SPZz6b h2 span', '.qrShPb span']:
            el = soup.select_one(sel)
            if el:
                data['business_name'] = el.get_text(strip=True)
                break

        # Rating
        for sel in ['.Aq14fc', '.yi40Hd.YrbPuc', '[data-attrid*="rating"]']:
            el = soup.select_one(sel)
            if el:
                match = re.search(r'[\d,\.]+', el.get_text())
                if match:
                    data['rating'] = match.group().replace(',', '.')
                break

        # Reviews count
        for sel in ['.hqzQac span', '.z5jxId']:
            el = soup.select_one(sel)
            if el:
                match = re.search(r'[\d.,]+', el.get_text())
                if match:
                    data['reviews_count'] = int(re.sub(r'[^\d]', '', match.group()))
                break

        # Address
        el = soup.select_one('[data-attrid*="address"] .LrzXr') or soup.select_one('.LrzXr')
        if el:
            data['address'] = el.get_text(strip=True)

        # Phone
        el = soup.select_one('[data-attrid*="phone"] .LrzXr') or soup.select_one('a[href^="tel:"]')
        if el:
            data['phone'] = el.get_text(strip=True)

        # Website
        el = soup.select_one('[data-attrid*="website"] a') or soup.select_one('a.n1obkb')
        if el:
            data['website'] = el.get('href', el.get_text(strip=True))

        # Category
        for sel in ['.YhemCb', '.YDC0yf']:
            el = soup.select_one(sel)
            if el:
                data['categories'] = [el.get_text(strip=True)]
                break

        # Hours
        el = soup.select_one('[data-attrid*="hours"] .LrzXr')
        if el:
            data['hours'] = el.get_text(strip=True)

        # Description
        el = soup.select_one('[data-attrid="description"] span')
        if el:
            data['description'] = el.get_text(strip=True)

        # Verification (heuristic)
        data['is_verified'] = 'no reclamado' not in text and 'não reivindicado' not in text and 'unclaimed' not in text
        
        # Photos
        photos = soup.select('[data-attrid*="lu attribute list"] img')
        data['photo_count'] = len(photos)
        data['has_photos'] = len(photos) > 0
        data['has_logo'] = any('logo' in (img.get('alt', '').lower()) for img in photos)

        # Posts, Q&A, social, products (heuristic from text)
        data['has_posts'] = 'publicaciones' in text or 'atualizações' in text or 'updates' in text
        data['has_q_and_a'] = bool(soup.select_one('[data-attrid*="question"]'))
        data['has_social_profiles'] = bool(soup.select_one('[data-attrid*="social"]'))
        data['has_products_services'] = bool(soup.select_one('[data-attrid*="product"]') or soup.select_one('[data-attrid*="menu"]'))

        # CID
        el = soup.select_one('[data-ludocid]')
        if el:
            data['cid'] = el.get('data-ludocid', '')

        # Interior/exterior heuristic
        all_img_alt = ' '.join(img.get('alt', '').lower() for img in soup.select('img'))
        data['has_interior_photos'] = 'interior' in all_img_alt
        data['has_exterior_photos'] = 'exterior' in all_img_alt or 'fachada' in all_img_alt
        data['has_videos'] = 'video' in all_img_alt or bool(soup.select('video'))

        return data

    @staticmethod
    def _extract_from_maps_html(soup, url):
        """Extrai dados básicos do HTML do Google Maps (server-side, limitado)."""
        data = {
            'page_type': 'maps',
            'business_name': '',
            'address': '',
            'phone': '',
            'website': '',
            'rating': None,
            'reviews_count': 0,
            'hours': None,
            'categories': [],
            'description': '',
            'has_posts': False,
            'has_photos': False,
            'photo_count': 0,
            'has_videos': False,
            'has_logo': False,
            'has_q_and_a': False,
            'is_verified': False,
            'has_owner_photos': False,
            'has_review_responses': False,
            'has_interior_photos': False,
            'has_exterior_photos': False,
            'has_social_profiles': False,
            'has_products_services': False,
            'cid': '',
            'place_id': '',
            'coordinates': None,
        }

        # Google Maps pages are heavily JavaScript-rendered, so server-side
        # extraction is very limited. Try to get APP_INITIALIZATION_STATE.
        text = soup.get_text(' ', strip=True)
        script_text = str(soup)

        # Try to extract from meta tags (Google Maps has some)
        for meta in soup.select('meta[content]'):
            content = meta.get('content', '')
            name = meta.get('name', '') or meta.get('property', '')
            if 'og:title' in name and content:
                data['business_name'] = content.split(' - ')[0].strip()

        # Coordinates from URL
        coord_match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url)
        if coord_match:
            data['coordinates'] = {'lat': float(coord_match.group(1)), 'lng': float(coord_match.group(2))}

        # CID from URL
        cid_match = re.search(r'[?&]cid=(\d+)', url)
        if cid_match:
            data['cid'] = cid_match.group(1)

        return data

    @staticmethod
    def perform_scan_audit(scan_data, user_id):
        """
        Método principal: recebe dados do scan, avalia critérios.
        Se client_id for fornecido, salva no DB. Caso contrário, retorna dados sem persistir
        (HealthCheck.client_id é NOT NULL — scans avulsos são retornados mas não salvos).
        
        Args:
            scan_data: dict com dados extraídos pelo bookmarklet/extensão
            user_id: ID do usuário que fez o scan
            
        Returns:
            dict com success, score, report, check_id (check_id=None se não salvo)
        """
        from config.settings import Config
        from app.models import HealthCheck, Client
        from config.database import get_db

        try:
            # 1. Extrair dados estruturados do payload
            parsed = GBPScanService._parse_scan_data(scan_data)
            
            if not parsed.get('business_name'):
                return {'success': False, 'error': 'Nome do negócio não detectado no scan.'}

            # 2. Avaliar os 17 critérios
            criteria = Config.HEALTH_CHECK_CRITERIA
            evaluation = GBPScanService._evaluate_criteria(parsed, criteria)

            # 3. Montar relatório compatível com o formato existente
            report_data = {
                'business_name': parsed.get('business_name'),
                'source_data': {
                    'title': parsed.get('business_name'),
                    'address': parsed.get('address'),
                    'phone': parsed.get('phone'),
                    'website': parsed.get('website'),
                    'rating': parsed.get('rating'),
                    'reviewsCount': parsed.get('reviews_count'),
                    'hours': parsed.get('hours'),
                    'categories': parsed.get('categories', []),
                    'cid': parsed.get('cid'),
                    'placeId': parsed.get('place_id'),
                    'coordinates': parsed.get('coordinates'),
                    'scan_url': scan_data.get('url', ''),
                },
                'details': evaluation['details'],
                'criteria_results': evaluation['criteria_results'],
                'top_critical_issues': evaluation['top_critical_issues'],
                'recommendations': evaluation['recommendations'][:5],
                'summary': {
                    'critical_issues_count': evaluation['critical_issues'],
                    'moderate_issues_count': evaluation['moderate_issues'],
                    'positive_points_count': evaluation['positive_points'],
                    'text': f"GBP Scan: {evaluation['score']}/100"
                },
                'criteria': [
                    {
                        'name': res['name_es'],
                        'status': 'Detectado' if res['passed'] else 'Não detectado',
                        'score': 100 if res['passed'] else 0
                    } for res in evaluation['criteria_results']
                ],
                'scan_metadata': {
                    'scan_type': scan_data.get('scan_type', 'bookmarklet'),
                    'scan_url': scan_data.get('url', ''),
                    'scan_date': datetime.now().isoformat(),
                    'page_type': parsed.get('page_type', 'unknown'),
                }
            }

            # 4. Save to DB only if linked to a client (client_id is NOT NULL in DB)
            check_id = None
            client_id = scan_data.get('client_id')

            if client_id:
                with get_db() as db:
                    health_check = HealthCheck(
                        client_id=client_id,
                        score=evaluation['score'],
                        report_data=report_data
                    )
                    health_check.source = 'gbp_scan'
                    health_check.origin_id = parsed.get('place_id') or parsed.get('cid')

                    db.add(health_check)
                    db.commit()
                    check_id = health_check.id

            return {
                'success': True,
                'check_id': check_id,
                'score': evaluation['score'],
                'report': report_data,
                'saved': check_id is not None,
            }

        except Exception as e:
            logger.exception(f"GBPScanService.perform_scan_audit failed: {e}")
            return {'success': False, 'error': f'Erro ao processar scan: {str(e)}'}

    @staticmethod
    def _parse_scan_data(scan_data):
        """
        Parseia os dados estruturados enviados pelo bookmarklet/extensão.
        O bookmarklet/extensão já faz a extração do DOM e envia dados estruturados.
        """
        parsed = {
            'page_type': scan_data.get('page_type', 'search'),
            'business_name': scan_data.get('business_name', ''),
            'address': scan_data.get('address', ''),
            'phone': scan_data.get('phone', ''),
            'website': scan_data.get('website', ''),
            'rating': None,
            'reviews_count': 0,
            'hours': scan_data.get('hours'),
            'categories': scan_data.get('categories', []),
            'description': scan_data.get('description', ''),
            'has_posts': scan_data.get('has_posts', False),
            'has_photos': scan_data.get('has_photos', False),
            'photo_count': scan_data.get('photo_count', 0),
            'has_videos': scan_data.get('has_videos', False),
            'has_logo': scan_data.get('has_logo', False),
            'has_q_and_a': scan_data.get('has_q_and_a', False),
            'is_verified': scan_data.get('is_verified', False),
            'has_owner_photos': scan_data.get('has_owner_photos', False),
            'has_review_responses': scan_data.get('has_review_responses', False),
            'has_interior_photos': scan_data.get('has_interior_photos', False),
            'has_exterior_photos': scan_data.get('has_exterior_photos', False),
            'has_social_profiles': scan_data.get('has_social_profiles', False),
            'has_products_services': scan_data.get('has_products_services', False),
            'cid': scan_data.get('cid', ''),
            'place_id': scan_data.get('place_id', ''),
            'coordinates': scan_data.get('coordinates'),
        }

        # Parse rating
        rating_raw = scan_data.get('rating')
        if rating_raw:
            try:
                parsed['rating'] = float(str(rating_raw).replace(',', '.'))
            except (ValueError, TypeError):
                pass

        # Parse reviews count
        reviews_raw = scan_data.get('reviews_count')
        if reviews_raw:
            try:
                parsed['reviews_count'] = int(re.sub(r'[^\d]', '', str(reviews_raw)))
            except (ValueError, TypeError):
                pass

        return parsed

    @staticmethod
    def _evaluate_criteria(parsed, criteria):
        """
        Avalia os 17 critérios oficiais baseado nos dados parseados.
        Formato de saída compatível com o HealthCheckService existente.
        """
        score = 0
        criteria_results = []
        details = []
        recommendations = []
        positive_points = 0
        moderate_issues = 0
        critical_issues = 0

        for c in criteria:
            cid = c['id']
            passed = False

            if cid == 1:  # Horário de Funcionamento
                passed = bool(parsed.get('hours'))
            elif cid == 2:  # Fotos dos Produtos/Serviços
                passed = parsed.get('has_owner_photos', False) or parsed.get('photo_count', 0) > 5
            elif cid == 3:  # Vídeos
                passed = parsed.get('has_videos', False)
            elif cid == 4:  # Perfil Verificado
                passed = parsed.get('is_verified', False)
                if passed:
                    details.append("Perfil Verificado (detectado via scan)")
            elif cid == 5:  # Website
                ws = parsed.get('website', '').lower()
                passed = bool(ws)
                if passed and any(d in ws for d in ['facebook.com', 'instagram.com', 'linktr.ee']):
                    passed = False
                    details.append(f"Site detectado é rede social ({ws})")
            elif cid == 6:  # Q&A
                passed = parsed.get('has_q_and_a', False)
            elif cid == 7:  # Posts
                passed = parsed.get('has_posts', False)
            elif cid == 8:  # Descrição
                desc = parsed.get('description', '')
                passed = bool(desc and len(str(desc)) > 15)
            elif cid == 9:  # Presença Redes Sociais
                passed = parsed.get('has_social_profiles', False) or parsed.get('has_posts', False)
            elif cid == 10:  # Presença Google Maps
                passed = True  # Se fez scan, está no Maps
            elif cid == 11:  # Fotos Exterior
                passed = parsed.get('has_exterior_photos', False) or (
                    parsed.get('has_owner_photos', False) and parsed.get('photo_count', 0) > 15
                )
            elif cid == 12:  # Fotos Interior
                passed = parsed.get('has_interior_photos', False) or (
                    parsed.get('has_owner_photos', False) and parsed.get('photo_count', 0) > 15
                )
            elif cid == 13:  # Informações Produtos/Serviços
                passed = parsed.get('has_products_services', False) or parsed.get('has_posts', False)
            elif cid == 14:  # Avaliações
                passed = parsed.get('reviews_count', 0) >= 5
            elif cid == 15:  # Endereço
                passed = bool(parsed.get('address'))
            elif cid == 16:  # Logo
                passed = parsed.get('has_logo', False) or parsed.get('has_photos', False)
            elif cid == 17:  # Resposta a Avaliações
                passed = parsed.get('has_review_responses', False)

            res_score = c['weight'] if passed else 0
            score += res_score

            if passed:
                positive_points += 1
            else:
                if c['type'] == 'critical':
                    critical_issues += 1
                else:
                    moderate_issues += 1

            criteria_results.append({
                'id': cid,
                'name_pt': c['name_pt'],
                'name_es': c['name_es'],
                'passed': passed,
                'weight': c['weight'],
                'type': c['type']
            })

        # Score normalization
        is_managed = parsed.get('is_verified') or parsed.get('has_review_responses') or parsed.get('has_posts')
        if is_managed:
            if 80 < score < 95:
                score = 95
            elif 60 < score <= 80:
                score += 10

        score = min(max(score, 0), 100)

        # Recommendations
        if not parsed.get('is_verified'):
            recommendations.append("URGENTE: Reivindique e verifique seu perfil para proteger sua marca.")
        if not parsed.get('has_review_responses'):
            recommendations.append("Responda às avaliações pendentes para melhorar o ranking.")
        if not parsed.get('has_posts'):
            recommendations.append("Publique atualizações semanais (Posts) para manter o perfil ativo.")
        if not parsed.get('has_videos'):
            recommendations.append("Adicione vídeos. O Google valoriza muito conteúdo em vídeo.")
        for res in criteria_results:
            if not res['passed'] and res['type'] == 'critical':
                recommendations.append(f"Corrija: {res['name_es']} ausente.")

        top_critical_issues = [
            {'name': r['name_es'], 'message': 'Ausente'}
            for r in criteria_results if not r['passed'] and r['type'] == 'critical'
        ]

        return {
            'score': score,
            'criteria_results': criteria_results,
            'details': details,
            'recommendations': recommendations,
            'top_critical_issues': top_critical_issues,
            'positive_points': positive_points,
            'moderate_issues': moderate_issues,
            'critical_issues': critical_issues,
        }
