from django.db import models
from django.contrib.auth.models import AbstractUser
from decimal import Decimal


class User(AbstractUser):
    USER_TYPE_CHOICES = [
        ('admin', '系统管理员'),
        ('supervisor', '药事所监督科'),
        ('drug_section', '药事所药品科'),
        ('pharmacy', '药店'),
        ('company', '药企'),
        ('district', '区县医保局'),
    ]
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, verbose_name='用户类型')
    phone = models.CharField(max_length=20, blank=True, verbose_name='联系电话')
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    organization = models.CharField(max_length=200, blank=True, verbose_name='所属机构')
    medical_insurance_code = models.CharField(max_length=50, blank=True, verbose_name='医保编码')

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'


class Department(models.Model):
    name = models.CharField(max_length=100, verbose_name='部门名称')
    code = models.CharField(max_length=50, unique=True, verbose_name='部门编码')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_depts')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '部门'
        verbose_name_plural = '部门'

    def __str__(self):
        return self.name


class Role(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name='角色名称')
    code = models.CharField(max_length=50, unique=True, verbose_name='角色编码')
    permissions = models.ManyToManyField('Permission', blank=True, related_name='roles')
    description = models.TextField(blank=True, verbose_name='描述')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '角色'
        verbose_name_plural = '角色'

    def __str__(self):
        return self.name


class Permission(models.Model):
    name = models.CharField(max_length=50, verbose_name='权限名称')
    code = models.CharField(max_length=50, unique=True, verbose_name='权限编码')
    module = models.CharField(max_length=50, verbose_name='所属模块')
    description = models.TextField(blank=True, verbose_name='描述')

    class Meta:
        verbose_name = '权限'
        verbose_name_plural = '权限'

    def __str__(self):
        return self.name


class CustomerStatus(models.TextChoices):
    POTENTIAL = '潜在', '潜在'
    FOLLOWING = '跟进中', '跟进中'
    OPPORTUNITY = '商机', '商机'
    WIN = '成交', '成交'
    LOST = '流失', '流失'


class CustomerSource(models.TextChoices):
    REFERAL = '推荐', '推荐'
    COLD_CALL = '电话营销', '电话营销'
    EXHIBITION = '展会', '展会'
    ONLINE = '网络推广', '网络推广'
    OTHER = '其他', '其他'


class Customer(models.Model):
    name = models.CharField(max_length=200, verbose_name='客户名称')
    code = models.CharField(max_length=50, unique=True, verbose_name='客户编码')
    industry = models.CharField(max_length=100, blank=True, verbose_name='行业')
    level = models.CharField(max_length=50, blank=True, verbose_name='客户级别')
    status = models.CharField(max_length=20, choices=CustomerStatus.choices, default=CustomerStatus.POTENTIAL, verbose_name='状态')
    source = models.CharField(max_length=20, choices=CustomerSource.choices, blank=True, verbose_name='客户来源')
    address = models.CharField(max_length=300, blank=True, verbose_name='地址')
    website = models.CharField(max_length=200, blank=True, verbose_name='网站')
    description = models.TextField(blank=True, verbose_name='描述')
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_customers')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_customers')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '客户'
        verbose_name_plural = '客户'

    def __str__(self):
        return self.name


class Contact(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='contacts')
    name = models.CharField(max_length=100, verbose_name='姓名')
    position = models.CharField(max_length=100, blank=True, verbose_name='职位')
    phone = models.CharField(max_length=20, blank=True, verbose_name='电话')
    mobile = models.CharField(max_length=20, blank=True, verbose_name='手机')
    email = models.CharField(max_length=100, blank=True, verbose_name='邮箱')
    is_primary = models.BooleanField(default=False, verbose_name='是否主要联系人')
    description = models.TextField(blank=True, verbose_name='备注')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '联系人'
        verbose_name_plural = '联系人'

    def __str__(self):
        return f"{self.name} - {self.customer.name}"


class ProjectStatus(models.TextChoices):
    DRAFT = '草稿', '草稿'
    SUBMITTED = '已提交', '已提交'
    APPROVED = '已立项', '已立项'
    IN_PROGRESS = '进行中', '进行列'
    COMPLETED = '已完成', '已完成'
    CANCELLED = '已取消', '已取消'


class Project(models.Model):
    name = models.CharField(max_length=200, verbose_name='项目名称')
    code = models.CharField(max_length=50, unique=True, verbose_name='项目编码')
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='projects')
    budget = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='预算')
    status = models.CharField(max_length=20, choices=ProjectStatus.choices, default=ProjectStatus.DRAFT, verbose_name='状态')
    start_date = models.DateField(null=True, blank=True, verbose_name='开始日期')
    end_date = models.DateField(null=True, blank=True, verbose_name='结束日期')
    description = models.TextField(blank=True, verbose_name='项目描述')
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_projects')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '项目'
        verbose_name_plural = '项目'

    def __str__(self):
        return self.name


class FollowUpType(models.TextChoices):
    PHONE = '电话', '电话'
    VISIT = '拜访', '拜访'
    EMAIL = '邮件', '邮件'
    MEETING = '会议', '会议'
    OTHER = '其他', '其他'


