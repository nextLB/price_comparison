from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Pharmacy, PharmaceuticalCompany, Drug, PharmacyRecord, CompanyRecord


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'user_type', 'district', 'is_staff')
    list_filter = ('user_type', 'is_staff', 'is_superuser')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('扩展信息', {'fields': ('user_type', 'phone', 'district')}),
    )


@admin.register(Pharmacy)
class PharmacyAdmin(admin.ModelAdmin):
    list_display = ('pharmacy_code', 'pharmacy_name', 'medical_insurance_code', 'district')
    search_fields = ('pharmacy_name', 'pharmacy_code')


@admin.register(PharmaceuticalCompany)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('company_code', 'company_name')
    search_fields = ('company_name', 'company_code')


@admin.register(Drug)
class DrugAdmin(admin.ModelAdmin):
    list_display = ('code', 'generic_name', 'drug_category', 'network_price', 'is_standard')
    search_fields = ('code', 'generic_name')
    list_filter = ('drug_category',)


@admin.register(PharmacyRecord)
class PharmacyRecordAdmin(admin.ModelAdmin):
    list_display = ('pharmacy', 'drug', 'record_price', 'record_date', 'status')
    list_filter = ('status', 'record_date')


@admin.register(CompanyRecord)
class CompanyRecordAdmin(admin.ModelAdmin):
    list_display = ('company', 'drug', 'declared_price', 'record_date', 'status')
    list_filter = ('status', 'record_date')
