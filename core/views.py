from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.core.paginator import Paginator
from django.db.models import Q
from django.urls import reverse
from datetime import datetime
import pandas as pd
import io

from .models import (
    User, Pharmacy, PharmaceuticalCompany, Drug,
    PharmacyRecord, CompanyRecord, DrugRecordStatus
)
from .price_calculator import (
    extract_number, process_all_drugs, get_dosage_ratio,
    is_oral_normal_dosage, get_no_sugar_ratio
)


def is_yaoshisuo(user):
    return user.is_authenticated and user.user_type == 'yaoshisuo'


def is_yaodian(user):
    return user.is_authenticated and user.user_type == 'yaodian'


def is_yaoqi(user):
    return user.is_authenticated and user.user_type == 'yaoqi'


def is_quxian(user):
    return user.is_authenticated and user.user_type == 'quxian'


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


def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        user_type = request.POST.get('user_type')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        district = request.POST.get('district', '')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, '用户名已存在')
            return redirect('register')
        
        if password != confirm_password:
            messages.error(request, '两次密码输入不一致')
            return redirect('register')
        
        if not user_type:
            messages.error(request, '请选择用户类型')
            return redirect('register')
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            user_type=user_type,
            phone=phone,
            district=district,
        )
        
        messages.success(request, '注册成功，请登录')
        return redirect('login')
    
    return render(request, 'core/register.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    user = request.user
    context = {'user': user}
    
    if user.user_type == 'yaoshisuo':
        context['drug_count'] = Drug.objects.count()
        context['pharmacy_count'] = Pharmacy.objects.count()
        context['company_count'] = PharmaceuticalCompany.objects.count()
        context['abnormal_count'] = Drug.objects.filter(
            Q(price_diff__gt=0) | Q(network_price__gt=0)
        ).exclude(price_diff=0).count()
    elif user.user_type == 'yaodian':
        pharmacy = user.pharmacies.first()
        if pharmacy:
            context['pharmacy'] = pharmacy
            context['record_count'] = PharmacyRecord.objects.filter(pharmacy=pharmacy).count()
    elif user.user_type == 'yaoqi':
        company = user.companies.first()
        if company:
            context['company'] = company
            context['record_count'] = CompanyRecord.objects.filter(company=company).count()
    elif user.user_type == 'quxian':
        context['pending_count'] = PharmacyRecord.objects.filter(
            status=DrugRecordStatus.SUBMITTED,
            pharmacy__district=user.district
        ).count()
    
    return render(request, 'core/dashboard.html', context)


@user_passes_test(is_yaoshisuo)
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
    
    return render(request, 'core/yaoshisuo/drug_list.html', {'page_obj': page_obj})


@user_passes_test(is_yaoshisuo)
def calculate_ratio(request):
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
                'spec_package': drug.spec_package,
                'content': drug.content,
                'content_unit': drug.content_unit,
                'volume': drug.volume,
                'volume_unit': drug.volume_unit,
                'quantity': drug.quantity,
                'quantity_unit': drug.quantity_unit,
                'usage_days': drug.usage_days,
                'standard_holder': drug.standard_holder,
                'catalog_name': drug.catalog_name,
                'special_note': drug.special_note,
                'network_price': drug.network_price,
                'anchor_price': drug.anchor_price,
            })
        
        drug_list = process_all_drugs(drug_list, basis=basis)
        
        for drug_data in drug_list:
            Drug.objects.filter(id=drug_data['id']).update(
                is_standard=drug_data.get('is_standard', False),
                standard_price=drug_data.get('standard_price', 0),
                price_diff=drug_data.get('price_diff', 0),
                unit_value=drug_data.get('unit_value', 0),
            )
        
        messages.success(request, f'差比价计算完成，共处理 {len(drug_list)} 条药品数据')
        return redirect('drug_list')
    
    return render(request, 'core/yaoshisuo/calculate_ratio.html')


