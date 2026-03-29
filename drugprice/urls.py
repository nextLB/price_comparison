from django.contrib import admin
from django.urls import path
from core import views as v

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', v.login_view, name='login'),
    path('register/', v.register_view, name='register'),
    path('logout/', v.logout_view, name='logout'),
    path('dashboard/', v.dashboard, name='dashboard'),
    
    # 系统管理
    path('system/users/', v.user_list, name='user_list'),
    path('system/users/create/', v.user_create, name='user_create'),
    path('system/roles/', v.role_list, name='role_list'),
    path('system/roles/create/', v.role_create, name='role_create'),
    path('system/departments/', v.department_list, name='department_list'),
    path('system/departments/create/', v.department_create, name='department_create'),
    
    # 客户管理
    path('crm/customers/', v.customer_list, name='customer_list'),
    path('crm/customers/create/', v.customer_create, name='customer_create'),
    path('crm/customers/<int:pk>/', v.customer_detail, name='customer_detail'),
    path('crm/customers/<int:pk>/edit/', v.customer_edit, name='customer_edit'),
    path('crm/customers/<int:pk>/delete/', v.customer_delete, name='customer_delete'),
    path('crm/contacts/', v.contact_list, name='contact_list'),
    path('crm/contacts/create/', v.contact_create, name='contact_create'),
    path('crm/contacts/<int:pk>/edit/', v.contact_edit, name='contact_edit'),
    path('crm/contacts/<int:pk>/delete/', v.contact_delete, name='contact_delete'),
    
    # 项目管理
    path('projects/', v.project_list, name='project_list'),
    path('projects/create/', v.project_create, name='project_create'),
    path('projects/<int:pk>/', v.project_detail, name='project_detail'),
    path('projects/<int:pk>/edit/', v.project_edit, name='project_edit'),
    path('projects/<int:pk>/delete/', v.project_delete, name='project_delete'),
    
    # 跟进管理
    path('followups/', v.followup_list, name='followup_list'),
    path('followups/create/', v.followup_create, name='followup_create'),
    path('followups/<int:pk>/edit/', v.followup_edit, name='followup_edit'),
    path('followups/<int:pk>/delete/', v.followup_delete, name='followup_delete'),
    
    # 出差管理
    path('trips/', v.trip_list, name='trip_list'),
    path('trips/create/', v.trip_create, name='trip_create'),
    path('trips/<int:pk>/approve/', v.trip_approve, name='trip_approve'),
    
    # 业务费管理
    path('expenses/', v.expense_list, name='expense_list'),
    path('expenses/create/', v.expense_create, name='expense_create'),
    path('expenses/<int:pk>/approve/', v.expense_approve, name='expense_approve'),
    
    # 药品差比价管理
    path('drugs/', v.drug_list, name='drug_list'),
    path('drugs/import/', v.drug_import, name='drug_import'),
    path('drugs/calculate/', v.drug_calculate, name='drug_calculate'),
    path('pharmacies/', v.pharmacy_list, name='pharmacy_list'),
    path('pharmacies/import/', v.pharmacy_import, name='pharmacy_import'),
    path('companies/', v.company_list, name='company_list'),
    path('companies/import/', v.company_import, name='company_import'),
]
