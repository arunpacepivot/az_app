from django.db import migrations

def create_report_types(apps, schema_editor):
    ReportType = apps.get_model('amazon_ads_reports', 'ReportType')
    
    # Daily Product Ads Report
    ReportType.objects.create(
        name='Daily Product Ads Report',
        slug='daily-product-ads',
        description='Daily performance metrics for advertised products',
        api_report_type='spAdvertisedProduct',
        ad_product='SPONSORED_PRODUCTS',
        metrics=[
            'portfolioId', 'campaignName', 'campaignId', 'adGroupName', 'adGroupId', 'adId', 
            'campaignBudgetType', 'campaignBudgetAmount', 'campaignBudgetCurrencyCode', 
            'campaignStatus', 'advertisedAsin', 'advertisedSku', 'date', 'impressions', 
            'clicks', 'clickThroughRate', 'cost', 'costPerClick', 'spend', 'unitsSoldClicks30d', 
            'unitsSoldSameSku30d', 'sales1d', 'sales7d', 'sales14d', 'sales30d', 
            'attributedSalesSameSku30d', 'purchases1d', 'purchases7d', 'purchases14d', 
            'purchases30d', 'purchasesSameSku30d', 'unitsSoldOtherSku7d', 'salesOtherSku7d'
        ],
        time_unit='DAILY'
    )
    
    # Search Term Report
    ReportType.objects.create(
        name='Search Term Report',
        slug='search-term',
        description='Performance metrics for customer search terms',
        api_report_type='spSearchTerm',
        ad_product='SPONSORED_PRODUCTS',
        metrics=[
            'campaignId', 'campaignName', 'adGroupId', 'adGroupName', 'keywordId', 
            'keywordText', 'matchType', 'query', 'impressions', 'clicks', 'costPerClick', 
            'clickThroughRate', 'cost', 'conversions', 'conversionRate', 'sales7d', 
            'sales14d', 'sales30d', 'date'
        ],
        time_unit='DAILY'
    )
    
    # Campaign Placement Report
    ReportType.objects.create(
        name='Campaign Placement Report',
        slug='campaign-placement',
        description='Performance metrics by placement location',
        api_report_type='spCampaignPlacement',
        ad_product='SPONSORED_PRODUCTS',
        metrics=[
            'campaignId', 'campaignName', 'date', 'placementClassification', 
            'impressions', 'clicks', 'cost', 'costPerClick', 'clickThroughRate', 
            'sales7d', 'sales30d', 'purchases7d', 'purchases30d'
        ],
        time_unit='DAILY'
    )
    
    # Sponsored Display Report
    ReportType.objects.create(
        name='Sponsored Display Report',
        slug='sponsored-display',
        description='Performance metrics for Sponsored Display ads',
        api_report_type='sdAdvertisedProduct',
        ad_product='SPONSORED_DISPLAY',
        metrics=[
            'campaignId', 'campaignName', 'adGroupId', 'adGroupName', 'advertisedAsin', 
            'advertisedSku', 'impressions', 'clicks', 'cost', 'costPerClick', 'clickThroughRate', 
            'sales14d', 'purchases14d', 'date'
        ],
        time_unit='DAILY'
    )

def delete_report_types(apps, schema_editor):
    ReportType = apps.get_model('amazon_ads_reports', 'ReportType')
    ReportType.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ('amazon_ads_reports', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_report_types, delete_report_types),
    ] 