@user_passes_test(is_yaoshisuo)
def import_drugs(request):
    if request.method == 'POST':
        excel_file = request.FILES.get('excel_file')
        if not excel_file:
            messages.error(request, '请选择文件')
            return redirect('import_drugs')
        
        try:
            df = pd.read_excel(excel_file)
            
            required_cols = ['统编代码', '药品分类', '通用名']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                messages.error(request, f'缺少必要列: {", ".join(missing_cols)}')
                return redirect('import_drugs')
            
            for _, row in df.iterrows():
                drug, created = Drug.objects.update_or_create(
                    code=str(row.get('统编代码', '')),
                    defaults={
                        'drug_category': str(row.get('药品分类', '')),
                        'generic_name': str(row.get('通用名', '')),
                        'catalog_dosage_form': str(row.get('目录剂型', '')),
                        'spec_package': str(row.get('规格包装', '')),
                        'content': str(row.get('含量', '')),
                        'content_unit': str(row.get('含量单位', '')),
                        'volume': str(row.get('装量', '')),
                        'volume_unit': str(row.get('装量单位', '')),
                        'quantity': str(row.get('计价数量', '')),
                        'quantity_unit': str(row.get('计价数量单位', '')),
                        'usage_days': str(row.get('服用天数', '')),
                        'standard_holder': str(row.get('标化持有人', '')),
                        'catalog_name': str(row.get('医保目录名', '')),
                        'special_note': str(row.get('特殊标注', '')),
                        'network_price': extract_number(row.get('挂网价', 0)),
                    }
                )
            
            messages.success(request, f'成功导入 {len(df)} 条药品数据')
        except Exception as e:
            messages.error(request, f'导入失败: {str(e)}')
        
        return redirect('drug_list')
    
    return render(request, 'core/yaoshisuo/import_drugs.html')


@user_passes_test(is_yaoshisuo)
def import_anchor_price(request):
    if request.method == 'POST':
        excel_file = request.FILES.get('excel_file')
        if not excel_file:
            messages.error(request, '请选择文件')
            return redirect('import_anchor_price')
        
        try:
            df = pd.read_excel(excel_file)
            
            for _, row in df.iterrows():
                code = str(row.get('统编代码', ''))
                anchor_price = extract_number(row.get('锚点价格', 0))
                ratio = extract_number(row.get('倍率', 1))
                
                Drug.objects.filter(code=code).update(
                    anchor_price=anchor_price,
                    anchor_price_ratio=ratio,
                )
            
            messages.success(request, f'成功导入 {len(df)} 条锚点价格')
        except Exception as e:
            messages.error(request, f'导入失败: {str(e)}')
        
        return redirect('drug_list')
    
    return render(request, 'core/yaoshisuo/import_anchor_price.html')


@user_passes_test(is_yaoshisuo)
def pharmacy_list(request):
    pharmacies = Pharmacy.objects.all()
    
    code = request.GET.get('code')
    name = request.GET.get('name')
    district = request.GET.get('district')
    
    if code:
        pharmacies = pharmacies.filter(pharmacy_code__icontains=code)
    if name:
        pharmacies = pharmacies.filter(pharmacy_name__icontains=name)
    if district:
        pharmacies = pharmacies.filter(district=district)
    
    paginator = Paginator(pharmacies, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'core/yaoshisuo/pharmacy_list.html', {'page_obj': page_obj})


@user_passes_test(is_yaoshisuo)
def pharmacy_import(request):
    if request.method == 'POST':
        excel_file = request.FILES.get('excel_file')
        if not excel_file:
            messages.error(request, '请选择文件')
            return redirect('pharmacy_import')
        
        try:
            df = pd.read_excel(excel_file)
            
            for _, row in df.iterrows():
                Pharmacy.objects.update_or_create(
                    pharmacy_code=str(row.get('药店编码', '')),
                    defaults={
                        'pharmacy_name': str(row.get('药店名称', '')),
                        'medical_insurance_code': str(row.get('药店医保编码', '')),
                        'district': str(row.get('注册区县', '')),
                    }
                )
            
            messages.success(request, f'成功导入 {len(df)} 条药店数据')
        except Exception as e:
            messages.error(request, f'导入失败: {str(e)}')
        
        return redirect('pharmacy_list')
    
    return render(request, 'core/yaoshisuo/pharmacy_import.html')


