from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

@api_view(['GET'])
def health_check(request):
    return Response({
        "status": "healthy",
        "message": "The service is running"
    }, status=status.HTTP_200_OK)
