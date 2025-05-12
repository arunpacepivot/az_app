from django.shortcuts import render
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from .models import ErrorLog
from .serializers import ErrorLogSerializer

class ErrorLogPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 1000

class ErrorLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows error logs to be viewed.
    Only accessible to staff users for security.
    """
    queryset = ErrorLog.objects.all()
    serializer_class = ErrorLogSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = ErrorLogPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['level', 'source', 'component']
    search_fields = ['message', 'component']
    ordering_fields = ['timestamp', 'level', 'source']
    ordering = ['-timestamp']

@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def error_log_stats(request):
    """
    Get statistics about error logs.
    """
    # Count by level
    level_stats = {}
    for level, _ in ErrorLog.ERROR_LEVELS:
        level_stats[level] = ErrorLog.objects.filter(level=level).count()
    
    # Count by source
    source_stats = {}
    for source, _ in ErrorLog.SOURCE_TYPES:
        source_stats[source] = ErrorLog.objects.filter(source=source).count()
    
    # Count by date (last 7 days)
    from django.utils import timezone
    from django.db.models.functions import TruncDate
    from django.db.models import Count
    
    today = timezone.now().date()
    seven_days_ago = today - timezone.timedelta(days=7)
    
    daily_counts = ErrorLog.objects.filter(
        timestamp__date__gte=seven_days_ago
    ).annotate(
        date=TruncDate('timestamp')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    date_stats = {
        item['date'].strftime('%Y-%m-%d'): item['count'] 
        for item in daily_counts
    }
    
    # Total count
    total_count = ErrorLog.objects.count()
    
    return Response({
        'total': total_count,
        'by_level': level_stats,
        'by_source': source_stats,
        'by_date': date_stats
    })
