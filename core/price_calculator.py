import math
import re
from decimal import Decimal
from typing import List, Dict, Optional


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
    "片", "普通片", "咀嚼片", "含片", "可溶片", "肠溶片", "分散片", "泡腾片",
    "胶囊", "硬胶囊", "肠溶胶囊", "软胶囊"
]


def extract_number(text):
    if text is None or text == "" or str(text).strip() == "":
        return Decimal('0')
    text = str(text)
    match = re.search(r'\d+\.?\d*', text)
    if match:
        return Decimal(match.group())
    return Decimal('0')


def get_dosage_ratio(dosage_form):
    if dosage_form is None or dosage_form == "":
        return Decimal('1.0')
    dosage_form = str(dosage_form)
    for key, ratio in DOSAGE_FORM_RATIO.items():
        if key in dosage_form:
            return ratio
    return Decimal('1.0')


def is_oral_normal_dosage(dosage_form):
    if dosage_form is None or dosage_form == "":
        return False
    dosage_form = str(dosage_form)
    return any(keyword in dosage_form for keyword in ORAL_NORMAL_DOSAGE_KEYWORDS)


def get_no_sugar_ratio(generic_name, spec_package):
    text = f"{generic_name} {spec_package}"
    if text is None or text.strip() == "":
        return Decimal('1.0')
    text = str(text)
    if any(keyword in text for keyword in NO_SUGAR_KEYWORDS):
        return Decimal('1.1')
    return Decimal('1.0')


def is_same_drug(drug1, drug2, dosage_form_keywords=None):
    if dosage_form_keywords is None:
        dosage_form_keywords = DOSAGE_FORM_KEYWORDS
    
    code1 = str(drug1.get("code") or drug1.get("统编代码", ""))
    code2 = str(drug2.get("code") or drug2.get("统编代码", ""))
    
    holder1 = str(drug1.get("standard_holder") or drug1.get("标化持有人", "")).strip()
    holder2 = str(drug2.get("standard_holder") or drug2.get("标化持有人", "")).strip()
    
    if holder1 == "" or holder2 == "" or holder1 != holder2:
        return False
    
    special_note1 = str(drug1.get("special_note", ""))
    special_note2 = str(drug2.get("special_note", ""))
    match1 = re.search(r"分组(\d+)", special_note1)
    match2 = re.search(r"分组(\d+)", special_note2)
    if match1 and match2 and match1.group(1) == match2.group(1):
        return True
    
    catalog1 = str(drug1.get("catalog_name") or drug1.get("医保目录名", "")).strip()
    catalog2 = str(drug2.get("catalog_name") or drug2.get("医保目录名", "")).strip()
    
    if catalog1 != "" and catalog2 != "" and catalog1 == catalog2:
        return True
    
    generic1 = str(drug1.get("generic_name") or drug1.get("通用名", "")).strip()
    generic2 = str(drug2.get("generic_name") or drug2.get("通用名", "")).strip()
    
    if generic1 != "" and generic2 != "":
        def normalize_name(name):
            name = re.sub(r'[0-9IVXLCDM]+', '', name, flags=re.IGNORECASE)
            name = re.sub(r'[a-zA-Z]+', '', name)
            sorted_keywords = sorted(dosage_form_keywords, key=len, reverse=True)
            for keyword in sorted_keywords:
                name = name.replace(keyword, '')
            return name.strip()
        
        if normalize_name(generic1) == normalize_name(generic2):
            return True
    
    return False


def calculate_western_drug_ratio_unit_value(drug):
    content = extract_number(drug.get("content", 0))
    quantity = extract_number(drug.get("quantity", 0))
    price = extract_number(drug.get("network_price", 0))
    dosage_form = str(drug.get("catalog_dosage_form", ""))
    volume = extract_number(drug.get("volume", 0))
    
    dosage_ratio = get_dosage_ratio(dosage_form)
    is_oral = is_oral_normal_dosage(dosage_form)
    quantity_coeff = Decimal('1.95') if is_oral else Decimal('2.0')
    
    if content > 0 and quantity > 0:
        unit_value = (Decimal('1.7') ** math.log2(float(1 / content))) * (quantity_coeff ** math.log2(float(1 / quantity))) * price / dosage_ratio
    elif volume > 0:
        unit_value = (Decimal('1.9') ** math.log2(float(1 / volume))) * price / dosage_ratio
    else:
        unit_value = Decimal('inf')
    
    return unit_value


def calculate_western_drug_ratio_price(drug, standard_drug):
    content = extract_number(drug.get("content", 0))
    quantity = extract_number(drug.get("quantity", 0))
    std_content = extract_number(standard_drug.get("content", 0))
    std_quantity = extract_number(standard_drug.get("quantity", 0))
    std_price = extract_number(standard_drug.get("network_price", 0))
    dosage_form = str(drug.get("catalog_dosage_form", ""))
    volume = extract_number(drug.get("volume", 0))
    std_volume = extract_number(standard_drug.get("volume", 0))
    
    dosage_ratio = get_dosage_ratio(dosage_form)
    is_oral = is_oral_normal_dosage(dosage_form)
    quantity_coeff = Decimal('1.95') if is_oral else Decimal('2.0')
    
    if content > 0 and quantity > 0 and std_content > 0 and std_quantity > 0:
        ratio_price = (Decimal('1.7') ** math.log2(float(content / std_content))) * (quantity_coeff ** math.log2(float(quantity / std_quantity))) * std_price * dosage_ratio
    elif volume > 0 and std_volume > 0:
        ratio_price = (Decimal('1.9') ** math.log2(float(volume / std_volume))) * std_price * dosage_ratio
    else:
        return None
    
    return round(ratio_price, 2)


