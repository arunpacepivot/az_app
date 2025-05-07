from django.shortcuts import render

# Create your views here.

"""
API views for Amazon Seller and Advertising OAuth flows
"""
import logging
import json
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views import View
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404

from .models import AmazonSellerAccount, AmazonAdvertisingAccount, AdvertisingReport, ReportSchedule
from .services.auth import AmazonAuthService
from .services.advertising import AmazonAdvertisingService
from .services.reports import ReportingService
from .serializers import (
    ReportScheduleSerializer,
    AdvertisingReportSerializer,
    ReportScheduleCreateSerializer
)

User = get_user_model()
logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class AmazonAuthView(View):
    """View to initiate Amazon Seller OAuth flow"""
    
    def get(self, request):
        """Generate an authorization URL for Amazon Seller Central"""
        region = request.GET.get('region', 'EU')  # Default to EU
        
        # Get user_id from query params if provided
        user_id = request.GET.get('user_id')
        
        try:
            auth_url, state = AmazonAuthService.get_authorization_url(region=region)
            
            # Store state in session for CSRF protection
            request.session['amazon_oauth_state'] = state
            
            # Store user_id in session if provided for mapping
            if user_id:
                request.session['amazon_oauth_user_id'] = user_id
            
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
        
        # Get user_id from query params for mapping
        user_id = request.GET.get('user_id')
        
        try:
            auth_url, state = AmazonAuthService.get_advertising_authorization_url(
                region=region,
                scopes=scopes_list,
                user_id=user_id
            )
            
            # Store state in session for CSRF protection
            request.session['amazon_adv_oauth_state'] = state
            
            # Store user_id in session if provided for mapping
            if user_id:
                request.session['amazon_adv_oauth_user_id'] = user_id
            
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
    """View to handle OAuth callback from Amazon Seller API"""
    
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
        
        # Validate state for CSRF protection
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
            
            # Check if we have a user_id stored in session for mapping
            user_id = request.session.get('amazon_oauth_user_id')
            user = None
            
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                    logger.info(f"Found user with ID {user_id} for mapping seller account")
                except User.DoesNotExist:
                    logger.warning(f"User with ID {user_id} not found for mapping seller account")
            
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
                    'is_active': True,
                    'user': user  # Link to user if available
                }
            )
            
            logger.info(f"{'Created' if created else 'Updated'} Amazon seller account: {seller_id}")
            
            # Clear the state and user_id from session
            if 'amazon_oauth_state' in request.session:
                del request.session['amazon_oauth_state']
            if 'amazon_oauth_user_id' in request.session:
                del request.session['amazon_oauth_user_id']
            
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
        
        # For advertising API, state might contain user_id
        user_id = None
        
        # Try to parse state as JSON to extract user_id
        if state:
            try:
                state_data = json.loads(state)
                if isinstance(state_data, dict) and 'user_id' in state_data:
                    user_id = state_data['user_id']
                    # Use uuid for state comparison
                    if session_state and state_data.get('uuid') != session_state:
                        logger.error(f"State UUID mismatch")
                        return JsonResponse({
                            'error': 'State parameter mismatch. Possible CSRF attack.'
                        }, status=400)
            except json.JSONDecodeError:
                # If not JSON, treat state as a simple string
                if session_state and state != session_state:
                    logger.error(f"State mismatch: {state} vs {session_state}")
                    return JsonResponse({
                        'error': 'State parameter mismatch. Possible CSRF attack.'
                    }, status=400)
        
        # If no user_id from state, check session
        if not user_id:
            user_id = request.session.get('amazon_adv_oauth_user_id')
        
        try:
            # Exchange code for tokens
            region = request.GET.get('region', 'EU')
            token_data = AmazonAuthService.exchange_advertising_code_for_tokens(auth_code, region=region)
            
            # Try to get user for mapping
            user = None
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                    logger.info(f"Found user with ID {user_id} for mapping advertising account")
                except User.DoesNotExist:
                    logger.warning(f"User with ID {user_id} not found for mapping advertising account")
            
            # After getting tokens, fetch profiles to get profile_id
            # Create a temporary account object for API calls
            temp_account = AmazonAdvertisingAccount(
                profile_id='temp',
                access_token=token_data['access_token'],
                refresh_token=token_data['refresh_token'],
                token_type=token_data['token_type'],
                token_expires_at=token_data['token_expires_at'],
                region=region,
                scopes=token_data.get('scopes', ''),
                is_active=True
            )
            
            # Get profiles from the Advertising API
            try:
                profiles = AmazonAuthService.get_advertising_profiles(temp_account.access_token, region=region)
                
                # If profiles were found, create accounts for each
                if profiles and isinstance(profiles, list):
                    created_accounts = []
                    
                    for profile in profiles:
                        profile_id = profile.get('profileId')
                        
                        if profile_id:
                            ad_account, created = AmazonAdvertisingAccount.objects.update_or_create(
                                profile_id=profile_id,
                                defaults={
                                    'auth_code': auth_code,
                                    'access_token': token_data['access_token'],
                                    'refresh_token': token_data['refresh_token'],
                                    'token_type': token_data['token_type'],
                                    'token_expires_at': token_data['token_expires_at'],
                                    'region': region,
                                    'scopes': token_data.get('scopes', ''),
                                    'is_active': True,
                                    'user': user  # Link to user if available
                                }
                            )
                            
                            created_accounts.append({
                                'profile_id': profile_id,
                                'account_type': profile.get('accountInfo', {}).get('type'),
                                'marketplace_id': profile.get('accountInfo', {}).get('marketplaceStringId'),
                                'created': created
                            })
                            
                            logger.info(f"{'Created' if created else 'Updated'} advertising account: {profile_id}")
                    
                    # Clear the state and user_id from session
                    if 'amazon_adv_oauth_state' in request.session:
                        del request.session['amazon_adv_oauth_state']
                    if 'amazon_adv_oauth_user_id' in request.session:
                        del request.session['amazon_adv_oauth_user_id']
                    
                    # Redirect to frontend success page
                    if hasattr(settings, 'FRONTEND_URL'):
                        redirect_url = f"{settings.FRONTEND_URL}/amazon/advertising/success?profiles={','.join([a['profile_id'] for a in created_accounts])}"
                        return HttpResponseRedirect(redirect_url)
                    else:
                        # If no frontend URL is configured, return JSON response
                        return JsonResponse({
                            'success': True,
                            'message': f"Successfully authenticated advertising accounts",
                            'accounts': created_accounts
                        })
                else:
                    logger.error(f"No advertising profiles found")
                    return JsonResponse({
                        'error': 'No advertising profiles found for the authorized account'
                    }, status=400)
                    
            except Exception as profile_error:
                logger.error(f"Error fetching advertising profiles: {str(profile_error)}")
                
                # If we can't get profiles, create a generic advertising account
                generic_profile_id = f"adv_{user_id or 'unknown'}_{timezone.now().timestamp()}"
                
                ad_account, created = AmazonAdvertisingAccount.objects.update_or_create(
                    profile_id=generic_profile_id,
                defaults={
                    'auth_code': auth_code,
                    'access_token': token_data['access_token'],
                    'refresh_token': token_data['refresh_token'],
                    'token_type': token_data['token_type'],
                    'token_expires_at': token_data['token_expires_at'],
                    'region': region,
                        'scopes': token_data.get('scopes', ''),
                        'is_active': True,
                        'user': user  # Link to user if available
                }
            )
            
                logger.info(f"Created generic advertising account: {generic_profile_id}")
            
                # Clear the state and user_id from session
            if 'amazon_adv_oauth_state' in request.session:
                del request.session['amazon_adv_oauth_state']
                if 'amazon_adv_oauth_user_id' in request.session:
                    del request.session['amazon_adv_oauth_user_id']
            
            # Redirect to frontend success page
            if hasattr(settings, 'FRONTEND_URL'):
                redirect_url = f"{settings.FRONTEND_URL}/amazon/advertising/success?profile_id={generic_profile_id}"
                return HttpResponseRedirect(redirect_url)
            else:
                # If no frontend URL is configured, return JSON response
                return JsonResponse({
                    'success': True,
                    'message': f"Successfully authenticated advertising account (generic)",
                    'profile_id': generic_profile_id,
                    'warning': f"Could not fetch profiles: {str(profile_error)}"
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


# API views with authentication for frontend use
class AdvertisingProfilesAPIView(APIView):
    """View to list advertising profiles for authenticated user"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get all advertising profiles for the authenticated user"""
        user = request.user
        
        # Get all advertising accounts for the user
        accounts = AmazonAdvertisingAccount.objects.filter(user=user, is_active=True)
        
        profiles_data = []
        for account in accounts:
            try:
                # Get actual profiles from the API
                profiles = AmazonAdvertisingService.get_profiles(account)
                profiles_data.extend(profiles)
            except Exception as e:
                logger.error(f"Error getting profiles for account {account.profile_id}: {str(e)}")
                # Add basic profile info from the database
                profiles_data.append({
                    'profileId': account.profile_id,
                    'error': str(e)
                })
        
        return Response(profiles_data)


class AdvertisingCampaignsAPIView(APIView):
    """View to list and create advertising campaigns"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, profile_id=None):
        """Get campaigns for a specific profile"""
        user = request.user
        
        if not profile_id:
            return Response({"error": "Profile ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get the advertising account
            account = AmazonAdvertisingAccount.objects.get(
                profile_id=profile_id,
                user=user,
                is_active=True
            )
            
            # Get optional query parameters
            state_filter = request.query_params.get('state')
            campaign_type = request.query_params.get('campaignType')
            
            # Get campaigns from the API
            campaigns = AmazonAdvertisingService.get_campaigns(
                account, 
                profile_id, 
                state_filter=state_filter,
                campaign_type=campaign_type
            )
            
            return Response(campaigns)
        except AmazonAdvertisingAccount.DoesNotExist:
            return Response(
                {"error": f"No active advertising account found for profile {profile_id}"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error getting campaigns: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, profile_id=None):
        """Create a new campaign for a specific profile"""
        user = request.user
        
        if not profile_id:
            return Response({"error": "Profile ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get the advertising account
            account = AmazonAdvertisingAccount.objects.get(
                profile_id=profile_id,
                user=user,
                is_active=True
            )
            
            # Get campaign data from request body
            campaign_data = request.data
            
            # Create campaign through the API
            result = AmazonAdvertisingService.create_campaign(account, profile_id, campaign_data)
            
            return Response(result, status=status.HTTP_201_CREATED)
        except AmazonAdvertisingAccount.DoesNotExist:
            return Response(
                {"error": f"No active advertising account found for profile {profile_id}"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error creating campaign: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdvertisingAdGroupsAPIView(APIView):
    """View to list and create ad groups"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, profile_id=None):
        """Get ad groups for a specific profile"""
        user = request.user
        
        if not profile_id:
            return Response({"error": "Profile ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get the advertising account
            account = AmazonAdvertisingAccount.objects.get(
                profile_id=profile_id,
                user=user,
                is_active=True
            )
            
            # Get optional query parameters
            campaign_id = request.query_params.get('campaignId')
            state_filter = request.query_params.get('state')
            
            # Get ad groups from the API
            ad_groups = AmazonAdvertisingService.get_ad_groups(
                account, 
                profile_id, 
                campaign_id=campaign_id,
                state_filter=state_filter
            )
            
            return Response(ad_groups)
        except AmazonAdvertisingAccount.DoesNotExist:
            return Response(
                {"error": f"No active advertising account found for profile {profile_id}"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error getting ad groups: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, profile_id=None):
        """Create a new ad group for a specific profile"""
        user = request.user
        
        if not profile_id:
            return Response({"error": "Profile ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get the advertising account
            account = AmazonAdvertisingAccount.objects.get(
                profile_id=profile_id,
                user=user,
                is_active=True
            )
            
            # Get ad group data from request body
            ad_group_data = request.data
            
            # Create ad group through the API
            result = AmazonAdvertisingService.create_ad_group(account, profile_id, ad_group_data)
            
            return Response(result, status=status.HTTP_201_CREATED)
        except AmazonAdvertisingAccount.DoesNotExist:
            return Response(
                {"error": f"No active advertising account found for profile {profile_id}"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error creating ad group: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdvertisingReportsAPIView(APIView):
    """View to generate advertising reports"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, profile_id=None):
        """Generate a report for a specific profile"""
        user = request.user
        
        if not profile_id:
            return Response({"error": "Profile ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get the advertising account
            account = AmazonAdvertisingAccount.objects.get(
                profile_id=profile_id,
                user=user,
                is_active=True
            )
            
            # Get report parameters from request body
            report_type = request.data.get('reportType')
            metrics = request.data.get('metrics', [])
            start_date = request.data.get('startDate')
            end_date = request.data.get('endDate')
            segment = request.data.get('segment')
            
            # Validate required parameters
            if not report_type or not metrics or not end_date:
                return Response(
                    {"error": "reportType, metrics, and endDate are required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Generate report through the API
            result = AmazonAdvertisingService.get_reports(
                account, 
                profile_id, 
                report_type, 
                metrics, 
                start_date, 
                end_date,
                segment=segment
            )
            
            return Response(result)
        except AmazonAdvertisingAccount.DoesNotExist:
            return Response(
                {"error": f"No active advertising account found for profile {profile_id}"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReportScheduleAPIView(viewsets.ModelViewSet):
    """
    API endpoint for managing report schedules
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ReportScheduleSerializer
    queryset = ReportSchedule.objects.all()

    def get_queryset(self):
        """Filter schedules by user"""
        return ReportSchedule.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        """Use different serializer for creation"""
        if self.action == 'create':
            return ReportScheduleCreateSerializer
        return ReportScheduleSerializer

    def perform_create(self, serializer):
        """Set user and calculate next run time"""
        schedule = serializer.save(user=self.request.user)
        schedule.calculate_next_run()
        schedule.save()

    @action(detail=True, methods=['post'])
    def run_now(self, request, pk=None):
        """Run a scheduled report immediately"""
        schedule = self.get_object()
        
        try:
            # Calculate date range
            start_date, end_date = ReportingService.calculate_date_range(
                schedule.date_range,
                schedule.custom_start_date,
                schedule.custom_end_date
            )
            
            # Request the report
            report = ReportingService.request_report(
                account=schedule.advertising_account,
                profile_id=schedule.advertising_account.profile_id,
                report_type=schedule.report_type,
                metrics=schedule.metrics,
                start_date=start_date,
                end_date=end_date,
                segment=schedule.segment,
                user=schedule.user
            )
            
            # Update schedule
            schedule.last_run = timezone.now()
            schedule.calculate_next_run()
            schedule.save()
            
            return Response({
                'status': 'success',
                'report_id': str(report.report_id)
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ReportAPIView(viewsets.ModelViewSet):
    """
    API endpoint for managing advertising reports
    """
    permission_classes = [IsAuthenticated]
    serializer_class = AdvertisingReportSerializer
    queryset = AdvertisingReport.objects.all()

    def get_queryset(self):
        """Filter reports by user"""
        return AdvertisingReport.objects.filter(user=self.request.user)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download report data"""
        report = self.get_object()
        
        if not report.report_data:
            return Response({
                'status': 'error',
                'message': 'Report data not available'
            }, status=status.HTTP_404_NOT_FOUND)
            
        return Response(report.report_data)

    @action(detail=True, methods=['post'])
    def refresh(self, request, pk=None):
        """Refresh report status and data"""
        report = self.get_object()
        
        try:
            # In a real implementation, we would call the API to check status
            # For now, simulate with a placeholder
            if report.status in ['PENDING', 'IN_PROGRESS', 'PROCESSING']:
                # For demonstration, mark as complete after 5 minutes
                if (timezone.now() - report.created_at).total_seconds() > 300:
                    report.status = 'COMPLETED'
                    report.completed_at = timezone.now()
                    
                    # Simulate downloaded data
                    sample_data = {
                        "reportId": report.report_id,
                        "status": "COMPLETED",
                        "data": [
                            {"campaign": "Campaign 1", "impressions": 1000, "clicks": 50},
                            {"campaign": "Campaign 2", "impressions": 2000, "clicks": 100}
                        ]
                    }
                    
                    report.report_data = sample_data
                    report.save()
                    
                    return Response({
                        'status': 'success',
                        'message': 'Report completed and downloaded'
                    })
                else:
                    return Response({
                        'status': 'pending',
                        'message': 'Report still processing'
                    })
            else:
                return Response({
                    'status': 'error',
                    'message': 'Report is not in a pending state'
                })
                
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
