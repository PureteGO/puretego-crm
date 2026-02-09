"""
PURETEGO CRM - Google Business Service
Service class for Google Business Profile API operations
"""

import os
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from google.oauth2.credentials import Credentials
import google.auth.transport.requests

from app.models import GoogleConnection, GMBLocationLink, GMBReview, GMBInsight
from config.database import get_db


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
        params = {
            'pageSize': min(page_size, 50)
        }
        
        try:
            response = requests.get(url, headers=self._get_headers(), params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            reviews = data.get('reviews', [])
            
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
        
        Args:
            location_link_id: ID of the GMBLocationLink
            
        Returns:
            Number of reviews synced
        """
        with get_db() as db:
            link = db.query(GMBLocationLink).get(location_link_id)
            if not link:
                raise ValueError("Location link not found")
            
            try:
                reviews = self.list_reviews(link.gmb_location_name)
                synced_count = 0
                
                for review_data in reviews:
                    # Check if review already exists
                    existing = db.query(GMBReview).filter(
                        GMBReview.google_review_id == review_data['name']
                    ).first()
                    
                    if existing:
                        # Update existing
                        existing.star_rating = review_data['starRating']
                        existing.comment = review_data['comment']
                        existing.reply_text = review_data['replyComment']
                        existing.synced_at = datetime.utcnow()
                    else:
                        # Create new
                        review = GMBReview(
                            location_link_id=location_link_id,
                            google_review_id=review_data['name'],
                            reviewer_name=review_data['reviewerName'],
                            reviewer_photo_url=review_data['reviewerPhotoUrl'],
                            star_rating=review_data['starRating'],
                            comment=review_data['comment'],
                            review_date=datetime.fromisoformat(
                                review_data['createTime'].replace('Z', '+00:00')
                            ) if review_data['createTime'] else datetime.utcnow(),
                            reply_text=review_data['replyComment'],
                            reply_date=datetime.fromisoformat(
                                review_data['replyTime'].replace('Z', '+00:00')
                            ) if review_data['replyTime'] else None
                        )
                        db.add(review)
                        synced_count += 1
                
                # Update sync timestamp
                link.last_sync_at = datetime.utcnow()
                link.sync_error = None
                db.commit()
                
                return synced_count
                
            except Exception as e:
                link.sync_error = str(e)[:500]
                db.commit()
                raise

    def fetch_insights(self, location_name: str, days: int = 30) -> List[Dict]:
        """
        Fetch performance insights for a location using the GMB Performance API.
        
        Args:
            location_name: Full location name (accounts/X/locations/Y)
            days: Number of days of history to fetch (max 90)
        """
        # The Performance API uses a specific endpoint for daily metrics
        # GET https://businessprofileperformance.googleapis.com/v1/{name}/fetchMultiDailyMetricsTimeSeries
        url = f"https://businessprofileperformance.googleapis.com/v1/{location_name}:fetchMultiDailyMetricsTimeSeries"
        
        # Calculate time range
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        params = {
            'dailyMetrics': [
                'BUSINESS_IMPRESSIONS_DESKTOP_MAPS',
                'BUSINESS_IMPRESSIONS_DESKTOP_SEARCH',
                'BUSINESS_IMPRESSIONS_MOBILE_MAPS',
                'BUSINESS_IMPRESSIONS_MOBILE_SEARCH',
                'CALL_CLICKS',
                'WEBSITE_CLICKS',
                'BUSINESS_DIRECTION_REQUESTS'
            ],
            'dailyRange.startDate.year': start_date.year,
            'dailyRange.startDate.month': start_date.month,
            'dailyRange.startDate.day': start_date.day,
            'dailyRange.endDate.year': end_date.year,
            'dailyRange.endDate.month': end_date.month,
            'dailyRange.endDate.day': end_date.day
        }
        
        try:
            response = requests.get(url, headers=self._get_headers(), params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            time_series_list = data.get('multiDailyMetricTimeSeries', [])
            
            # Reformat data for easier storage
            # The API returns a list of TimeSeries, one per metric
            results = []
            for ts in time_series_list:
                metric_name = ts.get('dailyMetric', '')
                time_series = ts.get('dailyMetricTimeSeries', {}).get('timeSeries', [])
                
                for point in time_series:
                    date_data = point.get('date', {})
                    val = int(point.get('value', 0))
                    
                    results.append({
                        'metric': metric_name,
                        'date': f"{date_data.get('year')}-{date_data.get('month'):02d}-{date_data.get('day'):02d}",
                        'value': val
                    })
            
            return results
            
        except Exception as e:
            print(f"Error fetching GMB performance data: {str(e)}")
            return []

    def sync_insights_to_cache(self, location_link_id: int, days: int = 30) -> int:
        """
        Fetch insights from Google and sync to GMBInsight table.
        """
        with get_db() as db:
            link = db.query(GMBLocationLink).get(location_link_id)
            if not link:
                return 0
                
            insights_data = self.fetch_insights(link.gmb_location_name, days=days)
            if not insights_data:
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
            return synced_count


def get_service_for_connection(connection_id: int) -> GoogleBusinessService:
    """Factory function to create a GoogleBusinessService for a connection"""
    with get_db() as db:
        connection = db.query(GoogleConnection).get(connection_id)
        if not connection or not connection.is_active:
            raise ValueError("Connection not found or inactive")
        return GoogleBusinessService(connection)


def get_service_for_client(client_id: int) -> Optional[GoogleBusinessService]:
    """Get a GoogleBusinessService for a client's primary GMB location"""
    with get_db() as db:
        link = db.query(GMBLocationLink).filter(
            GMBLocationLink.client_id == client_id,
            GMBLocationLink.is_primary == True
        ).first()
        
        if not link:
            return None
        
        connection = db.query(GoogleConnection).get(link.google_connection_id)
        if not connection or not connection.is_active:
            return None
        
        return GoogleBusinessService(connection)
