"""
tests/conftest.py
Fixtures com catálogo mestre SAP e dados de teste.
"""
import pytest
from src.schemas.order_models import MasterCatalogItem, MaterialStatus


@pytest.fixture
def mock_catalog():
    return {
        "SKU-1001": MasterCatalogItem(
            internal_sku="SKU-1001",
            description="Biscoito Cream Cracker Tradicional 350g",
            status=MaterialStatus.ACTIVE,
            base_price=4.50,
            min_allowed_price=4.20,
            max_discount_pct=6.6,
            allowed_regions=["SP", "PR", "SC", "RJ"],
            substitute_sku=None
        ),
        "SKU-1002-OLD": MasterCatalogItem(
            internal_sku="SKU-1002-OLD",
            description="Biscoito Recheado Chocolate 130g",
            status=MaterialStatus.DISCONTINUED,
            base_price=2.80,
            min_allowed_price=2.60,
            max_discount_pct=5.0,
            allowed_regions=["SP", "PR"],
            substitute_sku="SKU-1002-NEW"
        ),
        "SKU-1002-NEW": MasterCatalogItem(
            internal_sku="SKU-1002-NEW",
            description="Biscoito Recheado Chocolate Nova Formula 140g",
            status=MaterialStatus.ACTIVE,
            base_price=2.80,
            min_allowed_price=2.60,
            max_discount_pct=5.0,
            allowed_regions=["SP", "PR", "RJ"],
            substitute_sku=None
        ),
        "SKU-1003": MasterCatalogItem(
            internal_sku="SKU-1003",
            description="Torrada Multigrãos Integral 140g",
            status=MaterialStatus.ACTIVE,
            base_price=5.00,
            min_allowed_price=4.75,
            max_discount_pct=5.0,
            allowed_regions=["SP", "PR"],
            substitute_sku=None
        ),
        "SKU-1004-BLOCKED": MasterCatalogItem(
            internal_sku="SKU-1004-BLOCKED",
            description="Wafer Morango Especial 115g",
            status=MaterialStatus.BLOCKED_COMMERCIAL,
            base_price=3.20,
            min_allowed_price=3.00,
            max_discount_pct=5.0,
            allowed_regions=["SP"],
            substitute_sku=None
        ),
    }