from django.urls import path
from . import views

app_name = 'contracts'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('tenant/<int:tenant_id>/', views.tenant_detail, name='tenant_detail'),
    path('contract/<int:contract_id>/', views.contract_detail, name='contract_detail'),
    path('template/<int:template_id>/', views.template_detail, name='template_detail'),
    path('reporting-period/<int:period_id>/', views.reporting_period_detail, name='reporting_period_detail'),
    path('reporting-period/<int:period_id>/generate/', views.generate_report, name='generate_report'),
]
