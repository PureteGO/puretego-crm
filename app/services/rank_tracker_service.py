import logging
from datetime import datetime
import math
from app.models.local_search import LocalSearchKeyword, LocalScanResult, LocalMetricsAggregated
from app.models import Client
from app.services.serpapi_service import SerpApiService
from config.database import get_db
from sqlalchemy import func

logger = logging.getLogger(__name__)

class RankTrackerService:
    
    @staticmethod
    def ensure_default_keywords(client_id):
        """
        Ensures the client has at least one keyword to track (Client Name).
        """
        with get_db() as db:
            count = db.query(LocalSearchKeyword).filter_by(client_id=client_id).count()
            if count == 0:
                client = db.query(Client).get(client_id)
                if client:
                    keyword = LocalSearchKeyword(
                        client_id=client_id,
                        keyword=client.name,
                        location=client.city or "Paraguay" # Default context
                    )
                    db.add(keyword)
                    db.commit()
                    logger.info(f"Created default keyword for client {client_id}: {client.name}")

    @staticmethod
    def perform_scan(client_id):
        """
        Executes SerpAPI scan for all keywords of a client.
        Saves results for Client and Competitors (from Local Pack).
        """
        RankTrackerService.ensure_default_keywords(client_id)
        
        with get_db() as db:
            keywords = db.query(LocalSearchKeyword).filter_by(client_id=client_id).all()
            client = db.query(Client).get(client_id)
            
            if not keywords or not client:
                return {'success': False, 'error': 'No keywords or client found'}
            
            serpapi = SerpApiService()
            today = datetime.now().date()
            
            # Check if already scanned today to avoid waste?
            # For now, we force scan if requested (Health Check logic usually implies on-demand or refreshed)
            
            results_stored = 0
            
            for k in keywords:
                # 1. Search SerpApi
                query = k.keyword
                location = k.location or client.city or "Paraguay"
                
                logger.info(f"Scanning keyword '{query}' in '{location}' for client {client_id}")
                
                scan_res = serpapi.search_local_pack(query, location, gl="py", hl="es")
                
                if 'error' in scan_res:
                    logger.error(f"SerpApi Error: {scan_res['error']}")
                    continue
                
                # 2. Parse Results
                local_results = scan_res.get('local_results', [])
                
                # If no local_results, try place_results (single result)?
                # The user prompt specifically focuses on 'local_results' (Pack).
                
                found_client = False
                
                for res in local_results:
                    # Check match
                    is_client = False
                    
                    # Fuzzy match logic
                    res_title = res.get('title', '').lower()
                    client_name = client.name.lower()
                    
                    # Match by Place ID / Data ID first
                    # We might not have client place_id stored safely in Client model yet, assume HealthCheck might have it
                    # Logic: if title matches significantly
                    if client_name in res_title or res_title in client_name:
                        is_client = True
                        found_client = True
                    
                    # Store Result
                    scan_entry = LocalScanResult(
                        search_keyword_id=k.id,
                        scan_date=today,
                        place_id=res.get('place_id') or res.get('data_id'),
                        title=res.get('title'),
                        position=res.get('position'),
                        rating=res.get('rating'),
                        reviews=res.get('reviews'),
                        type=res.get('type'),
                        address=res.get('address'),
                        is_client=is_client
                    )
                    db.add(scan_entry)
                    results_stored += 1
                
                # If client NOT found in list, we interpret this as "Not in Pack"
                # We do NOT create a fake "position 100" entry for Client here, 
                # because the metric logic counts "number of keywords with appearance".
                
            db.commit()
            
            # 3. Calculate Daily Metrics
            metrics = RankTrackerService.calculate_metrics(client_id, today)
            
            return {'success': True, 'scanned_keywords': len(keywords), 'metrics': metrics}

    @staticmethod
    def calculate_metrics(client_id, date_obj=None):
        """
        Aggregates LocalScanResults for a specific day into 0-100 scores.
        Follows the formulas provided in the user prompt.
        """
        if not date_obj:
            date_obj = datetime.now().date()
            
        with get_db() as db:
            # Get all keywords count
            total_keywords = db.query(LocalSearchKeyword).filter_by(client_id=client_id).count()
            if total_keywords == 0: return None
            
            # Get all scan results for this client on this date
            # Join with Keyword to ensure we filter by client
            results = db.query(LocalScanResult).join(LocalSearchKeyword).filter(
                LocalSearchKeyword.client_id == client_id,
                func.date(LocalScanResult.scan_date) == date_obj
            ).all()
            
            client_results = [r for r in results if r.is_client]
            competitor_results = [r for r in results if not r.is_client]
            
            # --- 1. Visibility ---
            # % of keywords where client appears in Local Pack
            # Count unique keywords where client appears
            client_found_keywords = set(r.search_keyword_id for r in client_results)
            visibility_score = (len(client_found_keywords) / total_keywords) * 100
            
            # --- 2. Average Position ---
            # Only for keywords where client appears
            if client_results:
                avg_pos = sum(r.position for r in client_results) / len(client_results)
                # Formula: 100 - ((avg_pos - 1) / 2) * 100 (Assuming top 3 pack, 2 scale)
                # If pos = 1 -> 100 - 0 = 100
                # If pos = 3 -> 100 - (1 * 100) = 0? Wait, (3-1)/2 = 1. 1*100 = 100. 100-100=0.
                # So Rank 1 = 100, Rank 3 = 0.
                # Let's soften this.
                # Rank 1 = 100, Rank 2 = 66, Rank 3 = 33? 
                # Formula: 100 - ( (pos - 1) * 33 ) might be safer for Top 3.
                # User proposed: 100 - ((media - 1) / 2) * 100.
                # Let's stick to a linear interpolation for 1-20 (since we fetch 20).
                # But "Local Pack" is usually top 3.
                # If looking at top 3:
                # 1 -> 100
                # 2 -> 66
                # 3 -> 33
                # >3 -> 0 (Not in pack visible)
                # However, our scan fetches 20.
                # Let's map Position 1..20 to Score 100..0
                pos_score = max(0, 100 - (avg_pos - 1) * 5) # 1=100, 2=95, 20=5
            else:
                pos_score = 0
            
            # --- 3. Reviews Score ---
            # 0.6 * rating_norm + 0.4 * review_vol_norm
            # Rating Norm: (Rating / 5) * 100 ? Or 3-5 scale map to 0-100?
            # User: "Normalizar rating para 0–100 considerando faixa 3–5 estrelas."
            # < 3 = 0. 3=0, 5=100. Formula: (Rating - 3) * 50.
            
            if client_results:
                # Use average of all occurrences (if appearing multiple times)
                avg_rating = sum(r.rating or 0 for r in client_results) / len(client_results)
                avg_reviews = sum(r.reviews or 0 for r in client_results) / len(client_results)
                
                rating_norm = max(0, min(100, (avg_rating - 3) * 50))
                
                # Review Volume Norm: Log scale against max competitor?
                # Find max reviews in the dataset for context
                max_reviews = max([r.reviews or 0 for r in competitor_results] + [avg_reviews]) if competitor_results else avg_reviews
                max_reviews = max(max_reviews, 10) # Avoid div/0 and low ceilings
                
                import math
                # Log normalization: log(val) / log(max)
                # Using log10
                vol_norm = (math.log10(max(1, avg_reviews)) / math.log10(max(1, max_reviews))) * 100
                vol_norm = max(0, min(100, vol_norm))
                
                reviews_score = 0.6 * rating_norm + 0.4 * vol_norm
            else:
                reviews_score = 0
                
            # --- 4. Local Authority ---
            # 0.4 * vis + 0.3 * pos + 0.3 * rev
            authority_score = 0.4 * visibility_score + 0.3 * pos_score + 0.3 * reviews_score
            
            # --- 5. Market Averages ---
            # Aggregating all competitors found
            market_vis = 0 # Cannot calculate visibility for others easily without tracking them explicitly
            # But we can calculate their Avg Position/Reviews/Authority WITHIN our scans
            
            if competitor_results:
                comp_positions = [r.position for r in competitor_results]
                comp_avg_pos = sum(comp_positions) / len(comp_positions)
                market_pos_score = max(0, 100 - (comp_avg_pos - 1) * 5)
                
                comp_ratings = [r.rating or 0 for r in competitor_results if r.rating]
                comp_revs = [r.reviews or 0 for r in competitor_results if r.reviews]
                
                avg_comp_rating = sum(comp_ratings) / len(comp_ratings) if comp_ratings else 0
                avg_comp_revs = sum(comp_revs) / len(comp_revs) if comp_revs else 0
                
                comp_rating_norm = max(0, min(100, (avg_comp_rating - 3) * 50))
                
                max_rev_context = max(max_reviews, avg_comp_revs) # Recalculate context
                comp_vol_norm = (math.log10(max(1, avg_comp_revs)) / math.log10(max(1, max_rev_context))) * 100
                
                market_reviews_score = 0.6 * comp_rating_norm + 0.4 * comp_vol_norm
                
                # Market Visibility: approx 50% as baseline? Or average of top competitors frequency?
                # Hard to estimate true visibility without full tracking.
                # Let's set it to average of our computed scores for now or a fixed benchmark
                market_vis = 50 # Baseline placeholder
                
                market_authority = 0.4 * market_vis + 0.3 * market_pos_score + 0.3 * market_reviews_score
            else:
                market_vis, market_pos_score, market_reviews_score, market_authority = 0, 0, 0, 0

            # --- Save Aggregated ---
            agg = db.query(LocalMetricsAggregated).filter_by(client_id=client_id, scan_date=date_obj).first()
            if not agg:
                agg = LocalMetricsAggregated(client_id=client_id, scan_date=date_obj)
            
            agg.visibility_score = visibility_score
            agg.avg_position_score = pos_score
            agg.reviews_score = reviews_score
            agg.local_authority_score = authority_score
            
            agg.market_avg_visibility = market_vis
            agg.market_avg_position = market_pos_score
            agg.market_avg_reviews = market_reviews_score
            agg.market_avg_authority = market_authority
            
            db.add(agg)
            db.commit()
            
            return agg
