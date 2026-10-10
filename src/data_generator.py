"""
src/data_generator.py
Gera dados sintéticos de alta fidelidade para simular pedidos EDI B2B
e o catálogo mestre de materiais SAP.
"""
import json
import random
from pathlib import Path
from typing import List, Dict

# Semente fixa para reprodutibilidade
random.seed(42)

# Garante o caminho absoluto para a pasta data na raiz do projeto
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PRODUCT_TEMPLATES = [
    ("Biscoito Cream Cracker Tradicional 350g", 4.50, 4.20, ["SP", "PR", "SC", "RJ", "MG"]),
    ("Biscoito Cream Cracker Folhado 350g", 4.80, 4.40, ["SP", "PR", "SC", "RJ"]),
    ("Biscoito Recheado Chocolate Nova Formula 140g", 2.90, 2.70, ["SP", "PR", "RJ", "MG", "BA"]),
    ("Biscoito Recheado Baunilha 140g", 2.90, 2.70, ["SP", "PR", "RJ"]),
    ("Biscoito Recheado Morango 140g", 2.90, 2.70, ["SP", "PR", "MG"]),
    ("Torrada Salgada Tradicional 140g", 4.20, 3.90, ["SP", "PR", "SC"]),
    ("Torrada Multigrãos Integral 140g", 5.10, 4.80, ["SP", "PR"]),
    ("Wafer Chocolate Crocante 115g", 3.40, 3.10, ["SP", "PR", "RJ", "MG"]),
    ("Wafer Morango Especial 115g", 3.40, 3.10, ["SP"]),
    ("Biscoito Maisena Tradicional 360g", 5.20, 4.90, ["SP", "PR", "SC", "RJ", "MG", "BA"]),
]

CLIENTS = [
    {"name": "Supermercados Muffato", "cnpj": "76.430.438/0001-00", "region": "PR"},
    {"name": "Atacadao S.A.", "cnpj": "75.315.333/0001-09", "region": "SP"},
    {"name": "Assai Atacadista", "cnpj": "06.057.223/0001-71", "region": "SP"},
    {"name": "Companhia Brasileira de Distribuicao", "cnpj": "47.508.411/0001-56", "region": "RJ"},
    {"name": "Supermercados BH", "cnpj": "04.641.376/0001-36", "region": "MG"},
    {"name": "Rede Nordeste Alimentos", "cnpj": "12.345.678/0001-90", "region": "BA"}
]

NOISE_PATTERNS = {
    "Biscoito": ["BISC", "Bisc.", "BSCT", "BISCOITO"],
    "Cream Cracker": ["CREAM CRACK", "CR CRACKER", "CR.CRACK", "CRACKER"],
    "Recheado": ["RECH", "RECH.", "RCH", "RECHEADO"],
    "Chocolate": ["CHOC", "CHOC.", "CHOCOLATE"],
    "Tradicional": ["TRAD", "TRAD.", "TRADICIONAL"],
    "Integral": ["INTEG", "INT", "INTEGRAL"],
    "Multigrãos": ["MULTIGRAOS", "MULTI GRAOS", "MULTIGR"],
    "350g": ["350G", "350 G", "350GR", "CX 350G"],
    "140g": ["140G", "140 G", "140GR"],
}

def inject_noise_in_description(description: str) -> str:
    words = description.split()
    noisy_words = []
    for w in words:
        if w in NOISE_PATTERNS and random.random() < 0.7:
            noisy_words.append(random.choice(NOISE_PATTERNS[w]))
        else:
            noisy_words.append(w)
    
    noisy_text = " ".join(noisy_words)
    dice = random.random()
    if dice < 0.4:
        return noisy_text.upper()
    elif dice < 0.6:
        return noisy_text.lower()
    return noisy_text


def generate_master_catalog() -> Dict:
    catalog = {}
    for i, (desc, base_price, min_price, regions) in enumerate(PRODUCT_TEMPLATES, start=1001):
        sku = f"SKU-{i}"
        catalog[sku] = {
            "internal_sku": sku,
            "description": desc,
            "status": "ATIVO",
            "base_price": base_price,
            "min_allowed_price": min_price,
            "max_discount_pct": round(((base_price - min_price) / base_price) * 100, 2),
            "allowed_regions": regions,
            "substitute_sku": None,
            "uom": "CX"
        }

    catalog["SKU-1003-OLD"] = {
        "internal_sku": "SKU-1003-OLD",
        "description": "Biscoito Recheado Chocolate Antigo 130g",
        "status": "DESCONTINUADO",
        "base_price": 2.90,
        "min_allowed_price": 2.70,
        "max_discount_pct": 6.9,
        "allowed_regions": ["SP", "PR", "RJ"],
        "substitute_sku": "SKU-1003",
        "uom": "CX"
    }

    catalog["SKU-9999-BLOCKED"] = {
        "internal_sku": "SKU-9999-BLOCKED",
        "description": "Item Piloto Bloqueado Vendas 200g",
        "status": "BLOQUEADO_COMERCIAL",
        "base_price": 6.00,
        "min_allowed_price": 5.50,
        "max_discount_pct": 8.3,
        "allowed_regions": ["SP"],
        "substitute_sku": None,
        "uom": "CX"
    }

    return catalog


def generate_mock_edi_orders(catalog: Dict, num_orders: int = 50) -> List[Dict]:
    orders = []
    catalog_items = list(catalog.values())

    for idx in range(1, num_orders + 1):
        client = random.choice(CLIENTS)
        num_items = random.randint(2, 6)
        chosen_items = random.sample(catalog_items, num_items)

        order_items = []
        for line_no, item in enumerate(chosen_items, start=1):
            raw_description = inject_noise_in_description(item["description"])
            
            scenario = random.random()
            if scenario < 0.60:
                unit_price = item["base_price"]
            elif scenario < 0.80:
                delta = random.choice([-0.01, -0.02, 0.01, 0.02])
                unit_price = round(item["base_price"] + delta, 2)
            elif scenario < 0.90:
                unit_price = round(random.uniform(item["min_allowed_price"], item["base_price"]), 2)
            else:
                unit_price = round(item["min_allowed_price"] * random.uniform(0.75, 0.95), 2)

            customer_sku = item["internal_sku"] if random.random() > 0.3 else None

            order_items.append({
                "line_number": line_no,
                "customer_sku_code": customer_sku,
                "customer_description": raw_description,
                "requested_quantity": random.choice([50, 100, 250, 500, 1000]),
                "customer_unit_price": unit_price,
                "customer_uom": "CX"
            })

        orders.append({
            "order_id": f"EDI-{20260000 + idx}",
            "customer_cnpj": client["cnpj"],
            "customer_name": client["name"],
            "region": client["region"],
            "created_at": "2026-10-10T09:30:00",
            "items": order_items
        })

    return orders


if __name__ == "__main__":
    master_catalog = generate_master_catalog()
    with open(DATA_DIR / "master_catalog.json", "w", encoding="utf-8") as f:
        json.dump(master_catalog, f, ensure_ascii=False, indent=2)

    mock_orders = generate_mock_edi_orders(master_catalog, num_orders=50)
    with open(DATA_DIR / "mock_edi_orders.json", "w", encoding="utf-8") as f:
        json.dump(mock_orders, f, ensure_ascii=False, indent=2)

    print(f"Sucesso! Gerados {len(master_catalog)} SKUs no catalogo e {len(mock_orders)} pedidos simulados em '{DATA_DIR}'.")