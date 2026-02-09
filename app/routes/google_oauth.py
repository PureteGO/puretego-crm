"""
PURETEGO CRM - Google OAuth Routes
OAuth flow for connecting Google Business Profile accounts
# Force update to fix circular imports and trigger CI/CD
"""

import os
import json
import secrets
from datetime import datetime, timedelta
from flask import Blueprint, request, redirect, url_for, flash, session, current_app, render_template
from flask_babel import _
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
import google.auth.transport.requests

from app.routes.auth import login_required
from app.models import GoogleConnection
from config.database import get_db

bp = Blueprint('google_oauth', __name__, url_prefix='/integrations/google')

# OAuth configuration
# OAuth configuration
SCOPES = [
    'https://www.googleapis.com/auth/business.manage',
    'https://www.googleapis.com/auth/userinfo.email',
    'openid'
]

def get_client_config():
    """Get OAuth client configuration from environment"""
    return {
        "web": {
            "client_id": os.environ.get('GOOGLE_CLIENT_ID', '722401847261-lfoe4j55kibqtt2e1r2ruv6qucens07b.apps.googleusercontent.com'),
            "client_secret": os.environ.get('GOOGLE_CLIENT_SECRET', ''),
            "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [get_redirect_uri()]
        }
    }

def get_redirect_uri():
    """Get the redirect URI - auto-detect local vs production environment"""
    # Check if explicitly set in environment
    explicit_uri = os.environ.get('GOOGLE_REDIRECT_URI')
    if explicit_uri:
        return explicit_uri
    
    # Auto-detect based on FLASK_ENV or ENVIRONMENT variable
    env = os.environ.get('FLASK_ENV', os.environ.get('ENVIRONMENT', 'development'))
    
    if env == 'production':
        return 'https://app2.maps2go.online/integrations/google/callback'
    else:
        # Local development - use dynamic URL if in request context
        try:
            # This ensures the redirect URI matches the host used by the user (localhost vs 127.0.0.1 vs LAN IP)
            return url_for('google_oauth.callback', _external=True)
        except RuntimeError:
            # Fallback if called outside request context
            return 'http://localhost:5000/integrations/google/callback'


@bp.route('/')
@login_required
def dashboard():
    """Google integrations dashboard - list connected accounts"""
    company_id = session.get('company_id')
    
    # Check if GBP integration is enabled
    gbp_enabled = os.environ.get('GBP_INTEGRATION_ENABLED', 'True').lower() == 'true'
    all_locations = []

    with get_db() as db:
        connections = db.query(GoogleConnection).filter(
            GoogleConnection.company_id == company_id,
            GoogleConnection.is_active == True
        ).all()
        
        # Calculate stats for each connection
        connections_data = []
        for conn in connections:
            connections_data.append({
                'id': conn.id,
                'email': conn.google_account_email or _('Cuenta desconocida'),
                'locations_count': len(conn.location_links) if conn.location_links else 0,
                'is_expired': conn.is_token_expired(),
                'created_at': conn.created_at,
                'last_error': conn.last_error
            })

        # Fetch locations for all active connections
        if gbp_enabled:
            from app.services.google_business_service import GoogleBusinessService
            from app.models import GMBLocationLink
            
            # Get all existing links for this company to check status
            existing_links = {
                link.gmb_location_name: link
                for link in db.query(GMBLocationLink).filter(
                    GMBLocationLink.company_id == company_id
                ).all()
            }
            
            for conn in connections:
                # Re-check expiry inside loop/session just in case, though is_token_expired is safer here
                if not conn.is_token_expired():
                    try:
                        service = GoogleBusinessService(conn)
                        accounts = service.list_accounts()
                        
                        for account in accounts:
                            try:
                                # Fetch locations for this account
                                locations = service.list_locations(account['name'])
                                
                                for loc in locations:
                                    is_linked = loc['name'] in existing_links
                                    linked_client_name = None
                                    link_id = None
                                    
                                    if is_linked:
                                        link = existing_links[loc['name']]
                                        linked_client_name = link.client.name if link.client else _('Cliente eliminado')
                                        link_id = link.id
                                    
                                    all_locations.append({
                                        'connection_id': conn.id,
                                        'connection_email': conn.google_account_email,
                                        'account_name': account['accountName'],
                                        'name': loc['name'],
                                        'title': loc['title'],
                                        'address': loc.get('address', ''),
                                        'city': loc.get('city', ''),
                                        'is_linked': is_linked,
                                        'linked_client_name': linked_client_name,
                                        'link_id': link_id,
                                        # Manage URL handles auto-linking
                                        'manage_url': url_for('google_oauth.manage_location', connection_id=conn.id, location_name=loc['name']),
                                        'link_url': url_for('google_oauth.locations', connection_id=conn.id)
                                    })
                            except Exception as e:
                                current_app.logger.warning(f"Error fetching locations for account {account['name']}: {e}")
                                
                        # Don't fail the whole page, just log
                                
                    except Exception as e:
                        current_app.logger.error(f"Error fetching data for connection {conn.id}: {e}")
                        # Update connection error
                        conn.last_error = str(e)
                        db.commit()
    
    return render_template('integrations/google_dashboard.html',
                           connections=connections_data,
                           gbp_enabled=gbp_enabled,
                           all_locations=all_locations)


