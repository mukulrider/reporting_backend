from django.conf.urls import url, include
from . import view_supplier
from . import view_promo
import urllib
from rest_framework.routers import DefaultRouter
from rest_framework.urlpatterns import format_suffix_patterns
from . import view_competitor, view_daily_sales,view_executive, view_product, view_kantar

router = DefaultRouter()

urlpatterns = [
    #URL for Product Page View
    url(r'^reporting/product$', view_product.product_performance.as_view(), name='product_performance'),
    url(r'^reporting/supplier_modal$', view_product.supplier_modal.as_view(), name='product_performance'),
    url(r'^reporting/sales_trend$', view_product.sales_trend.as_view(), name='product_performance'),
    url(r'^reporting/filter_data_product', view_product.Filters.as_view(), name='Filters'),
    url(r'^reporting/product/filter_data_week', view_product.product_filterdata_week.as_view(), name='product_filterdata'),

    #new filters
    url(r'^reporting/filter_new_data_product', view_product.product_filters_new.as_view(), name='product_filters_new'),


    # URL for filter data daily sales view
    url(r'^reporting/data_daily_sales', view_daily_sales.data_stage.as_view(),
        name='daily_sales'),
    url(r'^reporting/graph_daily_sales', view_daily_sales.dss_data_graph.as_view(),
        name='daily_sales'),
    url(r'^reporting/filter_daily_sales', view_daily_sales.dss_filterdata.as_view(),
        name='daily_sales_filters'),
    url(r'^reporting/filter_daily_tesco_week', view_daily_sales.dss_filterdata_weeks.as_view(),
        name='daily_sales_filters_weeks'),
    url(r'^reporting/dss_filter_week', view_daily_sales.dss_filter_week.as_view(),
        name='dss_filter_week'),

    #new filters
    url(r'^reporting/filter_new_daily_sales', view_daily_sales.daily_sales_filters_new.as_view(),
        name='daily_sales_filters_new'),

    ### Competitor URLS
    url(r'^reporting/filter_data_week', view_competitor.competitor_filterdata_week.as_view(),
        name='competitor_filterdata'),
    url(r'^reporting/competitor_filter_data', view_competitor.competitor_filterdata.as_view(),
        name='competitor_filterdata'),
    url(r'^reporting/competitor_view_range', view_competitor.competitor_view_range.as_view(),
        name='competitor_view_range'),
    # URL for model viewsets
    url(r'^', include(router.urls)),
    url(r'^reporting/competitor_market_outperformance', view_competitor.competitor_market_outperformance.as_view(),
        name='competitor_market_outperformance'),
    # URL for competitor view price index
    url(r'^reporting/competitor_market_share', view_competitor.competitor_market_share_1.as_view(),
        name='competitor_market_share_1'),
    url(r'reporting/competitor_price_index', view_competitor.competitor_price_index_2.as_view(),
        name='competitor_price_index_1'),


    ### URLs for supplier view
    url(r'^reporting/supplier_filter_data_week', view_supplier.supplier_filterdata_week.as_view(),
        name='competitor_filterdata'),
    url(r'^reporting/supplier_view_kpi', view_supplier.supplier_view_kpi.as_view(), name='supplier_view_kpi'),
    # URL for supplier view table below bubble chart
    url(r'^reporting/supplier_view_table_bubble', view_supplier.supplier_view_table_bubble.as_view(),
        name='supplier_view_table_bubble'),
    # URL for supplier view bubble chart
    url(r'^reporting/supplier_view_chart_bubble', view_supplier.supplier_view_chart_bubble.as_view(),
        name='supplier_view_chart_bubble'),
    url(r'^reporting/supplier_view_top_bottom', view_supplier.supplier_view_top_bottom.as_view(),
        name='supplier_view_top_bottom'),
    url(r'^reporting/filter_supplier', view_supplier.filters_supplier.as_view(), name='filters_supplier'),

    #new filters
    url(r'^reporting/filter_new_supplier', view_supplier.supplier_filters_new.as_view(), name='filters_new_supplier'),


    #URL for Supplier View Kantar Report
    url(r'^reporting/kantar_data', view_kantar.kantar_calculations.as_view(), name='kantar_data'),
    url(r'^reporting/kantar_tesco_week_filter', view_kantar.kantar_tesco_week_filters.as_view(), name='kantar_tesco_week_filters'),
    url(r'^reporting/kantar_filter', view_kantar.kantar_heirarchy_filter.as_view(), name='kantar_heirarchy_filter'),

    # Promo View Filter Urls
    url(r'^reporting/promo_filter_data', view_promo.promo_filterdata.as_view(), name='promo_filterdata'),
    url(r'^reporting/week_promo_filter_data', view_promo.promotion_filterdata_week.as_view(),
        name='promotion_week_filterdata'),
    # new filters
    url(r'^reporting/promo_new_filter_data', view_promo.promo_filters_new.as_view(), name='promo_filters_new'),

    # Promo View Urls
    url(r'^reporting/promo_kpi', view_promo.promo_kpi.as_view(), name='promo_kpi'),
    url(r'^reporting/promo_piechart', view_promo.promo_piechart.as_view(), name='promo_piechart'),
    url(r'^reporting/promo_trendchart', view_promo.promo_trendchart.as_view(), name='promo_trendchart'),
    url(r'^reporting/promo_table', view_promo.promo_prodtable.as_view(), name='promo_product_table'),
    url(r'^reporting/promo_prdlevel', view_promo.promo_product_level_info.as_view(), name='promo_product_level'),
    url(r'^reporting/promo_mechlevel', view_promo.promo_mechanic_name_level_info.as_view(), name='promo_product_level'),

    # Executive View Filter Urls
    url(r'^reporting/exec_filter_data', view_executive.executive_filterdata.as_view(), name='executive_filterdata'),
    url(r'^reporting/week_exec_filter_data', view_executive.executive_filterdata_week.as_view(),
        name='executive_week_filterdata'),

    #new filters
    url(r'^reporting/exec_new_filter_data', view_executive.executive_filters_new.as_view(), name='executive_filters_new'),

    # Exec urls to be used for overview tab

    url(r'^reporting/exec_overview_kpis', view_executive.OverviewKpis.as_view(), name='performance'),
    url(r'^reporting/exec_roles_and_intent', view_executive.roles_and_int.as_view(), name='strategy'),
    url(r'^reporting/exec_budget_forecast', view_executive.budget_forecast.as_view(), name='strategy'),
    url(r'^reporting/exec_overview_kpitrends', view_executive.OverviewKpiTrends.as_view(), name='trended'),
    url(r'^reporting/exec_overview_drivers_internal', view_executive.OverviewDriversInternal.as_view(),
        name='internal_drivers'),
    url(r'^reporting/exec_overview_drivers_external', view_executive.OverviewDriversExternal.as_view(),
        name='external_drivers'),

    # Exec urls to be used for value tab
    url(r'^reporting/exec_kpi', view_executive.KPI.as_view(), name='kpi'),
    url(r'^reporting/exec_best_worst', view_executive.BestWorstInfo.as_view(), name='best_worst_list'),
    url(r'^reporting/exec_best_info', view_executive.BestInfo.as_view(), name='best_chart'),
    url(r'^reporting/exec_worst_info', view_executive.WorstInfo.as_view(), name='worst_chart'),
    url(r'^reporting/exec_supp_info', view_executive.SupplierInfo.as_view(), name='supplier_list_top'),
    url(r'^reporting/exec_drivers_internal', view_executive.DriversInternalView.as_view(),
        name='value_internal_drivers'),
    url(r'^reporting/exec_drivers_external', view_executive.DriversExternalView.as_view(),
        name='value_external_drivers'),

    # Exec urls to be used for price tab
    url(r'^reporting/exec_pricing', view_executive.Pricing.as_view(), name='pricing'),
    url(r'^reporting/exec_holidays', view_executive.Holidays.as_view(), name='holidays'),
    url(r'^reporting/exec_supplier_info', view_executive.exec_supplier_info.as_view(), name='exec_supplier_info'),
    url(r'^reporting/executive_best_worst_performance', view_executive.executive_best_worst_performance.as_view(), name='best_worst_performance'),
    url(r'^reporting/exec_selected_level_performance', view_executive.exec_selected_level_performance.as_view(), name='exec_selected_level_performance'),

]