def calculate_tcm_ratio_unit_value(drug):
    price = extract_number(drug.get("network_price", 0))
    days = extract_number(drug.get("usage_days", 0))
    generic_name = str(drug.get("generic_name", ""))
    spec_package = str(drug.get("spec_package", ""))
    content = extract_number(drug.get("content", 0))
    quantity = extract_number(drug.get("quantity", 0))
    volume = extract_number(drug.get("volume", 0))
    
    no_sugar_ratio = get_no_sugar_ratio(generic_name, spec_package)
    
    if days > 0:
        unit_value = price / days / no_sugar_ratio
    elif content > 0 and quantity > 0:
        unit_value = (Decimal('1.7') ** math.log2(float(1 / content))) * (Decimal('2.0') ** math.log2(float(1 / quantity))) * price / no_sugar_ratio
    elif volume > 0:
        unit_value = (Decimal('1.9') ** math.log2(float(1 / volume))) * price / no_sugar_ratio
    else:
        unit_value = Decimal('inf')
    
    return unit_value


def calculate_tcm_ratio_price(drug, standard_drug):
    days = extract_number(drug.get("usage_days", 0))
    std_days = extract_number(standard_drug.get("usage_days", 0))
    std_price = extract_number(standard_drug.get("network_price", 0))
    generic_name = str(drug.get("generic_name", ""))
    spec_package = str(drug.get("spec_package", ""))
    volume = extract_number(drug.get("volume", 0))
    std_volume = extract_number(standard_drug.get("volume", 0))
    
    no_sugar_ratio = get_no_sugar_ratio(generic_name, spec_package)
    
    if days > 0 and std_days > 0:
        ratio_price = std_price / std_days * days * no_sugar_ratio
    elif volume > 0 and std_volume > 0:
        ratio_price = (Decimal('1.9') ** math.log2(float(volume / std_volume))) * std_price
    else:
        return None
    
    return round(ratio_price, 2)


def calculate_drug_price_ratio(drugs: List[Dict], basis: str = "max"):
    if not drugs:
        return drugs
    
    is_western = any(
        "生物制品" in str(d.get("drug_category", "")) or "化学药品" in str(d.get("drug_category", ""))
        for d in drugs
    )
    is_tcm = any("中成药" in str(d.get("drug_category", "")) for d in drugs)
    
    if not is_western and not is_tcm:
        return drugs
    
    for drug in drugs:
        if is_western:
            drug["unit_value"] = calculate_western_drug_ratio_unit_value(drug)
        else:
            drug["unit_value"] = calculate_tcm_ratio_unit_value(drug)
    
    valid_unit_values = [
        (i, d["unit_value"]) for i, d in enumerate(drugs)
        if d["unit_value"] != Decimal('inf') and d["unit_value"] > 0
    ]
    
    if not valid_unit_values:
        return drugs
    
    if basis == "min":
        standard_idx = min(valid_unit_values, key=lambda x: x[1])[0]
    else:
        standard_idx = max(valid_unit_values, key=lambda x: x[1])[0]
    
    standard_drug = drugs[standard_idx]
    standard_drug["is_standard"] = True
    standard_drug["standard_price"] = standard_drug.get("network_price", 0)
    standard_drug["price_diff"] = Decimal('0')
    
    for i, drug in enumerate(drugs):
        if i == standard_idx:
            continue
        
        if is_western:
            ratio_price = calculate_western_drug_ratio_price(drug, standard_drug)
        else:
            ratio_price = calculate_tcm_ratio_price(drug, standard_drug)
        
        if ratio_price is not None:
            drug["standard_price"] = ratio_price
            drug["price_diff"] = round(ratio_price - extract_number(drug.get("network_price", 0)), 2)
    
    return drugs


def process_all_drugs(drugs: List[Dict], basis: str = "max", dosage_form_keywords: List[str] = None):
    if dosage_form_keywords is None:
        dosage_form_keywords = DOSAGE_FORM_KEYWORDS
    
    drug_groups = {}
    for drug in drugs:
        drug_category = str(drug.get("drug_category", ""))
        if "生物制品" in drug_category or "化学药品" in drug_category:
            key = "western"
        elif "中成药" in drug_category:
            key = "tcm"
        else:
            continue
        
        holder = str(drug.get("standard_holder", "")).strip()
        catalog = str(drug.get("catalog_name", "")).strip()
        
        group_key = f"{key}_{holder}_{catalog}"
        if group_key not in drug_groups:
            drug_groups[group_key] = []
        drug_groups[group_key].append(drug)
    
    for group_key, group_drugs in drug_groups.items():
        calculate_drug_price_ratio(group_drugs, basis=basis)
    
    return drugs