@bp.route('/locations/<int:connection_id>')
@login_required
def locations(connection_id):
    """View and manage locations for a Google connection"""
    company_id = session.get('company_id')
    
    # Check basic permission - Allow superadmin or direct DB check fallback
    is_superadmin = session.get('is_superadmin', False)
    permissions = session.get('permissions') or {}
    has_permission = permissions.get('can_manage_gmb', False)
    
    if not is_superadmin and not has_permission:
        # Final fallback: check DB in case session is stale
        from app.utils.decorators import get_current_user
        user = get_current_user()
        if not user or not user.has_permission('can_manage_gmb'):
            flash(_('Você não tem permissão para gerenciar integrações Google.'), 'error')
            return redirect(url_for('dashboard.index'))

    try:
        with get_db() as db:
            connection = db.query(GoogleConnection).filter(
                GoogleConnection.id == connection_id,
                GoogleConnection.company_id == company_id
            ).first()
            
            if not connection:
                flash(_('Conexão não encontrada.'), 'error')
                return redirect(url_for('google_oauth.dashboard'))
            
            # Get already linked locations
            linked_locations = {}
            if connection.location_links:
                linked_locations = {
                    link.gmb_location_name: link 
                    for link in connection.location_links
                    if link.gmb_location_name
                }
        
        # Get clients for dropdown
        from app.models import Client
        from app.utils.decorators import get_current_user
        user = get_current_user()
        
        query = db.query(Client).filter(
            Client.company_id == company_id,
            Client.is_active == True
        )
        
        # RBAC Filtering
        if user and user.role:
            role_name = getattr(user.role, 'name', None)
            can_edit_all = getattr(user.role, 'can_edit_all_clients', False)
            if role_name == 'gmb_manager' and not can_edit_all:
                query = query.filter(Client.owner_id == user.id)
            
        clients = query.order_by(Client.name).all()
        
        # Fetch locations from Google API
        locations_data = []
        error_message = None
        
        try:
            from app.services.google_business_service import GoogleBusinessService
            service = GoogleBusinessService(connection)
            
            # List accounts first
            accounts = service.list_accounts()
            
            # For each account, get locations
            for account in accounts:
                try:
                    account_locations = service.list_locations(account['name'])
                    for loc in account_locations:
                        loc['account_name'] = account['accountName']
                        loc['is_linked'] = loc['name'] in linked_locations
                        loc['linked_client_id'] = None
                        loc['linked_client_name'] = None
                        loc['link_id'] = None
                        
                        if loc['is_linked']:
                            link = linked_locations[loc['name']]
                            loc['linked_client_id'] = link.client_id
                            loc['linked_client_name'] = link.client.name if link.client else None
                            loc['link_id'] = link.id
                        locations_data.append(loc)
                except Exception as e:
                    current_app.logger.warning(f"Error fetching locations for {account['name']}: {e}")
                    
        except Exception as e:
            error_message = str(e)
            current_app.logger.error(f"Error fetching Google locations: {e}")
    
        return render_template('integrations/location_mapping.html',
                               connection=connection,
                               locations=locations_data,
                               clients=clients,
                               error_message=error_message)
    except Exception as e:
        import traceback
        error_details = f"{str(e)}\n{traceback.format_exc()}"
        current_app.logger.error(f"FATAL ERROR in google_oauth.locations: {error_details}")
        # Show specific error for debugging on production
        flash(_('Erro ao carregar locais: %(error)s', error=str(e)), 'error')
        return redirect(url_for('google_oauth.dashboard'))


