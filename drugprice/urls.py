from django.contrib import admin
from django.urls import path, include
from core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', core_views.login_view, name='login'),
    path('register/', core_views.register_view, name='register'),
    path('logout/', core_views.logout_view, name='logout'),
    path('dashboard/', core_views.dashboard, name='dashboard'),
    
    path('drugs/', core_views.drug_list, name='drug_list'),
    path('drugs/calculate/', core_views.calculate_ratio, name='calculate_ratio'),
    path('drugs/import/', core_views.import_drugs, name='import_drugs'),
    path('drugs/anchor/import/', core_views.import_anchor_price, name='import_anchor_price'),
    
    path('pharmacies/', core_views.pharmacy_list, name='pharmacy_list'),
    path('pharmacies/import/', core_views.pharmacy_import, name='pharmacy_import'),
    path('pharmacies/records/review/', core_views.pharmacy_record_review, name='pharmacy_record_review'),
    
    path('companies/', core_views.company_list, name='company_list'),
    path('companies/import/', core_views.company_import, name='company_import'),
    
    path('pharmacy/records/submit/', core_views.pharmacy_record_submit, name='pharmacy_record_submit'),
    path('pharmacy/records/', core_views.pharmacy_record_list, name='pharmacy_record_list'),
    
    path('company/records/submit/', core_views.company_record_submit, name='company_record_submit'),
    path('company/records/', core_views.company_record_list, name='company_record_list'),
    
    path('district/records/review/', core_views.district_record_review, name='district_record_review'),
]