class FollowUpStatus(models.TextChoices):
    PENDING = '待处理', '待处理'
    IN_PROGRESS = '进行中', '进行中'
    COMPLETED = '已完成', '已完成'
    CANCELLED = '已取消', '已取消'


class FollowUp(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='follow_ups')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='follow_ups')
    follow_type = models.CharField(max_length=20, choices=FollowUpType.choices, default=FollowUpType.PHONE, verbose_name='跟进方式')
    subject = models.CharField(max_length=200, verbose_name='跟进主题')
    content = models.TextField(verbose_name='跟进内容')
    status = models.CharField(max_length=20, choices=FollowUpStatus.choices, default=FollowUpStatus.PENDING, verbose_name='状态')
    next_action = models.TextField(blank=True, verbose_name='下一步行动')
    next_date = models.DateField(null=True, blank=True, verbose_name='下次跟进日期')
    follower = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='follow_ups')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '跟进记录'
        verbose_name_plural = '跟进记录'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.customer.name} - {self.subject}"


class TripStatus(models.TextChoices):
    DRAFT = '草稿', '草稿'
    SUBMITTED = '已提交', '已提交'
    APPROVED = '已审批', '已审批'
    REJECTED = '已拒绝', '已拒绝'
    COMPLETED = '已完成', '已完成'


class Trip(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trips')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='trips')
    destination = models.CharField(max_length=200, verbose_name='出差目的地')
    purpose = models.TextField(verbose_name='出差目的')
    start_date = models.DateField(verbose_name='开始日期')
    end_date = models.DateField(verbose_name='结束日期')
    status = models.CharField(max_length=20, choices=TripStatus.choices, default=TripStatus.DRAFT, verbose_name='状态')
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='预计费用')
    actual_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='实际费用')
    notes = models.TextField(blank=True, verbose_name='备注')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '出差申请'
        verbose_name_plural = '出差申请'

    def __str__(self):
        return f"{self.user.username} - {self.destination}"


class ExpenseType(models.TextChoices):
    TRAVEL = '差旅费', '差旅费'
    ENTERTAINMENT = '招待费', '招待费'
    COMMUNICATION = '通讯费', '通讯费'
    OFFICE = '办公费', '办公费'
    OTHER = '其他', '其他'


class ExpenseStatus(models.TextChoices):
    DRAFT = '草稿', '草稿'
    SUBMITTED = '已提交', '已提交'
    APPROVED = '已审批', '已审批'
    REJECTED = '已拒绝', '已拒绝'
    REIMBURSED = '已报销', '已报销'


class Expense(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses')
    trip = models.ForeignKey(Trip, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses')
    expense_type = models.CharField(max_length=20, choices=ExpenseType.choices, verbose_name='费用类型')
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='金额')
    expense_date = models.DateField(verbose_name='费用日期')
    description = models.TextField(verbose_name='费用说明')
    receipt = models.FileField(upload_to='receipts/', null=True, blank=True, verbose_name='收据')
    status = models.CharField(max_length=20, choices=ExpenseStatus.choices, default=ExpenseStatus.DRAFT, verbose_name='状态')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '业务费用'
        verbose_name_plural = '业务费用'

    def __str__(self):
        return f"{self.user.username} - {self.expense_type} - {self.amount}"


# ==================== 药品差比价相关模型 ====================

class DrugCategory(models.TextChoices):
    CHEMICAL = '化学药品', '化学药品'
    BIOLOGICAL = '生物制品', '生物制品'
    TCM = '中成药', '中成药'


class Drug(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name='统编代码')
    drug_category = models.CharField(max_length=50, choices=DrugCategory.choices, verbose_name='药品分类')
    generic_name = models.CharField(max_length=200, verbose_name='通用名')
    catalog_dosage_form = models.CharField(max_length=100, blank=True, verbose_name='目录剂型')
    spec_package = models.CharField(max_length=200, blank=True, verbose_name='规格包装')
    content = models.CharField(max_length=50, blank=True, verbose_name='含量')
    content_unit = models.CharField(max_length=20, blank=True, verbose_name='含量单位')
    volume = models.CharField(max_length=50, blank=True, verbose_name='装量')
    volume_unit = models.CharField(max_length=20, blank=True, verbose_name='装量单位')
    quantity = models.CharField(max_length=50, blank=True, verbose_name='计价数量')
    quantity_unit = models.CharField(max_length=20, blank=True, verbose_name='计价数量单位')
    usage_days = models.CharField(max_length=50, blank=True, verbose_name='服用天数')
    standard_holder = models.CharField(max_length=200, blank=True, verbose_name='标化持有人')
    catalog_name = models.CharField(max_length=200, blank=True, verbose_name='医保目录名')
    special_note = models.CharField(max_length=200, blank=True, verbose_name='特殊标注')
    network_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='挂网价')
    anchor_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='锚点价格')
    is_standard = models.BooleanField(default=False, verbose_name='是否标准品')
    standard_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='差比价')
    price_diff = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='价差对比')

    class Meta:
        verbose_name = '药品'
        verbose_name_plural = '药品'

    def __str__(self):
        return f"{self.generic_name} ({self.code})"


