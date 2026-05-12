import math
import re
from decimal import Decimal, getcontext
from typing import List, Dict, Optional

getcontext().prec = 28


def _pow(base, exponent):
    """计算 base^exponent，返回 Decimal"""
    return Decimal(str(float(base) ** float(exponent)))


def _log2_pow(base, value):
    """计算 base^log2(value)，返回 Decimal"""
    if float(value) <= 0:
        return Decimal('1')
    return Decimal(str(float(base) ** math.log2(float(value))))


DOSAGE_FORM_RATIO = {
    "普通片": Decimal('1.0'),
    "咀嚼片": Decimal('1.05'),
    "含片": Decimal('1.05'),
    "可溶片": Decimal('1.05'),
    "肠溶片": Decimal('1.1'),
    "分散片": Decimal('1.2'),
    "泡腾片": Decimal('1.3'),
    "硬胶囊": Decimal('1.0'),
    "肠溶胶囊": Decimal('1.1'),
    "软胶囊": Decimal('1.2'),
}

ORAL_NORMAL_DOSAGE_KEYWORDS = ["口服常释剂", "缓释控释剂型"]

NO_SUGAR_KEYWORDS = ["无蔗糖", "无糖"]

DOSAGE_FORM_KEYWORDS = [
    "普通片", "咀嚼片", "含片", "可溶片", "肠溶片", "分散片", "泡腾片",
    "硬胶囊", "肠溶胶囊", "软胶囊",
    "片", "胶囊",
]


def extract_number(text):
    if text is None:
        return Decimal('0')
    text = str(text).strip()
    if text == "" or text.lower() == "nan":
        return Decimal('0')
    match = re.search(r'\d+\.?\d*', text)
    if match:
        return Decimal(match.group())
    return Decimal('0')


def get_dosage_ratio(description_dosage_form):
    """从表述剂型获取剂型比值"""
    if description_dosage_form is None or str(description_dosage_form).strip() == "":
        return Decimal('1.0')
    dosage_form = str(description_dosage_form)
    for key, ratio in DOSAGE_FORM_RATIO.items():
        if key in dosage_form:
            return ratio
    return Decimal('1.0')


def is_oral_normal_dosage(catalog_dosage_form):
    """判断目录剂型是否为口服常释剂或缓释控释剂型
    '口服常释剂型（不含分散片）'不视为口服常释剂型
    """
    if catalog_dosage_form is None or str(catalog_dosage_form).strip() == "":
        return False
    dosage_form = str(catalog_dosage_form)
    if '不含分散片' in dosage_form:
        return False
    return any(keyword in dosage_form for keyword in ORAL_NORMAL_DOSAGE_KEYWORDS)


def get_no_sugar_ratio(spec_package):
    """获取无蔗糖/无糖系数"""
    if spec_package is None:
        return Decimal('1.0')
    text = str(spec_package)
    if any(keyword in text for keyword in NO_SUGAR_KEYWORDS):
        return Decimal('1.1')
    return Decimal('1.0')


def normalize_generic_name(name):
    """标准化通用名（去除剂型、数字、字母信息）"""
    name = re.sub(r'[0-9IVXLCDM]+', '', name, flags=re.IGNORECASE)
    name = re.sub(r'[a-zA-Z]+', '', name)
    sorted_keywords = sorted(DOSAGE_FORM_KEYWORDS, key=len, reverse=True)
    for keyword in sorted_keywords:
        name = name.replace(keyword, '')
    return name.strip()


def _safe_get(drug, *keys):
    """从字典中安全获取值，支持多个键名"""
    for key in keys:
        val = drug.get(key)
        if val is not None:
            return val
    return ""


def get_quantity_coeff(catalog_dosage_form):
    """获取计价数量系数：口服常释剂/缓释控释剂型用1.95，其余用2.0"""
    return Decimal('1.95') if is_oral_normal_dosage(catalog_dosage_form) else Decimal('2.0')