@bp.route('/repair-permissions')
@login_required
def repair_permissions():
    """Utility route to fix missing GMB permissions for Owner and Manager roles in DB"""
    from config.database import db_session
    from app.models import Role, User
    
    # Update ALL roles of type owner and manager to have GMB permissions
    roles_to_fix = db_session.query(Role).filter(Role.name.in_(['owner', 'manager'])).all()
    for role in roles_to_fix:
        role.can_manage_gmb = True
        role.can_manage_healthchecks = True
    
    db_session.commit()
    
    # Force session refresh of permissions for the current user
    user_id = session.get('user_id')
    user = db_session.query(User).filter(User.id == user_id).first()
    
    if user and user.role:
        # Refresh the relationship to ensure we have updated role data
        db_session.refresh(user.role)
        session['permissions'] = user.role.get_permissions_dict()
        session['role'] = user.role.name
        # Clear g.current_user to force decorators to reload it next time
        from flask import g
        if hasattr(g, 'current_user'):
            g.current_user = None
            
    flash(_('Permissões de GMB restauradas para Proprietários e Gerentes. Sua sessão foi atualizada.'), 'success')
    return redirect(url_for('dashboard.index'))


@bp.route('/connect')
@login_required  
def connect():
    """Initiate OAuth flow to connect a new Google account"""
    
    # Check if feature is enabled
    if os.environ.get('GBP_INTEGRATION_ENABLED', 'True').lower() != 'true':
        flash(_('La integración con Google Business Profile está deshabilitada.'), 'warning')
        return redirect(url_for('google_oauth.dashboard'))
    
    # Check for client secret
    if not os.environ.get('GOOGLE_CLIENT_SECRET'):
        flash(_('Error de configuración: Falta el Client Secret de Google.'), 'error')
        return redirect(url_for('google_oauth.dashboard'))
    
    company_id = session.get('company_id')
    
    # Create OAuth flow
    flow = Flow.from_client_config(
        get_client_config(),
        scopes=SCOPES,
        redirect_uri=get_redirect_uri()
    )
    
    # Create state token with company_id for callback
    state_data = {
        'company_id': company_id,
        'csrf_token': secrets.token_urlsafe(32)
    }
    state = json.dumps(state_data)
    
    # Store CSRF token in session for validation
    session['oauth_csrf'] = state_data['csrf_token']
    
    # Generate authorization URL
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent',
        state=state
    )
    
    return redirect(authorization_url)


@bp.route('/callback')
def callback():
    """Handle OAuth callback from Google"""
    
    # Get authorization code and state
    code = request.args.get('code')
    state_str = request.args.get('state')
    error = request.args.get('error')

    if error:
        flash(_('Error de autorización de Google: %(error)s', error=error), 'error')
        return redirect(url_for('google_oauth.dashboard'))
    
    if not code or not state_str:
        flash(_('Respuesta OAuth inválida.'), 'error')
        return redirect(url_for('google_oauth.dashboard'))
    
    try:
        # Parse state
        state_data = json.loads(state_str)
        company_id = state_data.get('company_id')
        csrf_token = state_data.get('csrf_token')
        
        # Validate CSRF token
        if csrf_token != session.get('oauth_csrf'):
            flash(_('Token de seguridad inválido. Intente nuevamente.'), 'error')
            return redirect(url_for('google_oauth.dashboard'))
        
        # Clear CSRF token
        session.pop('oauth_csrf', None)
        
        # Exchange code for tokens
        flow = Flow.from_client_config(
            get_client_config(),
            scopes=SCOPES,
            redirect_uri=get_redirect_uri()
        )
        
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Get user info to identify the account
        google_email = _get_google_email(credentials)
        
        # Calculate expiry time
        expires_at = datetime.utcnow() + timedelta(seconds=3600)
        if credentials.expiry:
            expires_at = credentials.expiry
        
        with get_db() as db:
            # Check if this Google account is already connected for this company
            existing = db.query(GoogleConnection).filter(
                GoogleConnection.company_id == company_id,
                GoogleConnection.google_account_email == google_email
            ).first()
            
            if existing:
                # Update existing connection
                existing.set_access_token(credentials.token)
                if credentials.refresh_token:
                    existing.set_refresh_token(credentials.refresh_token)
                existing.expires_at = expires_at
                existing.scopes = ' '.join(SCOPES)
                existing.is_active = True
                existing.last_error = None
                
                flash(_('Cuenta Google %(email)s reconectada exitosamente.', email=google_email), 'success')
            else:
                # Create new connection
                connection = GoogleConnection(
                    company_id=company_id,
                    google_account_email=google_email,
                    access_token='',  # Will be encrypted below
                    expires_at=expires_at,
                    scopes=' '.join(SCOPES)
                )
                connection.set_access_token(credentials.token)
                if credentials.refresh_token:
                    connection.set_refresh_token(credentials.refresh_token)
                
                db.add(connection)
                flash(_('Cuenta Google %(email)s conectada exitosamente.', email=google_email), 'success')
            
            db.commit()
        
        return redirect(url_for('google_oauth.dashboard'))
        
    except Exception as e:
        current_app.logger.error(f"OAuth callback error: {str(e)}")
        flash(_('Error al procesar la autorización: %(error)s', error=str(e)), 'error')
        return redirect(url_for('google_oauth.dashboard'))


