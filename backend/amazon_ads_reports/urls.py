from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TenantViewSet, AmazonAdsCredentialViewSet, ReportTypeViewSet,
    AdsReportViewSet, DailyProductAdsDataViewSet, SearchTermReportDataViewSet,
    ReportScheduleViewSet
)

router = DefaultRouter()
router.register(r'tenants', TenantViewSet)
router.register(r'credentials', AmazonAdsCredentialViewSet)
router.register(r'report-types', ReportTypeViewSet)
router.register(r'reports', AdsReportViewSet)
router.register(r'daily-data', DailyProductAdsDataViewSet)
router.register(r'search-terms', SearchTermReportDataViewSet)
router.register(r'schedules', ReportScheduleViewSet)

app_name = 'amazon_ads_reports'

urlpatterns = [
    path('', include(router.urls)),
] 