def calculate_western_unit_value(drug):
    """
    西药标准品标记公式（单体差比值）：
    含量>0: 1.7^LOG(1/含量,2) * coeff^LOG(1/计价数量,2) * 挂网价
    含量=0,装量>0: 1.9^LOG(1/装量,2) * coeff^LOG(1/计价数量,2) * 挂网价
    含量=0,装量=0: coeff^LOG(1/计价数量,2) * 挂网价
    注：标准品标记时不除以剂型比值
    """
    content = extract_number(drug.get("content", 0))
    quantity = extract_number(drug.get("quantity", 0))
    price = extract_number(drug.get("network_price", 0))
    volume = extract_number(drug.get("volume", 0))
    catalog_dosage = str(_safe_get(drug, "catalog_dosage_form", "目录剂型"))

    coeff = get_quantity_coeff(catalog_dosage)

    if content > 0 and quantity > 0:
        return (_log2_pow(Decimal('1.7'), 1 / content) *
                _log2_pow(coeff, 1 / quantity) * price)
    elif volume > 0 and quantity > 0:
        return (_log2_pow(Decimal('1.9'), 1 / volume) *
                _log2_pow(coeff, 1 / quantity) * price)
    elif quantity > 0:
        return _log2_pow(coeff, 1 / quantity) * price
    else:
        return Decimal('inf')


def calculate_western_ratio_price(drug, standard_drug):
    """
    西药差比价计算公式：
    含量>0: 1.7^LOG(自身含量/标准品含量,2) * coeff^LOG(自身计价数量/标准品计价数量,2) * 标准品挂网价
    含量=0,装量>0: 1.9^LOG(自身装量/标准品装量,2) * coeff^LOG(自身计价数量/标准品计价数量,2) * 标准品挂网价
    含量=0,装量=0: coeff^LOG(自身计价数量/标准品计价数量,2) * 标准品挂网价
    """
    content = extract_number(drug.get("content", 0))
    quantity = extract_number(drug.get("quantity", 0))
    volume = extract_number(drug.get("volume", 0))
    std_content = extract_number(standard_drug.get("content", 0))
    std_quantity = extract_number(standard_drug.get("quantity", 0))
    std_volume = extract_number(standard_drug.get("volume", 0))
    std_price = extract_number(standard_drug.get("network_price", 0))
    catalog_dosage = str(_safe_get(drug, "catalog_dosage_form", "目录剂型"))

    coeff = get_quantity_coeff(catalog_dosage)

    if content > 0 and std_content > 0 and quantity > 0 and std_quantity > 0:
        ratio_price = (_log2_pow(Decimal('1.7'), content / std_content) *
                       _log2_pow(coeff, quantity / std_quantity) *
                       std_price)
    elif volume > 0 and std_volume > 0 and quantity > 0 and std_quantity > 0:
        ratio_price = (_log2_pow(Decimal('1.9'), volume / std_volume) *
                       _log2_pow(coeff, quantity / std_quantity) *
                       std_price)
    elif quantity > 0 and std_quantity > 0:
        ratio_price = (_log2_pow(coeff, quantity / std_quantity) *
                       std_price)
    else:
        return None

    return round(ratio_price, 2)


def calculate_tcm_unit_value(drug):
    """
    中成药标准品标记公式（单体差比值）：
    服用天数>0: 挂网价 / 服用天数 / 无糖比值
    服用天数=0,装量>0: 1.9^LOG(1/装量,2) * 2^LOG(1/计价数量,2) * 挂网价
    """
    price = extract_number(drug.get("network_price", 0))
    days = extract_number(drug.get("usage_days", 0))
    spec_package = str(_safe_get(drug, "spec_package", "规格包装"))
    content = extract_number(drug.get("content", 0))
    volume = extract_number(drug.get("volume", 0))
    quantity = extract_number(drug.get("quantity", 0))

    no_sugar_ratio = get_no_sugar_ratio(spec_package)

    if days > 0:
        return price / days / no_sugar_ratio
    elif content > 0 and quantity > 0:
        return (_log2_pow(Decimal('1.7'), 1 / content) *
                _log2_pow(Decimal('2.0'), 1 / quantity) * price)
    elif volume > 0 and quantity > 0:
        return (_log2_pow(Decimal('1.9'), 1 / volume) *
                _log2_pow(Decimal('2.0'), 1 / quantity) * price)
    elif quantity > 0:
        return price / quantity
    else:
        return Decimal('inf')


