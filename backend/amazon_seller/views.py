from django.shortcuts import render

# Create your views here.

"""
API views for Amazon Seller OAuth flow
"""
import logging
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views import View

from .models import AmazonSellerAccount
from .services.auth import AmazonAuthService

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class AmazonAuthView(View):
    """View to initiate Amazon Seller OAuth flow"""
    
    def get(self, request):
        """Generate an authorization URL for Amazon Seller Central"""
        region = request.GET.get('region', 'EU')  # Default to EU
        
        try:
            auth_url, state = AmazonAuthService.get_authorization_url(region=region)
            
            # Store state in session for CSRF protection
            request.session['amazon_oauth_state'] = state
            
            return JsonResponse({
                'authorization_url': auth_url,
                'state': state
            })
        except Exception as e:
            logger.error(f"Error generating authorization URL: {str(e)}")
            return JsonResponse({
                'error': f"Failed to generate authorization URL: {str(e)}"
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class AmazonAdvertisingAuthView(View):
    """View to initiate Amazon Advertising API OAuth flow"""
    
    def get(self, request):
        """Generate an authorization URL for Amazon Advertising API"""
        region = request.GET.get('region', 'EU')  # Default to EU for Advertising
        
        # Get scopes from query params or use default
        scopes = request.GET.get('scopes', 'advertising::campaign_management')
        scopes_list = scopes.split(',')
        
        try:
            auth_url, state = AmazonAuthService.get_advertising_authorization_url(
                region=region,
                scopes=scopes_list
            )
            
            # Store state in session for CSRF protection
            request.session['amazon_adv_oauth_state'] = state
            
            return JsonResponse({
                'authorization_url': auth_url,
                'state': state
            })
        except Exception as e:
            logger.error(f"Error generating Advertising authorization URL: {str(e)}")
            return JsonResponse({
                'error': f"Failed to generate Advertising authorization URL: {str(e)}"
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class AmazonCallbackView(View):
    """View to handle OAuth callback from Amazon"""
    
    def get(self, request):
        """Handle the callback from Amazon with the authorization code"""
        # Get parameters from request
        auth_code = request.GET.get('spapi_oauth_code')
        seller_id = request.GET.get('selling_partner_id')
        state = request.GET.get('state')
        
        # Validate parameters
        if not auth_code or not seller_id:
            logger.error("Missing required parameters in callback")
            return JsonResponse({
                'error': 'Missing required parameters: auth code or seller ID'
            }, status=400)
        
        # Validate state for CSRF protection (if you implemented it)
        session_state = request.session.get('amazon_oauth_state')
        if session_state and state != session_state:
            logger.error(f"State mismatch: {state} vs {session_state}")
            return JsonResponse({
                'error': 'State parameter mismatch. Possible CSRF attack.'
            }, status=400)
        
        try:
            # Exchange code for tokens
            region = request.GET.get('region', 'EU')
            token_data = AmazonAuthService.exchange_code_for_tokens(auth_code, region=region)
            
            # Create or update the seller account
            seller_account, created = AmazonSellerAccount.objects.update_or_create(
                seller_id=seller_id,
                defaults={
                    'auth_code': auth_code,
                    'access_token': token_data['access_token'],
                    'refresh_token': token_data['refresh_token'],
                    'token_type': token_data['token_type'],
                    'token_expires_at': token_data['token_expires_at'],
                    'region': region,
                    'is_active': True
                }
            )
            
            logger.info(f"{'Created' if created else 'Updated'} Amazon seller account: {seller_id}")
            
            # Clear the state from session
            if 'amazon_oauth_state' in request.session:
                del request.session['amazon_oauth_state']
            
            # Redirect to frontend success page
            if hasattr(settings, 'FRONTEND_URL'):
                redirect_url = f"{settings.FRONTEND_URL}/amazon/success?seller_id={seller_id}"
                return HttpResponseRedirect(redirect_url)
            else:
                # If no frontend URL is configured, return JSON response
                return JsonResponse({
                    'success': True,
                    'message': f"Successfully authenticated seller: {seller_id}",
                    'seller_id': seller_id
                })
                
        except Exception as e:
            logger.error(f"OAuth callback error: {str(e)}")
            
            # Redirect to frontend error page or return JSON error
            if hasattr(settings, 'FRONTEND_URL'):
                redirect_url = f"{settings.FRONTEND_URL}/amazon/error?message={str(e)}"
                return HttpResponseRedirect(redirect_url)
            else:
                return JsonResponse({
                    'error': f"Authentication failed: {str(e)}"
                }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class AmazonAdvertisingCallbackView(View):
    """View to handle OAuth callback from Amazon Advertising API"""
    
    def get(self, request):
        """Handle the callback from Amazon Advertising with the authorization code"""
        # Get parameters from request
        auth_code = request.GET.get('code')  # Different parameter name for Advertising API
        state = request.GET.get('state')
        
        # Validate parameters
        if not auth_code:
            logger.error("Missing required parameter: code")
            return JsonResponse({
                'error': 'Missing required parameter: code'
            }, status=400)
        
        # Validate state for CSRF protection
        session_state = request.session.get('amazon_adv_oauth_state')
        if session_state and state != session_state:
            logger.error(f"State mismatch: {state} vs {session_state}")
            return JsonResponse({
                'error': 'State parameter mismatch. Possible CSRF attack.'
            }, status=400)
        
        try:
            # Exchange code for tokens
            region = request.GET.get('region', 'EU')
            token_data = AmazonAuthService.exchange_advertising_code_for_tokens(auth_code, region=region)
            
            # For Advertising API, we'll use the profile_id as the identifier
            # We'll need to make an API call to get the profile ID in a real implementation
            # For now, we'll use a placeholder
            profile_id = "advertising_profile"
            
            # Create or update the seller account for advertising
            # Note: In a real implementation, you might want a separate model for Advertising accounts
            seller_account, created = AmazonSellerAccount.objects.update_or_create(
                seller_id=f"adv_{profile_id}",  # Prefix to distinguish from seller accounts
                defaults={
                    'auth_code': auth_code,
                    'access_token': token_data['access_token'],
                    'refresh_token': token_data['refresh_token'],
                    'token_type': token_data['token_type'],
                    'token_expires_at': token_data['token_expires_at'],
                    'region': region,
                    'is_active': True
                }
            )
            
            logger.info(f"{'Created' if created else 'Updated'} Amazon advertising account: {profile_id}")
            
            # Clear the state from session
            if 'amazon_adv_oauth_state' in request.session:
                del request.session['amazon_adv_oauth_state']
            
            # Redirect to frontend success page
            if hasattr(settings, 'FRONTEND_URL'):
                redirect_url = f"{settings.FRONTEND_URL}/amazon/advertising/success?profile_id={profile_id}"
                return HttpResponseRedirect(redirect_url)
            else:
                # If no frontend URL is configured, return JSON response
                return JsonResponse({
                    'success': True,
                    'message': f"Successfully authenticated advertising account: {profile_id}",
                    'profile_id': profile_id
                })
                
        except Exception as e:
            logger.error(f"Advertising OAuth callback error: {str(e)}")
            
            # Redirect to frontend error page or return JSON error
            if hasattr(settings, 'FRONTEND_URL'):
                redirect_url = f"{settings.FRONTEND_URL}/amazon/advertising/error?message={str(e)}"
                return HttpResponseRedirect(redirect_url)
            else:
                return JsonResponse({
                    'error': f"Authentication failed: {str(e)}"
                }, status=500)