@bp.route('/disconnect/<int:connection_id>', methods=['POST'])
@login_required
def disconnect(connection_id):
    """Disconnect a Google account"""
    company_id = session.get('company_id')
    
    with get_db() as db:
        connection = db.query(GoogleConnection).filter(
            GoogleConnection.id == connection_id,
            GoogleConnection.company_id == company_id
        ).first()
        
        if connection:
            email = connection.google_account_email
            connection.is_active = False
            db.commit()
            flash(_('Cuenta %(email)s desconectada.', email=email), 'info')
        else:
            flash(_('Conexión no encontrada.'), 'error')
    
    return redirect(url_for('google_oauth.dashboard'))


def _get_google_email(credentials):
    """Get the email address of the authenticated Google user"""
    try:
        import requests
        response = requests.get(
            'https://www.googleapis.com/oauth2/v3/userinfo',
            headers={'Authorization': f'Bearer {credentials.token}'}
        )
        if response.status_code == 200:
            user_info = response.json()
            return user_info.get('email', 'unknown@google.com')
    except Exception:
        pass
    return 'unknown@google.com'


def refresh_connection_token(connection_id):
    """Refresh the access token for a connection (used by cron job)"""
    with get_db() as db:
        connection = db.query(GoogleConnection).get(connection_id)
        
        if not connection or not connection.is_active:
            return False
        
        refresh_token = connection.get_refresh_token()
        if not refresh_token:
            connection.last_error = "No refresh token available"
            db.commit()
            return False
        
        try:
            # Create credentials with refresh token
            creds = Credentials(
                token=connection.get_access_token(),
                refresh_token=refresh_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=os.environ.get('GOOGLE_CLIENT_ID'),
                client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
                scopes=SCOPES
            )
            
            # Refresh the token
            request_obj = google.auth.transport.requests.Request()
            creds.refresh(request_obj)
            
            # Update stored tokens
            connection.set_access_token(creds.token)
            connection.expires_at = creds.expiry or (datetime.utcnow() + timedelta(hours=1))
            connection.last_error = None
            
            db.commit()
            return True
            
        except Exception as e:
            connection.last_error = str(e)
            db.commit()
            return False




@bp.route('/api/locations/<int:connection_id>')
@login_required
def api_locations(connection_id):
    """API: List locations for a connection as JSON"""
    company_id = session.get('company_id')
    from app.services.google_business_service import GoogleBusinessService
    
    with get_db() as db:
        connection = db.query(GoogleConnection).filter(
            GoogleConnection.id == connection_id,
            GoogleConnection.company_id == company_id,
            GoogleConnection.is_active == True
        ).first()
        
        if not connection:
            return jsonify({'success': False, 'message': 'Conexão não encontrada'}), 404
            
        try:
            service = GoogleBusinessService(connection)
            accounts = service.list_accounts()
            
            all_locations = []
            for account in accounts:
                locs = service.list_locations(account['name'])
                for l in locs:
                    all_locations.append({
                        'name': l['name'],
                        'title': l['title'],
                        'address': l.get('storefrontAddress', {}).get('addressLines', [''])[0]
                    })
            
            return jsonify({'success': True, 'locations': all_locations})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/locations/<int:connection_id>/link', methods=['POST'])