def calculate_tcm_ratio_price(drug, standard_drug):
    """
    中成药差比价计算公式：
    自身服用天数>0: 标准品挂网价 / 标准品服用天数 / 标准品无糖比值 * 自身服用天数 * 自身无糖比值
    自身服用天数=0: 1.9^LOG(自身装量/标准品装量,2) * 2^LOG(自身计价数量/标准品计价数量,2) * 标准品挂网价
    """
    days = extract_number(drug.get("usage_days", 0))
    std_days = extract_number(standard_drug.get("usage_days", 0))
    std_price = extract_number(standard_drug.get("network_price", 0))
    spec_package = str(_safe_get(drug, "spec_package", "规格包装"))
    std_spec_package = str(_safe_get(standard_drug, "spec_package", "规格包装"))
    volume = extract_number(drug.get("volume", 0))
    std_volume = extract_number(standard_drug.get("volume", 0))
    quantity = extract_number(drug.get("quantity", 0))
    std_quantity = extract_number(standard_drug.get("quantity", 0))

    self_no_sugar = get_no_sugar_ratio(spec_package)
    std_no_sugar = get_no_sugar_ratio(std_spec_package)

    if days > 0 and std_days > 0:
        ratio_price = std_price / std_days / std_no_sugar * days * self_no_sugar
    elif volume > 0 and std_volume > 0 and quantity > 0 and std_quantity > 0:
        ratio_price = (_log2_pow(Decimal('1.9'), volume / std_volume) *
                       _log2_pow(Decimal('2.0'), quantity / std_quantity) *
                       std_price)
    elif quantity > 0 and std_quantity > 0:
        ratio_price = (_log2_pow(Decimal('2.0'), quantity / std_quantity) *
                       std_price)
    else:
        return None

    return round(ratio_price, 2)


def is_same_drug(drug1, drug2):
    """
    判断两个药品是否为"二同药品"。
    匹配优先级：
    1. 同医保目录名 + 同标化持有人
    2. 同特殊标注分组号 + 同标化持有人
    3. 同通用名（去除剂型信息后）
    """
    holder1 = str(_safe_get(drug1, "standard_holder", "标化持有人")).strip()
    holder2 = str(_safe_get(drug2, "standard_holder", "标化持有人")).strip()

    if holder1 == "" or holder2 == "" or holder1 != holder2:
        return False

    special1 = str(_safe_get(drug1, "special_note", "特殊标注"))
    special2 = str(_safe_get(drug2, "special_note", "特殊标注"))
    match1 = re.search(r"分组(\d+)", special1)
    match2 = re.search(r"分组(\d+)", special2)
    if match1 and match2 and match1.group(1) == match2.group(1):
        return True

    catalog1 = str(_safe_get(drug1, "catalog_name", "医保目录名")).strip()
    catalog2 = str(_safe_get(drug2, "catalog_name", "医保目录名")).strip()
    if catalog1 != "" and catalog2 != "" and catalog1 == catalog2:
        return True

    generic1 = str(_safe_get(drug1, "generic_name", "通用名")).strip()
    generic2 = str(_safe_get(drug2, "generic_name", "通用名")).strip()
    if generic1 != "" and generic2 != "":
        if normalize_generic_name(generic1) == normalize_generic_name(generic2):
            return True

    return False


