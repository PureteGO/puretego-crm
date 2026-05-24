"""
PURETEGO CRM - Google Business Service
Service class for Google Business Profile API operations
"""

import os
import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from google.oauth2.credentials import Credentials
import google.auth.transport.requests

from app.models import GoogleConnection, GMBLocationLink, GMBReview, GMBInsight
from config.database import get_db

logger = logging.getLogger(__name__)


class GoogleBusinessService:
    """
    Service for interacting with Google Business Profile APIs:
    - My Business Account Management API (accounts)
    - My Business Business Information API (locations)
    """
    
    ACCOUNTS_API_BASE = "https://mybusinessaccountmanagement.googleapis.com/v1"
    LOCATIONS_API_BASE = "https://mybusinessbusinessinformation.googleapis.com/v1"
    
    def __init__(self, connection: GoogleConnection):
        """Initialize with a GoogleConnection"""
        self.connection = connection
        self._ensure_valid_token()
    
    def _ensure_valid_token(self):
        """Ensure the access token is valid, refresh if needed"""
        if self.connection.is_token_expired():
            self._refresh_token()
    
    def _refresh_token(self):
        """Refresh the access token using the refresh token"""
        refresh_token = self.connection.get_refresh_token()
        if not refresh_token:
            raise ValueError("No refresh token available")
        
        try:
            creds = Credentials(
                token=self.connection.get_access_token(),
                refresh_token=refresh_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=os.environ.get('GOOGLE_CLIENT_ID'),
                client_secret=os.environ.get('GOOGLE_CLIENT_SECRET')
            )
            
            request_obj = google.auth.transport.requests.Request()
            creds.refresh(request_obj)
            
            # Update stored tokens
            with get_db() as db:
                conn = db.query(GoogleConnection).get(self.connection.id)
                if conn:
                    conn.set_access_token(creds.token)
                    conn.expires_at = creds.expiry or (datetime.utcnow() + timedelta(hours=1))
                    conn.last_error = None
                    db.commit()
                
            # Update local instance to match (without switching sessions)
            self.connection.set_access_token(creds.token)
            self.connection.expires_at = creds.expiry or (datetime.utcnow() + timedelta(hours=1))
            self.connection.last_error = None
                
        except Exception as e:
            with get_db() as db:
                conn = db.query(GoogleConnection).get(self.connection.id)
                conn.last_error = str(e)
                db.commit()
            raise
    
    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers"""
        return {
            'Authorization': f'Bearer {self.connection.get_access_token()}',
            'Content-Type': 'application/json'
        }
    
    def list_accounts(self) -> List[Dict]:
        """
        List all Google Business accounts accessible by this connection.
        Returns list of accounts with id, name, accountName, type.
        """
        url = f"{self.ACCOUNTS_API_BASE}/accounts"
        
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            
            data = response.json()
            accounts = data.get('accounts', [])
            
            return [
                {
                    'id': acc.get('name', '').split('/')[-1],  # Extract ID from "accounts/123"
                    'name': acc.get('name', ''),
                    'accountName': acc.get('accountName', ''),
                    'type': acc.get('type', 'UNKNOWN'),
                    'role': acc.get('role', 'UNKNOWN')
                }
                for acc in accounts
            ]
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                raise Exception("API Quota Exceeded or API Not Enabled (429). Please enable 'Google My Business Account Management API' in Google Cloud Console.")
            if e.response.status_code == 403:
                raise Exception("Permission Denied (403). Ensure the account has access and APIs are enabled.")
            raise Exception(f"Google API Error: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network Error listing accounts: {str(e)}")
    
    def list_locations(self, account_name: str) -> List[Dict]:
        """
        List all locations for a specific account.
        
        Args:
            account_name: Full account name (e.g., "accounts/123456789")
            
        Returns:
            List of locations with name, title, address, etc.
        """
        url = f"{self.LOCATIONS_API_BASE}/{account_name}/locations"
        params = {
            'readMask': 'name,title,storefrontAddress,metadata,profile'
        }
        
        try:
            response = requests.get(url, headers=self._get_headers(), params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            locations = data.get('locations', [])
            
            result = []
            for loc in locations:
                address = loc.get('storefrontAddress', {})
                address_lines = address.get('addressLines', [])
                
                # Ensure we have the full resource name (accounts/X/locations/Y) for v4 API compatibility
                name = loc.get('name', '')
                if not name.startswith('accounts/'):
                   # account_name is like "accounts/123"
                   name = f"{account_name}/{name}"

                result.append({
                    'name': name,
                    'title': loc.get('title', ''),
                    'address': ', '.join(address_lines) if address_lines else '',
                    'city': address.get('locality', ''),
                    'state': address.get('administrativeArea', ''),
                    'country': address.get('regionCode', ''),
                    'postal_code': address.get('postalCode', ''),
                    'metadata': loc.get('metadata', {})
                })
            
            return result
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                raise Exception("API Quota Exceeded or API Not Enabled (429). Please enable 'Google My Business Business Information API' in Google Cloud Console.")
            if e.response.status_code == 403:
                raise Exception("Permission Denied (403). Ensure the account has access and APIs are enabled.")
            raise Exception(f"Google API Error: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network Error listing locations: {str(e)}")
    
    def get_location_details(self, location_name: str) -> Dict:
        """
        Get detailed information for a specific location.
        
        Args:
            location_name: Full location name (e.g., "accounts/123/locations/456")
        """
        if '/locations/' in location_name:
             try:
                real_name = 'locations/' + location_name.split('/locations/')[1]
             except:
                real_name = location_name
        else:
             real_name = location_name

        url = f"{self.LOCATIONS_API_BASE}/{real_name}"
        params = {
            'readMask': 'name,title,storefrontAddress,phoneNumbers,websiteUri,regularHours,profile,metadata,categories,latlng,serviceArea'
        }
        
        try:
            response = requests.get(url, headers=self._get_headers(), params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Compatibility helpers for template
            if 'categories' in data:
                data['primaryCategory'] = data['categories'].get('primaryCategory')
            
            if 'metadata' in data:
                data['locationState'] = {
                    'isPublished': bool(data['metadata'].get('mapsUri')),
                    'isClean': True # Placeholder
                }
            
            return data
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error getting location details: {str(e)}")

    def get_location_summary_v4(self, location_name: str) -> Dict:
        """
        Get location summary from API (includes ratings/reviews count if available).
        Tries v4 first, then falls back to v1 if 404.
        """
        # Host for v4 My Business API
        v4_url = f"https://mybusiness.googleapis.com/v4/{location_name}"
        # Host for v1 Business Information API
        v1_url = f"https://mybusinessbusinessinformation.googleapis.com/v1/{location_name}"
        
        logger.debug(f"Attempting v4 Summary: {v4_url}")
        from flask import current_app
        
        try:
            # Try v4 first as it contains averageRating/totalReviewCount
            response = requests.get(v4_url, headers=self._get_headers(), timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                current_app.logger.info(f"GMB v4 Summary Data for {location_name}: {data}")
                return {
                    'averageRating': data.get('averageRating', 0),
                    'totalReviewCount': data.get('totalReviewCount', 0)
                }
            
            if response.status_code == 404:
                logger.debug(f"v4 Summary 404. Trying v1 fallback: {v1_url}")
                v1_resp = requests.get(v1_url, headers=self._get_headers(), timeout=30)
                if v1_resp.status_code == 200:
                    data = v1_resp.json()
                    current_app.logger.info(f"GMB v1 Location Data for {location_name}: {data}")
                    # v1 doesn't have ratings, but at least we confirmed the location exists
                    return {
                        'averageRating': 0,
                        'totalReviewCount': 0,
                        'v1_data': True,
                        'title': data.get('title', '')
                    }
                else:
                    logger.warning(f"v1 fallback also failed: {v1_resp.status_code}")
            
            current_app.logger.error(f"GMB Summary Error {response.status_code} for {location_name}: {response.text}")
            return {'averageRating': 0, 'totalReviewCount': 0, 'error': response.status_code}
            
        except Exception as e:
            current_app.logger.error(f"Exception getting summary for {location_name}: {e}")
            return {'averageRating': 0, 'totalReviewCount': 0, 'exception': str(e)}


    def get_voice_of_merchant_state(self, location_name: str) -> Dict:
        """
        Verify if a business profile is verified using the Voice of Merchant API.
        GET https://mybusinessverifications.googleapis.com/v1/{locationName}/VoiceOfMerchantState
        """
        if '/locations/' in location_name:
            try:
                real_name = 'locations/' + location_name.split('/locations/')[1]
            except:
                real_name = location_name
        else:
            real_name = location_name

        url = f"https://mybusinessverifications.googleapis.com/v1/{real_name}/VoiceOfMerchantState"
        
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {'hasVoiceOfMerchant': False, 'error': str(e)}

    def list_verifications(self, location_name: str) -> List[Dict]:
        """
        List verification attempts for a location.
        GET https://mybusinessverifications.googleapis.com/v1/{locationName}/verifications
        """
        if '/locations/' in location_name:
            try:
                real_name = 'locations/' + location_name.split('/locations/')[1]
            except:
                real_name = location_name
        else:
            real_name = location_name

        url = f"https://mybusinessverifications.googleapis.com/v1/{real_name}/verifications"
        
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            return response.json().get('verifications', [])
        except Exception:
            return []
    
    def list_reviews(self, location_name: str, page_size: int = 50) -> List[Dict]:
        """
        List reviews for a location.
        NOTE: Review reply feature deferred to Phase 2.
        
        Args:
            location_name: Full location name
            page_size: Number of reviews to fetch (max 50)
        """
        # The reviews endpoint uses a different base URL pattern
        # For v1 API: GET accounts/{accountId}/locations/{locationId}/reviews
        url = f"https://mybusiness.googleapis.com/v4/{location_name}/reviews"
        logger.debug(f"v4 Reviews URL: {url}")
        params = {
            'pageSize': min(page_size, 50)
        }
        
        try:
            response = requests.get(url, headers=self._get_headers(), params=params, timeout=30)
            logger.debug(f"v4 Reviews Status: {response.status_code}")
            
            from flask import current_app
            if response.status_code == 403:
                 logger.error(f"v4 Reviews 403 Body: {response.text}")
                 current_app.logger.error(f"GMB Reviews 403 Forbidden for {location_name}. Check if API is enabled and scopes are correct.")
                 raise Exception("Acceso Denegado (403): La 'Google My Business API' podría no estar habilitada en su Google Cloud Console o su cuenta no tiene permisos suficientes para este perfil.")
            
            if response.status_code != 200:
                 logger.error(f"v4 Reviews Error Body: {response.text}")
                 current_app.logger.error(f"GMB Reviews Error {response.status_code}: {response.text}")
            
            response.raise_for_status()
            
            data = response.json()
            reviews = data.get('reviews', [])
            
            if not reviews:
                 current_app.logger.info(f"GMB API returned successfully but with 0 reviews for {location_name}")
            
            result = []
            for review in reviews:
                reviewer = review.get('reviewer', {})
                reply = review.get('reviewReply', {})
                
                result.append({
                    'reviewId': review.get('reviewId', ''),
                    'name': review.get('name', ''),
                    'reviewerName': reviewer.get('displayName', 'Anonymous'),
                    'reviewerPhotoUrl': reviewer.get('profilePhotoUrl', ''),
                    'starRating': self._parse_star_rating(review.get('starRating', 'STAR_RATING_UNSPECIFIED')),
                    'comment': review.get('comment', ''),
                    'createTime': review.get('createTime', ''),
                    'updateTime': review.get('updateTime', ''),
                    'hasReply': bool(reply),
                    'replyComment': reply.get('comment', '') if reply else None,
                    'replyTime': reply.get('updateTime', '') if reply else None
                })
            
            return result
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error listing reviews: {str(e)}")

    def update_review_reply(self, review_name: str, comment: str) -> Dict:
        """
        Update or create a reply to a review.
        PUT https://mybusiness.googleapis.com/v4/{reviewName}/reply
        
        Args:
            review_name: Full review name (accounts/*/locations/*/reviews/*)
            comment: The reply text
        """
        url = f"https://mybusiness.googleapis.com/v4/{review_name}/reply"
        data = {
            'comment': comment
        }
        
        try:
            response = requests.put(url, headers=self._get_headers(), json=data, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"Error updating review reply: {str(e)}")

    def delete_review_reply(self, review_name: str) -> bool:
        """
        Delete a reply to a review.
        DELETE https://mybusiness.googleapis.com/v4/{reviewName}/reply
        """
        url = f"https://mybusiness.googleapis.com/v4/{review_name}/reply"
        
        try:
            response = requests.delete(url, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            return True
        except Exception:
            return False
    
    def list_media(self, location_name: str) -> List[Dict]:
        """
        List media items (photos) for a location.
        Uses v4 API as this is not yet fully replaced in v1.
        
        Args:
            location_name: Full location name
        """
        url = f"https://mybusiness.googleapis.com/v4/{location_name}/media"
        params = {'pageSize': 100}
        
        try:
            response = requests.get(url, headers=self._get_headers(), params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            media_items = data.get('mediaItems', [])
            
            result = []
            for item in media_items:
                result.append({
                    'name': item.get('name', ''),
                    'mediaFormat': item.get('mediaFormat', 'MEDIA_FORMAT_UNSPECIFIED'),
                    'locationAssociation': item.get('locationAssociation', {}).get('category', 'CATEGORY_UNSPECIFIED'),
                    'googleUrl': item.get('googleUrl', ''),
                    'thumbnailUrl': item.get('thumbnailUrl', ''),
                    'createTime': item.get('createTime', ''),
                    'views': item.get('insights', {}).get('viewCount', 0)
                })
            
            return result
            
        except Exception as e:
            # Media API might fail or be empty, don't crash
            return []
    
    def _parse_star_rating(self, rating_str: str) -> int:
        """Convert Google's star rating enum to integer"""
        rating_map = {
            'ONE': 1,
            'TWO': 2,
            'THREE': 3,
            'FOUR': 4,
            'FIVE': 5,
            'STAR_RATING_UNSPECIFIED': 0
        }
        return rating_map.get(rating_str, 0)
    
    def sync_reviews_to_cache(self, location_link_id: int) -> int:
        """
        Sync reviews from Google to local cache.
        Fetches up to 150 reviews (3 pages) to ensure cache is warm.
        """
        with get_db() as db:
            try:
                # Fetch up to 10 pages (total 500 reviews)
                for _ in range(10):
                    try:
                        url = f"https://mybusiness.googleapis.com/v4/{location_name}/reviews"
                        params = {'pageSize': 50}
                        if next_page_token:
                            params['pageToken'] = next_page_token
                            
                        response = requests.get(url, headers=self._get_headers(), params=params, timeout=30)
                        response.raise_for_status()
                        data = response.json()
                        
                        page_reviews = data.get('reviews', [])
                        all_reviews.extend(page_reviews)
                        
                        next_page_token = data.get('nextPageToken')
                        if not next_page_token:
                            break
                    except Exception as e:
                        from flask import current_app
                        current_app.logger.error(f"Error fetching reviews page: {e}")
                        break

                if not all_reviews:
                    return 0
                
                count = 0
                for review_data in all_reviews:
                    # Check if exists
                    review_name = review_data.get('name')
                    existing = db.query(GMBReview).filter(
                        GMBReview.gmb_review_id == review_name
                    ).first()
                    
                    if existing:
                        # Update potentially
                        existing.star_rating = self._parse_star_rating(review_data.get('starRating'))
                        existing.comment = review_data.get('comment', '')
                        reply = review_data.get('reviewReply', {})
                        existing.reply_comment = reply.get('comment', '')
                        if 'updateTime' in review_data:
                            try:
                                existing.updated_at = datetime.fromisoformat(review_data['updateTime'].replace('Z', '+00:00'))
                            except:
                                pass
                    else:
                        new_review = GMBReview(
                            location_link_id=location_link_id,
                            gmb_review_id=review_name,
                            reviewer_name=review_data.get('reviewer', {}).get('displayName', 'Anonymous'),
                            star_rating=self._parse_star_rating(review_data.get('starRating')),
                            comment=review_data.get('comment', ''),
                            reply_comment=review_data.get('reviewReply', {}).get('comment', ''),
                            review_date=datetime.fromisoformat(review_data['createTime'].replace('Z', '+00:00')) if 'createTime' in review_data else datetime.utcnow()
                        )
                        db.add(new_review)
                        count += 1
                
                db.commit()
                return count
            except Exception as e:
                link.sync_error = str(e)[:500]
                db.commit()
                raise

    def fetch_insights(self, location_name: str, days: int = 30) -> List[Dict]:
        """
        Fetch performance insights for a location using the GMB Performance API.
        Uses the GET dailyMetricsTimeSeries endpoint for maximum compatibility.
        """
        # Performance API requires EXACTLY 'locations/{location_id}'
        # Full resource names with 'accounts/' prefix cause 404 errors.
        if 'locations/' in location_name:
            location_id = location_name.split('locations/')[-1]
        else:
            location_id = location_name
            
        base_url = f"https://businessprofileperformance.googleapis.com/v1/locations/{location_id}/dailyMetricsTimeSeries"
        
        # Calculate time range - Google usually has a 2-3 day lag for performance data
        # So we fetch up to 3 days ago to avoid empty recent dates
        today = datetime.utcnow().date()
        end_date = today - timedelta(days=3)
        start_date = end_date - timedelta(days=days)
        
        # Ensure we don't go beyond the 180-day limit of the API (approx 6 months)
        max_history = today - timedelta(days=179)
        if start_date < max_history:
            start_date = max_history
        
        # List of metrics to fetch one by one (since we're using the single GET endpoint)
        metrics = [
            'BUSINESS_IMPRESSIONS_DESKTOP_MAPS',
            'BUSINESS_IMPRESSIONS_DESKTOP_SEARCH',
            'BUSINESS_IMPRESSIONS_MOBILE_MAPS',
            'BUSINESS_IMPRESSIONS_MOBILE_SEARCH',
            'CALL_CLICKS',
            'WEBSITE_CLICKS',
            'BUSINESS_DIRECTION_REQUESTS'
        ]
        
        results = []
        headers = self._get_headers()
        
        for metric in metrics:
            params = {
                'dailyMetric': metric,
                'dailyRange.startDate.year': start_date.year,
                'dailyRange.startDate.month': start_date.month,
                'dailyRange.startDate.day': start_date.day,
                'dailyRange.endDate.year': end_date.year,
                'dailyRange.endDate.month': end_date.month,
                'dailyRange.endDate.day': end_date.day
            }
            
            try:
                response = requests.get(base_url, headers=headers, params=params, timeout=20)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"GMB API Response for {metric}: {data}")
                    time_series = data.get('timeSeries', {}).get('datedValues', [])
                    
                    for point in time_series:
                        date_data = point.get('date', {})
                        val = int(point.get('value', 0))
                        
                        results.append({
                            'metric': metric,
                            'date': f"{date_data.get('year')}-{date_data.get('month'):02d}-{date_data.get('day'):02d}",
                            'value': val
                        })
                elif response.status_code == 404:
                    # Log but continue if one metric is missing
                    logger.warning(f"Metric {metric} not found (404) for location {location_id}")
                else:
                    logger.warning(f"Error fetching metric {metric}: {response.status_code} - {response.text}")
                    
            except Exception as e:
                logger.error(f"Failed to fetch metric {metric}: {e}")
                
        return results


    def test_performance_api(self, location_name: str) -> Dict:
        """Diagnostic tool to test if Performance API is working for this connection"""
        try:
            # Try to fetch 180 days of data (maximum) to be absolutely sure
            results = self.fetch_insights(location_name, days=180)
            count = len(results)
            return {
                'success': True, 
                'message': f'API de Performance funcionando! Encontrados {count} pontos de dados nos últimos 180 dias.'
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}


    def sync_insights_to_cache(self, location_link_id: int, days: int = 90) -> int:
        """
        Fetch insights from Google and sync to GMBInsight table.
        """
        import traceback
        from app.models.ranking import GMBInsight
        from app.models.gmb_location_link import GMBLocationLink
        
        try:
            with get_db() as db:
                link = db.query(GMBLocationLink).get(location_link_id)
                if not link:
                    logger.error(f"Link {location_link_id} not found.")
                    return 0
                    
                insights_data = self.fetch_insights(link.gmb_location_name, days=days)
                if not insights_data:
                    logger.warning(f"No insights data returned for {link.gmb_location_name}")
                    return 0
                    
                synced_count = 0
                for item in insights_data:
                    # Map Google metric names to our internal names
                    # Simplified categories for dashboard
                    metric_cat = 'impressions'
                    if 'IMPRESSIONS' in item['metric']:
                        metric_cat = 'impressions'
                    elif 'CALL' in item['metric']:
                        metric_cat = 'calls'
                    elif 'WEBSITE' in item['metric']:
                        metric_cat = 'website_clicks'
                    elif 'DIRECTION' in item['metric']:
                        metric_cat = 'directions'
                    
                    item_date = datetime.strptime(item['date'], '%Y-%m-%d')
                    
                    # Check for existing record for this link/date/metric
                    existing = db.query(GMBInsight).filter(
                        GMBInsight.location_link_id == location_link_id,
                        GMBInsight.date == item_date,
                        GMBInsight.metric == item['metric']
                    ).first()
                    
                    if existing:
                        existing.value = item['value']
                        existing.synced_at = datetime.utcnow()
                    else:
                        insight = GMBInsight(
                            location_link_id=location_link_id,
                            date=item_date,
                            metric=item['metric'],
                            value=item['value']
                        )
                        db.add(insight)
                    
                    synced_count += 1
                
                db.commit()
                logger.info(f"Successfully synced {synced_count} insights for link {location_link_id}")
                return synced_count
            
        except Exception as e:
            logger.exception(f"Sync insights failed: {str(e)}")
            return 0


def get_service_for_connection(connection_id: int) -> GoogleBusinessService:
    """Factory function to create a GoogleBusinessService for a connection"""
    with get_db() as db:
        connection = db.query(GoogleConnection).get(connection_id)
        if not connection or not connection.is_active:
            raise ValueError("Connection not found or inactive")
        return GoogleBusinessService(connection)


def get_service_for_client(client_id: int, location_link_id: Optional[int] = None) -> Optional[GoogleBusinessService]:
    """Get a GoogleBusinessService for a client's specific or primary GMB location"""
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
            # If no primary, grab the first one
            if not link:
                link = db.query(GMBLocationLink).filter(
                    GMBLocationLink.client_id == client_id
                ).first()
        
        if not link:
            return None
        
        connection = db.query(GoogleConnection).get(link.google_connection_id)
        if not connection or not connection.is_active:
            return None
        
        return GoogleBusinessService(connection)
