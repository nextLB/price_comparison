from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Department, Role, Permission,
    Customer, Contact, Project, FollowUp,
    Trip, Expense, Drug, Pharmacy, PharmaceuticalCompany,
    PharmacyRecord, CompanyRecord
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'user_type', 'department', 'is_staff')
    list_filter = ('user_type', 'is_staff', 'is_superuser')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('扩展信息', {'fields': ('user_type', 'phone', 'department')}),
    )


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'parent', 'manager')
    search_fields = ('name', 'code')


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'created_at')
    search_fields = ('name', 'code')


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'module')
    search_fields = ('name', 'code')
    list_filter = ('module',)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'industry', 'level', 'status', 'owner')
    search_fields = ('name', 'code')
    list_filter = ('status', 'source')


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'customer', 'position', 'phone', 'mobile', 'email', 'is_primary')
    search_fields = ('name', 'customer__name')
    list_filter = ('is_primary',)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'customer', 'budget', 'status', 'owner')
    search_fields = ('name', 'code')
    list_filter = ('status',)


@admin.register(FollowUp)
class FollowUpAdmin(admin.ModelAdmin):
    list_display = ('customer', 'subject', 'follow_type', 'status', 'follower', 'created_at')
    search_fields = ('subject', 'customer__name')
    list_filter = ('status', 'follow_type')


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ('user', 'destination', 'start_date', 'end_date', 'estimated_cost', 'status')
    list_filter = ('status',)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('user', 'expense_type', 'amount', 'expense_date', 'status')
    list_filter = ('status', 'expense_type')


@admin.register(Drug)
class DrugAdmin(admin.ModelAdmin):
    list_display = ('code', 'generic_name', 'drug_category', 'network_price', 'is_standard')
    search_fields = ('code', 'generic_name')
    list_filter = ('drug_category',)


@admin.register(Pharmacy)
class PharmacyAdmin(admin.ModelAdmin):
    list_display = ('pharmacy_code', 'pharmacy_name', 'medical_insurance_code', 'district')
    search_fields = ('pharmacy_name', 'pharmacy_code')


@admin.register(PharmaceuticalCompany)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('company_code', 'company_name', 'contact_person', 'phone')
    search_fields = ('company_name', 'company_code')


@admin.register(PharmacyRecord)
class PharmacyRecordAdmin(admin.ModelAdmin):
    list_display = ('pharmacy', 'drug', 'record_price', 'record_date', 'status')
    list_filter = ('status',)


@admin.register(CompanyRecord)
class CompanyRecordAdmin(admin.ModelAdmin):
    list_display = ('company', 'drug', 'declared_price', 'record_date', 'status')
    list_filter = ('status',)