@login_required
def link_location(connection_id):
    """Link a Google location to a CRM client"""
    company_id = session.get('company_id')
    
    location_name = request.form.get('location_name')
    location_title = request.form.get('location_title')
    location_address = request.form.get('location_address')
    client_id = request.form.get('client_id')
    
    if not location_name or not client_id:
        flash(_('Datos incompletos.'), 'error')
        return redirect(url_for('google_oauth.locations', connection_id=connection_id))
    
    with get_db() as db:
        # Verify connection belongs to company
        connection = db.query(GoogleConnection).filter(
            GoogleConnection.id == connection_id,
            GoogleConnection.company_id == company_id
        ).first()
        
        if not connection:
            flash(_('Conexión no encontrada.'), 'error')
            return redirect(url_for('google_oauth.dashboard'))

        client = db.query(Client).get(int(client_id))
        user = get_current_user()
        if not client or not user.can_manage_gmb_for(client):
            flash(_('Você não tem permissão para vincular este cliente.'), 'error')
            return redirect(url_for('google_oauth.locations', connection_id=connection_id))

        # Check if link already exists
        from app.models import GMBLocationLink
        existing = db.query(GMBLocationLink).filter(
            GMBLocationLink.gmb_location_name == location_name
        ).first()
        
        if existing:
            # Update existing link
            existing.client_id = int(client_id)
            existing.gmb_location_title = location_title
            existing.gmb_location_address = location_address
            flash(_('Vínculo actualizado.'), 'success')
        else:
            # Create new link
            link = GMBLocationLink(
                company_id=company_id,
                google_connection_id=connection_id,
                client_id=int(client_id),
                gmb_location_name=location_name,
                gmb_location_title=location_title,
                gmb_location_address=location_address,
                is_primary=True
            )
            db.add(link)
            flash(_('Perfil vinculado exitosamente.'), 'success')
        
        db.commit()
    
    return redirect(url_for('google_oauth.locations', connection_id=connection_id))


@bp.route('/locations/<int:connection_id>/unlink/<int:link_id>', methods=['POST'])
@login_required
def unlink_location(connection_id, link_id):
    """Remove a location-client link"""
    company_id = session.get('company_id')
    
    with get_db() as db:
        from app.models import GMBLocationLink
        link = db.query(GMBLocationLink).filter(
            GMBLocationLink.id == link_id,
            GMBLocationLink.company_id == company_id,
            GMBLocationLink.google_connection_id == connection_id
        ).first()
        
        if link:
            # RBAC Check: GMB Manager can only unlink for clients they own
            from app.utils.decorators import get_current_user
            user = get_current_user()
            if link.client and not user.can_manage_gmb_for(link.client):
                flash(_('Você não tem permissão para remover este vínculo.'), 'error')
                return redirect(url_for('google_oauth.locations', connection_id=connection_id))

            db.delete(link)
            db.commit()
            flash(_('Vínculo eliminado.'), 'info')
        else:
            flash(_('Vínculo no encontrado.'), 'error')
    
    return redirect(url_for('google_oauth.locations', connection_id=connection_id))


