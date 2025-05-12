from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

@api_view(['GET'])
def health_check(request):
    return Response({
        "status": "healthy",
        "message": "The service is running"
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
def connectivity_test(request):
    """
    Simple endpoint to test frontend-backend connectivity
    """
    try:
        # You can access POST data using request.data
        message = request.data.get('message', 'No message provided')
        
        return Response({
            "status": "success",
            "message": f"Backend message received: {message}",
            "echo": message
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