def calculate_drug_price_ratio(drugs: List[Dict]):
    """
    对一组二同药品进行差比价计算。
    选择单体差比值最低的作为标准品。
    """
    if not drugs:
        return drugs

    is_western = any(
        "生物制品" in str(d.get("drug_category", "")) or
        "化学药品" in str(d.get("drug_category", ""))
        for d in drugs
    )
    is_tcm = any("中成药" in str(d.get("drug_category", "")) for d in drugs)

    if not is_western and not is_tcm:
        return drugs

    drugs = list(drugs)

    for drug in drugs:
        if is_western:
            drug["unit_value"] = calculate_western_unit_value(drug)
        else:
            drug["unit_value"] = calculate_tcm_unit_value(drug)

    valid_unit_values = [
        (i, d["unit_value"]) for i, d in enumerate(drugs)
        if d["unit_value"] != Decimal('inf') and d["unit_value"] > 0
    ]

    if not valid_unit_values:
        return drugs

    standard_idx = min(valid_unit_values, key=lambda x: x[1])[0]
    standard_drug = drugs[standard_idx]
    standard_drug["is_standard"] = True
    standard_drug["standard_mark"] = "是(按单体差比值最低)"
    standard_drug["standard_price"] = standard_drug.get("network_price", 0)
    standard_drug["price_diff"] = Decimal('0')

    for i, drug in enumerate(drugs):
        if i == standard_idx:
            continue

        drug["is_standard"] = False
        drug["standard_mark"] = ""

        if is_western:
            ratio_price = calculate_western_ratio_price(drug, standard_drug)
        else:
            ratio_price = calculate_tcm_ratio_price(drug, standard_drug)

        if ratio_price is not None:
            drug["standard_price"] = ratio_price
            drug["price_diff"] = round(
                ratio_price - extract_number(drug.get("network_price", 0)), 2
            )
        else:
            drug["standard_price"] = Decimal('0')
            drug["price_diff"] = Decimal('0')

    return drugs


def group_by_same_catalog(drugs: List[Dict]):
    """按同医保目录名 + 同标化持有人分组"""
    groups: Dict[str, List[Dict]] = {}
    for drug in drugs:
        holder = str(_safe_get(drug, "standard_holder", "标化持有人")).strip()
        catalog = str(_safe_get(drug, "catalog_name", "医保目录名")).strip()
        group_key = f"{holder}|{catalog}"
        if group_key not in groups:
            groups[group_key] = []
        groups[group_key].append(drug)
    return list(groups.values())


def group_by_same_generic(drugs: List[Dict]):
    """按同通用名（标准化后）+ 同标化持有人分组"""
    groups: Dict[str, List[Dict]] = {}
    for drug in drugs:
        holder = str(_safe_get(drug, "standard_holder", "标化持有人")).strip()
        generic = str(drug.get("generic_name", ""))
        normalized = normalize_generic_name(generic)
        group_key = f"{holder}|{normalized}"
        if group_key not in groups:
            groups[group_key] = []
        groups[group_key].append(drug)
    return list(groups.values())


def group_by_both(drugs: List[Dict]):
    """
    二同分组：优先按医保目录名+标化持有人匹配，
    再按特殊标注分组号匹配，最后按通用名匹配。
    """
    matched_indices = set()
    groups = []
    drug_list = list(drugs)

    for i, drug in enumerate(drug_list):
        if i in matched_indices:
            continue
        group = [drug]
        matched_indices.add(i)

        for j, other in enumerate(drug_list):
            if j in matched_indices:
                continue
            if is_same_drug(drug, other):
                group.append(other)
                matched_indices.add(j)

        groups.append(group)

    return groups


def process_all_drugs(drugs: List[Dict], match_catalog: bool = True,
                      match_generic: bool = True):
    """
    对所有药品按分组进行差比价计算。

    参数:
    - match_catalog: 是否启用同医保目录名匹配
    - match_generic: 是否启用同通用名匹配
    两者同时启用时：优先医保目录名，再特殊标注，最后通用名
    """
    if not drugs:
        return drugs

    result_drugs = []

    western_drugs = []
    tcm_drugs = []
    for drug in drugs:
        drug_category = str(drug.get("drug_category", ""))
        if "生物制品" in drug_category or "化学药品" in drug_category:
            western_drugs.append(drug)
        else:
            tcm_drugs.append(drug)

    for category_drugs in [western_drugs, tcm_drugs]:
        if not category_drugs:
            continue

        if match_catalog and match_generic:
            groups = group_by_both(category_drugs)
        elif match_catalog:
            groups = group_by_same_catalog(category_drugs)
        elif match_generic:
            groups = group_by_same_generic(category_drugs)
        else:
            result_drugs.extend(category_drugs)
            continue

        for group in groups:
            calculate_drug_price_ratio(group)
            result_drugs.extend(group)

    return result_drugs