class Pharmacy(models.Model):
    pharmacy_code = models.CharField(max_length=50, unique=True, verbose_name='药店编码')
    pharmacy_name = models.CharField(max_length=200, verbose_name='药店名称')
    medical_insurance_code = models.CharField(max_length=50, verbose_name='医保编码')
    district = models.CharField(max_length=50, verbose_name='区县')
    address = models.CharField(max_length=300, blank=True, verbose_name='地址')
    phone = models.CharField(max_length=20, blank=True, verbose_name='电话')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '药店'
        verbose_name_plural = '药店'

    def __str__(self):
        return self.pharmacy_name


class PharmaceuticalCompany(models.Model):
    company_code = models.CharField(max_length=50, unique=True, verbose_name='机构编码')
    company_name = models.CharField(max_length=200, verbose_name='企业名称')
    contact_person = models.CharField(max_length=100, blank=True, verbose_name='联系人')
    phone = models.CharField(max_length=20, blank=True, verbose_name='电话')
    address = models.CharField(max_length=300, blank=True, verbose_name='地址')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '药企'
        verbose_name_plural = '药企'

    def __str__(self):
        return self.company_name


class DrugRecordStatus(models.TextChoices):
    NORMAL = '正常', '正常'
    ABNORMAL = '异常', '异常'
    PENDING = '待整改', '待整改'
    SUBMITTED = '已提交', '已提交'
    UNDER_REVIEW = '待审核', '待审核'
    APPROVED = '审核通过', '审核通过'
    REJECTED = '审核不通过', '审核不通过'


class PharmacyRecord(models.Model):
    pharmacy = models.ForeignKey(Pharmacy, on_delete=models.CASCADE, related_name='records')
    drug = models.ForeignKey(Drug, on_delete=models.CASCADE, related_name='pharmacy_records')
    record_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='备案价')
    record_date = models.DateField(verbose_name='数据年月')
    status = models.CharField(max_length=20, choices=DrugRecordStatus.choices, default=DrugRecordStatus.SUBMITTED, verbose_name='状态')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '药店备案价'
        verbose_name_plural = '药店备案价'


class CompanyRecord(models.Model):
    company = models.ForeignKey(PharmaceuticalCompany, on_delete=models.CASCADE, related_name='records')
    drug = models.ForeignKey(Drug, on_delete=models.CASCADE, related_name='company_records')
    declared_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='申报价')
    record_date = models.DateField(verbose_name='数据年月')
    status = models.CharField(max_length=20, choices=DrugRecordStatus.choices, default=DrugRecordStatus.SUBMITTED, verbose_name='状态')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '药企申报价'
        verbose_name_plural = '药企申报价'


class AnchorPrice(models.Model):
    drug = models.ForeignKey(Drug, on_delete=models.CASCADE, related_name='anchor_prices')
    anchor_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='锚点价格')
    adjust_ratio = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('1.0'), verbose_name='调整倍率')
    target_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='治理价格')
    record_date = models.DateField(verbose_name='数据年月')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='创建人')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '锚点价格'
        verbose_name_plural = '锚点价格'

    def save(self, *args, **kwargs):
        self.target_price = round(self.anchor_price * self.adjust_ratio, 2)
        super().save(*args, **kwargs)


class PharmacyUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='pharmacy_profile')
    pharmacy = models.ForeignKey(Pharmacy, on_delete=models.CASCADE, related_name='users')

    class Meta:
        verbose_name = '药店用户'
        verbose_name_plural = '药店用户'


class CompanyUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='company_profile')
    company = models.ForeignKey(PharmaceuticalCompany, on_delete=models.CASCADE, related_name='users')

    class Meta:
        verbose_name = '药企用户'
        verbose_name_plural = '药企用户'


class District(models.Model):
    name = models.CharField(max_length=100, verbose_name='区县名称')
    code = models.CharField(max_length=50, unique=True, verbose_name='区县编码')

    class Meta:
        verbose_name = '区县'
        verbose_name_plural = '区县'

    def __str__(self):
        return self.name


class PharmacyRecordReview(models.Model):
    pharmacy_record = models.ForeignKey(PharmacyRecord, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='审核人')
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, verbose_name='审核区县')
    status = models.CharField(max_length=20, choices=DrugRecordStatus.choices, default=DrugRecordStatus.UNDER_REVIEW, verbose_name='审核状态')
    comment = models.TextField(blank=True, verbose_name='审核意见')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '药店备案价审核'
        verbose_name_plural = '药店备案价审核'


class DrugPriceReview(models.Model):
    drug = models.ForeignKey(Drug, on_delete=models.CASCADE, related_name='price_reviews')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='审核人')
    original_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='原价格')
    proposed_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='整改价格')
    status = models.CharField(max_length=20, choices=DrugRecordStatus.choices, default=DrugRecordStatus.PENDING, verbose_name='审核状态')
    comment = models.TextField(blank=True, verbose_name='审核意见')
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name='审核时间')

    class Meta:
        verbose_name = '药品挂网价审核'
        verbose_name_plural = '药品挂网价审核'
