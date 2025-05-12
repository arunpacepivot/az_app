"""
API views for Amazon SP API authentication
"""
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import AmazonSPApiToken
from .auth_service import SPApiAuthService
from .serializers import AmazonSPApiTokenSerializer

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def token_list(request):
    """List all tokens"""
    tokens = AmazonSPApiToken.objects.all()
    serializer = AmazonSPApiTokenSerializer(tokens, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_active_token(request):
    """Get the currently active token"""
    token = AmazonSPApiToken.objects.filter(is_active=True).first()
    if not token:
        return Response({"error": "No active token found"}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = AmazonSPApiTokenSerializer(token)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_token(request):
    """Create a new token"""
    serializer = AmazonSPApiTokenSerializer(data=request.data)
    if serializer.is_valid():
        # If setting this as active, deactivate all other tokens
        if request.data.get('is_active', False):
            AmazonSPApiToken.objects.all().update(is_active=False)
            
        serializer.save()
        
        # Try to refresh to get the access token
        try:
            token = serializer.instance
            access_token = SPApiAuthService.get_access_token(
                client_id=token.client_id,
                client_secret=token.client_secret,
                refresh_token=token.refresh_token,
                region=token.region
            )
            # Re-serialize to include access token
            serializer = AmazonSPApiTokenSerializer(token)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            # Return created but with warning
            return Response({
                "data": serializer.data,
                "warning": "Token created but could not be refreshed. Check credentials."
            }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_token(request, token_id):
    """Update an existing token"""
    try:
        token = AmazonSPApiToken.objects.get(pk=token_id)
    except AmazonSPApiToken.DoesNotExist:
        return Response({"error": "Token not found"}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = AmazonSPApiTokenSerializer(token, data=request.data, partial=True)
    if serializer.is_valid():
        # If setting this as active, deactivate all other tokens
        if request.data.get('is_active', False):
            AmazonSPApiToken.objects.exclude(pk=token_id).update(is_active=False)
            
        serializer.save()
        return Response(serializer.data)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_token(request, token_id):
    """Delete a token"""
    try:
        token = AmazonSPApiToken.objects.get(pk=token_id)
    except AmazonSPApiToken.DoesNotExist:
        return Response({"error": "Token not found"}, status=status.HTTP_404_NOT_FOUND)
    
    token.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refresh_token(request, token_id):
    """Manually refresh a token"""
    try:
        token = AmazonSPApiToken.objects.get(pk=token_id)
    except AmazonSPApiToken.DoesNotExist:
        return Response({"error": "Token not found"}, status=status.HTTP_404_NOT_FOUND)
    
    try:
        access_token = SPApiAuthService.get_access_token(
            client_id=token.client_id,
            client_secret=token.client_secret,
            refresh_token=token.refresh_token,
            region=token.region
        )
        
        # Re-fetch the token to get updated info
        token.refresh_from_db()
        serializer = AmazonSPApiTokenSerializer(token)
        return Response(serializer.data)
    
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_active_token(request, token_id):
    """Set a token as active and deactivate others"""
    try:
        token = AmazonSPApiToken.objects.get(pk=token_id)
    except AmazonSPApiToken.DoesNotExist:
        return Response({"error": "Token not found"}, status=status.HTTP_404_NOT_FOUND)
    
    # Deactivate all tokens
    AmazonSPApiToken.objects.all().update(is_active=False)
    
    # Activate the selected token
    token.is_active = True
    token.save()
    
    serializer = AmazonSPApiTokenSerializer(token)
    return Response(serializer.data)

@api_view(['GET'])
def get_current_access_token(request):
    """Get the current access token - for use by other APIs"""
    try:
        access_token = SPApiAuthService.get_access_token()
        return Response({"access_token": access_token})
    except Exception as e:
        logger.error(f"Error getting access token: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST) 