@user_passes_test(is_yaoshisuo)
def company_list(request):
    companies = PharmaceuticalCompany.objects.all()
    
    code = request.GET.get('code')
    name = request.GET.get('name')
    
    if code:
        companies = companies.filter(company_code__icontains=code)
    if name:
        companies = companies.filter(company_name__icontains=name)
    
    paginator = Paginator(companies, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'core/yaoshisuo/company_list.html', {'page_obj': page_obj})


@user_passes_test(is_yaoshisuo)
def company_import(request):
    if request.method == 'POST':
        excel_file = request.FILES.get('excel_file')
        if not excel_file:
            messages.error(request, '请选择文件')
            return redirect('company_import')
        
        try:
            df = pd.read_excel(excel_file)
            
            for _, row in df.iterrows():
                PharmaceuticalCompany.objects.update_or_create(
                    company_code=str(row.get('机构编码', '')),
                    defaults={
                        'company_name': str(row.get('企业名称', '')),
                    }
                )
            
            messages.success(request, f'成功导入 {len(df)} 条药企数据')
        except Exception as e:
            messages.error(request, f'导入失败: {str(e)}')
        
        return redirect('company_list')
    
    return render(request, 'core/yaoshisuo/company_import.html')


@user_passes_test(is_yaoshisuo)
def pharmacy_record_review(request):
    records = PharmacyRecord.objects.filter(
        status__in=[DrugRecordStatus.SUBMITTED, DrugRecordStatus.UNDER_REVIEW]
    ).select_related('pharmacy', 'drug')
    
    status_filter = request.GET.get('status')
    if status_filter:
        records = records.filter(status=status_filter)
    
    paginator = Paginator(records, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    if request.method == 'POST':
        record_id = request.POST.get('record_id')
        action = request.POST.get('action')
        
        record = get_object_or_404(PharmacyRecord, id=record_id)
        
        if action == 'approve':
            record.status = DrugRecordStatus.APPROVED
        elif action == 'reject':
            record.status = DrugRecordStatus.REJECTED
        
        record.reviewed_by = request.user
        record.reviewed_at = datetime.now()
        record.save()
        
        messages.success(request, f'审核完成')
        return redirect('pharmacy_record_review')
    
    return render(request, 'core/yaoshisuo/pharmacy_record_review.html', {'page_obj': page_obj})


@user_passes_test(is_yaodian)
def pharmacy_record_submit(request):
    pharmacy = request.user.pharmacies.first()
    if not pharmacy:
        messages.error(request, '您还没有关联药店')
        return redirect('dashboard')
    
    if request.method == 'POST':
        excel_file = request.FILES.get('excel_file')
        if not excel_file:
            messages.error(request, '请选择文件')
            return redirect('pharmacy_record_submit')
        
        try:
            df = pd.read_excel(excel_file)
            
            record_date = request.POST.get('record_date')
            if not record_date:
                record_date = datetime.now().date()
            else:
                record_date = datetime.strptime(record_date, '%Y-%m-%d').date()
            
            success_count = 0
            for _, row in df.iterrows():
                code = str(row.get('统编代码', ''))
                record_price = extract_number(row.get('备案价', 0))
                
                try:
                    drug = Drug.objects.get(code=code)
                except Drug.DoesNotExist:
                    continue
                
                if record_price > drug.network_price * Decimal('1.15'):
                    messages.warning(request, f'药品 {code} 备案价高于挂网价1.15倍，无法提交')
                    continue
                if record_price < drug.network_price / Decimal('1.3'):
                    messages.warning(request, f'药品 {code} 备案价低于挂网价/1.3，无法提交')
                    continue
                
                PharmacyRecord.objects.update_or_create(
                    pharmacy=pharmacy,
                    drug=drug,
                    record_date=record_date,
                    defaults={
                        'record_price': record_price,
                        'status': DrugRecordStatus.SUBMITTED,
                    }
                )
                success_count += 1
            
            messages.success(request, f'成功提交 {success_count} 条备案记录')
        except Exception as e:
            messages.error(request, f'提交失败: {str(e)}')
        
        return redirect('pharmacy_record_list')
    
    return render(request, 'core/yaodian/record_submit.html')


@user_passes_test(is_yaodian)
def pharmacy_record_list(request):
    pharmacy = request.user.pharmacies.first()
    if not pharmacy:
        messages.error(request, '您还没有关联药店')
        return redirect('dashboard')
    
    records = PharmacyRecord.objects.filter(pharmacy=pharmacy).select_related('drug')
    
    code = request.GET.get('code')
    generic_name = request.GET.get('generic_name')
    status_filter = request.GET.get('status')
    
    if code:
        records = records.filter(drug__code__icontains=code)
    if generic_name:
        records = records.filter(drug__generic_name__icontains=generic_name)
    if status_filter:
        records = records.filter(status=status_filter)
    
    paginator = Paginator(records, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'core/yaodian/record_list.html', {'page_obj': page_obj})


@user_passes_test(is_yaoqi)
def company_record_submit(request):
    company = request.user.companies.first()
    if not company:
        messages.error(request, '您还没有关联药企')
        return redirect('dashboard')
    
    if request.method == 'POST':
        excel_file = request.FILES.get('excel_file')
        if not excel_file:
            messages.error(request, '请选择文件')
            return redirect('company_record_submit')
        
        try:
            df = pd.read_excel(excel_file)
            
            record_date = request.POST.get('record_date')
            if not record_date:
                record_date = datetime.now().date()
            else:
                record_date = datetime.strptime(record_date, '%Y-%m-%d').date()
            
            for _, row in df.iterrows():
                code = str(row.get('统编代码', ''))
                declared_price = extract_number(row.get('申报价', 0))
                
                try:
                    drug = Drug.objects.get(code=code)
                except Drug.DoesNotExist:
                    continue
                
                CompanyRecord.objects.update_or_create(
                    company=company,
                    drug=drug,
                    record_date=record_date,
                    defaults={
                        'declared_price': declared_price,
                        'status': DrugRecordStatus.SUBMITTED,
                    }
                )
            
            messages.success(request, f'成功提交 {len(df)} 条申报记录')
        except Exception as e:
            messages.error(request, f'提交失败: {str(e)}')
        
        return redirect('company_record_list')
    
    return render(request, 'core/yaoqi/record_submit.html')


@user_passes_test(is_yaoqi)
def company_record_list(request):
    company = request.user.companies.first()
    if not company:
        messages.error(request, '您还没有关联药企')
        return redirect('dashboard')
    
    records = CompanyRecord.objects.filter(company=company).select_related('drug')
    
    code = request.GET.get('code')
    generic_name = request.GET.get('generic_name')
    status_filter = request.GET.get('status')
    
    if code:
        records = records.filter(drug__code__icontains=code)
    if generic_name:
        records = records.filter(drug__generic_name__icontains=generic_name)
    if status_filter:
        records = records.filter(status=status_filter)
    
    paginator = Paginator(records, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'core/yaoqi/record_list.html', {'page_obj': page_obj})


@user_passes_test(is_quxian)
def district_record_review(request):
    records = PharmacyRecord.objects.filter(
        pharmacy__district=request.user.district,
        status__in=[DrugRecordStatus.SUBMITTED, DrugRecordStatus.UNDER_REVIEW]
    ).select_related('pharmacy', 'drug')
    
    paginator = Paginator(records, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    if request.method == 'POST':
        record_id = request.POST.get('record_id')
        action = request.POST.get('action')
        
        record = get_object_or_404(PharmacyRecord, id=record_id)
        
        if action == 'approve':
            record.status = DrugRecordStatus.APPROVED
        elif action == 'reject':
            record.status = DrugRecordStatus.REJECTED
        
        record.reviewed_by = request.user
        record.reviewed_at = datetime.now()
        record.save()
        
        messages.success(request, f'审核完成')
        return redirect('district_record_review')
    
    return render(request, 'core/quxian/record_review.html', {'page_obj': page_obj})
