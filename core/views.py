from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from datetime import datetime, date
import pandas as pd

from .models import (
    User, Department, Role, Permission,
    Customer, Contact, Project, FollowUp,
    Trip, Expense, Drug, Pharmacy, PharmaceuticalCompany,
    PharmacyRecord, CompanyRecord, DrugRecordStatus
)
from .price_calculator import extract_number, process_all_drugs


# ==================== 认证相关 ====================

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, '用户名或密码错误')
    return render(request, 'core/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, '用户名已存在')
            return redirect('register')
        
        if password != confirm_password:
            messages.error(request, '两次密码输入不一致')
            return redirect('register')
        
        user = User.objects.create_user(
            username=username, email=email, password=password,
            phone=phone, user_type='sales'
        )
        messages.success(request, '注册成功，请登录')
        return redirect('login')
    
    return render(request, 'core/register.html')


# ==================== 首页和仪表盘 ====================

@login_required
def dashboard(request):
    user = request.user
    context = {
        'user': user,
        'customer_count': Customer.objects.count(),
        'project_count': Project.objects.count(),
        'followup_count': FollowUp.objects.count(),
        'expense_count': Expense.objects.count(),
        'drug_count': Drug.objects.count(),
    }
    return render(request, 'core/dashboard.html', context)


# ==================== 系统管理 ====================

@login_required
def user_list(request):
    users = User.objects.all().select_related('department')
    return render(request, 'core/system/user_list.html', {'page_obj': users})


@login_required
def user_create(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        user_type = request.POST.get('user_type')
        phone = request.POST.get('phone')
        department_id = request.POST.get('department')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, '用户名已存在')
            return redirect('user_create')
        
        department = Department.objects.get(id=department_id) if department_id else None
        User.objects.create_user(
            username=username, email=email, password=password,
            user_type=user_type, phone=phone, department=department
        )
        messages.success(request, '用户创建成功')
        return redirect('user_list')
    
    departments = Department.objects.all()
    return render(request, 'core/system/user_form.html', {'departments': departments})


@login_required
def role_list(request):
    roles = Role.objects.all()
    return render(request, 'core/system/role_list.html', {'page_obj': roles})


@login_required
def role_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        code = request.POST.get('code')
        description = request.POST.get('description')
        
        role = Role.objects.create(name=name, code=code, description=description)
        
        perm_ids = request.POST.getlist('permissions')
        role.permissions.set(Permission.objects.filter(id__in=perm_ids))
        
        messages.success(request, '角色创建成功')
        return redirect('role_list')
    
    permissions = Permission.objects.all()
    return render(request, 'core/system/role_form.html', {'permissions': permissions})


@login_required
def department_list(request):
    departments = Department.objects.all().select_related('parent', 'manager')
    return render(request, 'core/system/department_list.html', {'page_obj': departments})


@login_required
def department_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        code = request.POST.get('code')
        parent_id = request.POST.get('parent')
        manager_id = request.POST.get('manager')
        
        parent = Department.objects.get(id=parent_id) if parent_id else None
        manager = User.objects.get(id=manager_id) if manager_id else None
        
        Department.objects.create(name=name, code=code, parent=parent, manager=manager)
        messages.success(request, '部门创建成功')
        return redirect('department_list')
    
    departments = Department.objects.all()
    users = User.objects.all()
    return render(request, 'core/system/department_form.html', {'departments': departments, 'users': users})


# ==================== 客户管理 ====================

@login_required
def customer_list(request):
    customers = Customer.objects.all().select_related('owner')
    
    name = request.GET.get('name')
    status = request.GET.get('status')
    source = request.GET.get('source')
    
    if name:
        customers = customers.filter(name__icontains=name)
    if status:
        customers = customers.filter(status=status)
    if source:
        customers = customers.filter(source=source)
    
    paginator = Paginator(customers, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'core/crm/customer_list.html', {'page_obj': page_obj})


@login_required
def customer_create(request):
    if request.method == 'POST':
        customer = Customer.objects.create(
            name=request.POST.get('name'),
            code=request.POST.get('code'),
            industry=request.POST.get('industry'),
            level=request.POST.get('level'),
            status=request.POST.get('status'),
            source=request.POST.get('source'),
            address=request.POST.get('address'),
            website=request.POST.get('website'),
            description=request.POST.get('description'),
            owner=request.user,
            created_by=request.user
        )
        
        contact_name = request.POST.get('contact_name')
        contact_phone = request.POST.get('contact_phone')
        contact_mobile = request.POST.get('contact_mobile')
        contact_email = request.POST.get('contact_email')
        if contact_name:
            Contact.objects.create(
                customer=customer, name=contact_name,
                phone=contact_phone, mobile=contact_mobile,
                email=contact_email, is_primary=True
            )
        
        messages.success(request, '客户创建成功')
        return redirect('customer_list')
    
    return render(request, 'core/crm/customer_form.html')


@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    contacts = customer.contacts.all()
    follow_ups = customer.follow_ups.all()[:10]
    projects = customer.projects.all()[:10]
    return render(request, 'core/crm/customer_detail.html', {
        'customer': customer, 'contacts': contacts,
        'follow_ups': follow_ups, 'projects': projects
    })


@login_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        customer.name = request.POST.get('name')
        customer.industry = request.POST.get('industry')
        customer.level = request.POST.get('level')
        customer.status = request.POST.get('status')
        customer.source = request.POST.get('source')
        customer.address = request.POST.get('address')
        customer.website = request.POST.get('website')
        customer.description = request.POST.get('description')
        customer.save()
        messages.success(request, '客户更新成功')
        return redirect('customer_detail', pk=pk)
    return render(request, 'core/crm/customer_form.html', {'customer': customer})


@login_required
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    customer.delete()
    messages.success(request, '客户删除成功')
    return redirect('customer_list')


# ==================== 联系人管理 ====================

@login_required
def contact_list(request):
    contacts = Contact.objects.all().select_related('customer')
    
    name = request.GET.get('name')
    customer_id = request.GET.get('customer')
    
    if name:
        contacts = contacts.filter(name__icontains=name)
    if customer_id:
        contacts = contacts.filter(customer_id=customer_id)
    
    paginator = Paginator(contacts, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'core/crm/contact_list.html', {'page_obj': page_obj})


@login_required
def contact_create(request):
    if request.method == 'POST':
        customer = get_object_or_404(Customer, pk=request.POST.get('customer'))
        Contact.objects.create(
            customer=customer,
            name=request.POST.get('name'),
            position=request.POST.get('position'),
            phone=request.POST.get('phone'),
            mobile=request.POST.get('mobile'),
            email=request.POST.get('email'),
            is_primary=request.POST.get('is_primary') == 'on',
            description=request.POST.get('description')
        )
        messages.success(request, '联系人创建成功')
        return redirect('contact_list')
    
    customers = Customer.objects.all()
    return render(request, 'core/crm/contact_form.html', {'customers': customers})


@login_required
def contact_edit(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    if request.method == 'POST':
        contact.name = request.POST.get('name')
        contact.position = request.POST.get('position')
        contact.phone = request.POST.get('phone')
        contact.mobile = request.POST.get('mobile')
        contact.email = request.POST.get('email')
        contact.is_primary = request.POST.get('is_primary') == 'on'
        contact.description = request.POST.get('description')
        contact.save()
        messages.success(request, '联系人更新成功')
        return redirect('contact_list')
    customers = Customer.objects.all()
    return render(request, 'core/crm/contact_form.html', {'contact': contact, 'customers': customers})


@login_required
def contact_delete(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    contact.delete()
    messages.success(request, '联系人删除成功')
    return redirect('contact_list')


# ==================== 项目管理 ====================

@login_required
def project_list(request):
    projects = Project.objects.all().select_related('customer', 'owner')
    
    name = request.GET.get('name')
    status = request.GET.get('status')
    customer_id = request.GET.get('customer')
    
    if name:
        projects = projects.filter(name__icontains=name)
    if status:
        projects = projects.filter(status=status)
    if customer_id:
        projects = projects.filter(customer_id=customer_id)
    
    paginator = Paginator(projects, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'core/project/project_list.html', {'page_obj': page_obj})


@login_required
def project_create(request):
    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        customer = Customer.objects.get(id=customer_id) if customer_id else None
        
        Project.objects.create(
            name=request.POST.get('name'),
            code=request.POST.get('code'),
            customer=customer,
            budget=request.POST.get('budget'),
            status=request.POST.get('status'),
            start_date=request.POST.get('start_date') or None,
            end_date=request.POST.get('end_date') or None,
            description=request.POST.get('description'),
            owner=request.user,
            created_by=request.user
        )
        messages.success(request, '项目创建成功')
        return redirect('project_list')
    
    customers = Customer.objects.all()
    return render(request, 'core/project/project_form.html', {'customers': customers})


@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    follow_ups = project.follow_ups.all()[:10]
    expenses = project.expenses.all()[:10]
    trips = project.trips.all()[:10]
    return render(request, 'core/project/project_detail.html', {
        'project': project, 'follow_ups': follow_ups,
        'expenses': expenses, 'trips': trips
    })


@login_required
def project_edit(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        project.name = request.POST.get('name')
        project.budget = request.POST.get('budget')
        project.status = request.POST.get('status')
        project.start_date = request.POST.get('start_date') or None
        project.end_date = request.POST.get('end_date') or None
        project.description = request.POST.get('description')
        project.save()
        messages.success(request, '项目更新成功')
        return redirect('project_detail', pk=pk)
    customers = Customer.objects.all()
    return render(request, 'core/project/project_form.html', {'project': project, 'customers': customers})


@login_required
def project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk)
    project.delete()
    messages.success(request, '项目删除成功')
    return redirect('project_list')


# ==================== 跟进管理 ====================

@login_required
def followup_list(request):
    follow_ups = FollowUp.objects.all().select_related('customer', 'project', 'follower')
    
    customer_id = request.GET.get('customer')
    status = request.GET.get('status')
    follow_type = request.GET.get('follow_type')
    
    if customer_id:
        follow_ups = follow_ups.filter(customer_id=customer_id)
    if status:
        follow_ups = follow_ups.filter(status=status)
    if follow_type:
        follow_ups = follow_ups.filter(follow_type=follow_type)
    
    paginator = Paginator(follow_ups, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'core/followup/followup_list.html', {'page_obj': page_obj})


@login_required
def followup_create(request):
    if request.method == 'POST':
        customer = get_object_or_404(Customer, pk=request.POST.get('customer'))
        project_id = request.POST.get('project')
        project = Project.objects.get(id=project_id) if project_id else None
        
        FollowUp.objects.create(
            customer=customer,
            project=project,
            follow_type=request.POST.get('follow_type'),
            subject=request.POST.get('subject'),
            content=request.POST.get('content'),
            status=request.POST.get('status'),
            next_action=request.POST.get('next_action'),
            next_date=request.POST.get('next_date') or None,
            follower=request.user
        )
        messages.success(request, '跟进记录创建成功')
        return redirect('followup_list')
    
    customers = Customer.objects.all()
    projects = Project.objects.all()
    return render(request, 'core/followup/followup_form.html', {'customers': customers, 'projects': projects})


@login_required
def followup_edit(request, pk):
    followup = get_object_or_404(FollowUp, pk=pk)
    if request.method == 'POST':
        followup.subject = request.POST.get('subject')
        followup.content = request.POST.get('content')
        followup.status = request.POST.get('status')
        followup.next_action = request.POST.get('next_action')
        followup.next_date = request.POST.get('next_date') or None
        followup.save()
        messages.success(request, '跟进记录更新成功')
        return redirect('followup_list')
    customers = Customer.objects.all()
    projects = Project.objects.all()
    return render(request, 'core/followup/followup_form.html', {'followup': followup, 'customers': customers, 'projects': projects})


@login_required
def followup_delete(request, pk):
    followup = get_object_or_404(FollowUp, pk=pk)
    followup.delete()
    messages.success(request, '跟进记录删除成功')
    return redirect('followup_list')


# ==================== 出差管理 ====================

@login_required
def trip_list(request):
    trips = Trip.objects.all().select_related('user', 'project')
    
    user_id = request.GET.get('user')
    status = request.GET.get('status')
    
    if user_id:
        trips = trips.filter(user_id=user_id)
    if status:
        trips = trips.filter(status=status)
    
    paginator = Paginator(trips, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'core/trip/trip_list.html', {'page_obj': page_obj})


@login_required
def trip_create(request):
    if request.method == 'POST':
        project_id = request.POST.get('project')
        project = Project.objects.get(id=project_id) if project_id else None
        
        Trip.objects.create(
            user=request.user,
            project=project,
            destination=request.POST.get('destination'),
            purpose=request.POST.get('purpose'),
            start_date=request.POST.get('start_date'),
            end_date=request.POST.get('end_date'),
            status='submitted',
            estimated_cost=request.POST.get('estimated_cost') or 0,
            notes=request.POST.get('notes')
        )
        messages.success(request, '出差申请提交成功')
        return redirect('trip_list')
    
    projects = Project.objects.all()
    return render(request, 'core/trip/trip_form.html', {'projects': projects})


@login_required
def trip_approve(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    action = request.POST.get('action')
    
    if action == 'approve':
        trip.status = 'approved'
    elif action == 'reject':
        trip.status = 'rejected'
    
    trip.save()
    messages.success(request, '审批完成')
    return redirect('trip_list')


# ==================== 业务费管理 ====================

@login_required
def expense_list(request):
    expenses = Expense.objects.all().select_related('user', 'project', 'trip')
    
    user_id = request.GET.get('user')
    status = request.GET.get('status')
    expense_type = request.GET.get('expense_type')
    
    if user_id:
        expenses = expenses.filter(user_id=user_id)
    if status:
        expenses = expenses.filter(status=status)
    if expense_type:
        expenses = expenses.filter(expense_type=expense_type)
    
    paginator = Paginator(expenses, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'core/expense/expense_list.html', {'page_obj': page_obj})


@login_required
def expense_create(request):
    if request.method == 'POST':
        project_id = request.POST.get('project')
        trip_id = request.POST.get('trip')
        
        project = Project.objects.get(id=project_id) if project_id else None
        trip = Trip.objects.get(id=trip_id) if trip_id else None
        
        Expense.objects.create(
            user=request.user,
            project=project,
            trip=trip,
            expense_type=request.POST.get('expense_type'),
            amount=request.POST.get('amount'),
            expense_date=request.POST.get('expense_date'),
            description=request.POST.get('description'),
            status='submitted'
        )
        messages.success(request, '费用申请提交成功')
        return redirect('expense_list')
    
    projects = Project.objects.all()
    trips = Trip.objects.filter(user=request.user)
    return render(request, 'core/expense/expense_form.html', {'projects': projects, 'trips': trips})


@login_required
def expense_approve(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    action = request.POST.get('action')
    
    if action == 'approve':
        expense.status = 'approved'
    elif action == 'reject':
        expense.status = 'rejected'
    
    expense.save()
    messages.success(request, '审批完成')
    return redirect('expense_list')


# ==================== 药品差比价管理 ====================

@login_required
def drug_list(request):
    drugs = Drug.objects.all()
    
    code = request.GET.get('code')
    generic_name = request.GET.get('generic_name')
    
    if code:
        drugs = drugs.filter(code__icontains=code)
    if generic_name:
        drugs = drugs.filter(generic_name__icontains=generic_name)
    
    paginator = Paginator(drugs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'core/drug/drug_list.html', {'page_obj': page_obj})


@login_required
def drug_import(request):
    if request.method == 'POST':
        excel_file = request.FILES.get('excel_file')
        if not excel_file:
            messages.error(request, '请选择文件')
            return redirect('drug_import')
        
        try:
            df = pd.read_excel(excel_file)
            
            for _, row in df.iterrows():
                Drug.objects.update_or_create(
                    code=str(row.get('统编代码', '')),
                    defaults={
                        'drug_category': str(row.get('药品分类', '')),
                        'generic_name': str(row.get('通用名', '')),
                        'catalog_dosage_form': str(row.get('目录剂型', '')),
                        'spec_package': str(row.get('规格包装', '')),
                        'content': str(row.get('含量', '')),
                        'volume': str(row.get('装量', '')),
                        'quantity': str(row.get('计价数量', '')),
                        'usage_days': str(row.get('服用天数', '')),
                        'standard_holder': str(row.get('标化持有人', '')),
                        'catalog_name': str(row.get('医保目录名', '')),
                        'network_price': extract_number(row.get('挂网价', 0)),
                    }
                )
            
            messages.success(request, f'成功导入 {len(df)} 条药品数据')
        except Exception as e:
            messages.error(request, f'导入失败: {str(e)}')
        
        return redirect('drug_list')
    
    return render(request, 'core/drug/drug_import.html')


@login_required
def drug_calculate(request):
    if request.method == 'POST':
        basis = request.POST.get('basis', 'max')
        
        drugs = Drug.objects.all()
        drug_list = []
        for drug in drugs:
            drug_list.append({
                'id': drug.id,
                'code': drug.code,
                'drug_category': drug.drug_category,
                'generic_name': drug.generic_name,
                'catalog_dosage_form': drug.catalog_dosage_form,
                'content': drug.content,
                'volume': drug.volume,
                'quantity': drug.quantity,
                'usage_days': drug.usage_days,
                'standard_holder': drug.standard_holder,
                'catalog_name': drug.catalog_name,
                'network_price': drug.network_price,
            })
        
        drug_list = process_all_drugs(drug_list, basis=basis)
        
        for drug_data in drug_list:
            Drug.objects.filter(id=drug_data['id']).update(
                is_standard=drug_data.get('is_standard', False),
                standard_price=drug_data.get('standard_price', 0),
                price_diff=drug_data.get('price_diff', 0),
            )
        
        messages.success(request, '差比价计算完成')
        return redirect('drug_list')
    
    return render(request, 'core/drug/drug_calculate.html')


@login_required
def pharmacy_list(request):
    pharmacies = Pharmacy.objects.all()
    return render(request, 'core/drug/pharmacy_list.html', {'page_obj': pharmacies})


@login_required
def pharmacy_import(request):
    if request.method == 'POST':
        excel_file = request.FILES.get('excel_file')
        df = pd.read_excel(excel_file)
        
        for _, row in df.iterrows():
            Pharmacy.objects.update_or_create(
                pharmacy_code=str(row.get('药店编码', '')),
                defaults={
                    'pharmacy_name': str(row.get('药店名称', '')),
                    'medical_insurance_code': str(row.get('医保编码', '')),
                    'district': str(row.get('区县', '')),
                    'address': str(row.get('地址', '')),
                }
            )
        
        messages.success(request, f'成功导入 {len(df)} 条药店数据')
        return redirect('pharmacy_list')
    
    return render(request, 'core/drug/pharmacy_import.html')


@login_required
def company_list(request):
    companies = PharmaceuticalCompany.objects.all()
    return render(request, 'core/drug/company_list.html', {'page_obj': companies})


@login_required
def company_import(request):
    if request.method == 'POST':
        excel_file = request.FILES.get('excel_file')
        df = pd.read_excel(excel_file)
        
        for _, row in df.iterrows():
            PharmaceuticalCompany.objects.update_or_create(
                company_code=str(row.get('机构编码', '')),
                defaults={
                    'company_name': str(row.get('企业名称', '')),
                    'contact_person': str(row.get('联系人', '')),
                    'phone': str(row.get('电话', '')),
                }
            )
        
        messages.success(request, f'成功导入 {len(df)} 条药企数据')
        return redirect('company_list')
    
    return render(request, 'core/drug/company_import.html')