@bp.route('/manage/<int:connection_id>/<path:location_name>')
@login_required
def manage_location(connection_id, location_name):
    """Manage a specific Google Business Profile Location"""
    company_id = session.get('company_id')
    
    with get_db() as db:
        # Verify connection
        connection = db.query(GoogleConnection).filter(
            GoogleConnection.id == connection_id,
            GoogleConnection.company_id == company_id,
            GoogleConnection.is_active == True
        ).first()
        
        if not connection:
            flash(_('Conexión no encontrada o inactiva.'), 'error')
            return redirect(url_for('google_oauth.dashboard'))

        # Check existing link or create new one (Managed Only)
        from app.models import GMBLocationLink
        link = db.query(GMBLocationLink).filter(
            GMBLocationLink.gmb_location_name == location_name,
            GMBLocationLink.company_id == company_id
        ).first()
        
        # We need to fetch details to save title/address if creating content
        from app.services.google_business_service import GoogleBusinessService
        service = GoogleBusinessService(connection)
        
        try:
            # 1. Get Location Details (Full info + Summary for ratings)
            location_details = service.get_location_details(location_name)
            
            # Debug log the URLs
            current_app.logger.info(f"Fetching summary/reviews for: {location_name}")
            
            summary_v4 = service.get_location_summary_v4(location_name)
            
            # 2. Get Reviews (Soft fail if API not enabled or access denied)
            reviews = []
            review_error = None
            try:
                reviews = service.list_reviews(location_name)
            except Exception as e:
                review_error = str(e)
                current_app.logger.warning(f"Failed to fetch reviews for {location_name}: {e}")

            # Merge summary data
            location_details['averageRating'] = summary_v4.get('averageRating', 0)
            location_details['totalReviewCount'] = summary_v4.get('totalReviewCount', 0)

            # Fallback Rating Calculation: if summary is 0 but we have reviews, calculate local avg
            if (not location_details['averageRating'] or location_details['averageRating'] == 0) and reviews:
                total_stars = sum([r.get('starRating', 0) for r in reviews])
                location_details['averageRating'] = round(total_stars / len(reviews), 1)
                if not location_details['totalReviewCount']:
                    location_details['totalReviewCount'] = len(reviews)
            
            return render_template('integrations/manage_location.html',
                                   connection=connection,
                                   location=location_details,
                                   link=link,
                                   reviews=reviews,
                                   review_error=review_error,
                                   debug_location=location_name)
                                   
        except Exception as e:
            current_app.logger.error(f"Error managing location {location_name}: {e}")
            flash(_('Error al obtener datos de Google: %(error)s', error=str(e)), 'error')
            return redirect(url_for('google_oauth.dashboard'))

@bp.route('/manage/review/reply', methods=['POST'])
@login_required
def review_reply():
    try:
        connection_id = request.form.get('connection_id')
        review_name = request.form.get('review_name')
        comment = request.form.get('comment')
        
        if not all([connection_id, review_name, comment]):
            flash(_('Dados incompletos para a resposta.'), 'error')
            return redirect(request.referrer or url_for('google_oauth.dashboard'))
            
        from app.utils.decorators import get_current_user
        user = get_current_user()
        
        with get_db() as db:
            connection = db.query(GoogleConnection).filter(
                GoogleConnection.id == int(connection_id),
                GoogleConnection.company_id == user.company_id
            ).first()
            
            if not connection:
                flash(_('Conexão não encontrada.'), 'error')
                return redirect(url_for('google_oauth.dashboard'))
                
            from app.services.google_business_service import GoogleBusinessService
            service = GoogleBusinessService(connection)
            service.update_review_reply(review_name, comment)
            
        flash(_('Resposta enviada com sucesso!'), 'success')
        
    except Exception as e:
        current_app.logger.error(f"Error replying to review: {e}")
        flash(_('Erro ao enviar resposta: ') + str(e), 'error')
        
    return redirect(request.referrer or url_for('google_oauth.dashboard'))

@bp.route('/insights/sync/<int:connection_id>/<int:link_id>', methods=['POST'])
@login_required
def sync_insights(connection_id, link_id):
    """Route to manually sync GMB Insights for a client."""
    from app.services.google_business_service import get_service_for_connection
    company_id = session.get('company_id')
    
    with get_db() as db:
        connection = db.query(GoogleConnection).filter(
            GoogleConnection.id == connection_id,
            GoogleConnection.company_id == company_id
        ).first()
        
        link = db.query(GMBLocationLink).filter(
            GMBLocationLink.id == link_id,
            GMBLocationLink.company_id == company_id
        ).first()
        
        if not connection or not link:
            flash(_('Conexão ou Perfil não encontrado.'), 'error')
            return redirect(request.referrer or url_for('clients.index'))
            
        try:
            service = get_service_for_connection(connection_id)
            # Sync last 30 days
            count = service.sync_insights_to_cache(link_id, days=30)
            flash(_('Métricas sincronizadas com sucesso: %(count)s registros.', count=count), 'success')
        except Exception as e:
            flash(_('Erro ao sincronizar métricas: %(error)s', error=str(e)), 'error')
            
    return redirect(request.referrer or url_for('clients.view', client_id=link.client_id))
