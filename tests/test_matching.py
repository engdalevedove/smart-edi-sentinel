"""
tests/test_matching.py
Testes unitários para resolução semântica de SKUs e disponibilidade.
"""
import pytest
from src.engine.material_matcher import MaterialReconciliationEngine


@pytest.fixture
def matcher_engine(mock_catalog):
    return MaterialReconciliationEngine(master_catalog=mock_catalog, min_confidence_threshold=70.0)


@pytest.mark.parametrize("customer_text, expected_sku", [
    ("BISC CREAM CRACK TRAD 350G", "SKU-1001"),
    ("cream cracker tradicional 350 g", "SKU-1001"),
    ("TORRADA MULTIGRAOS INTEG 140G", "SKU-1003"),
    ("Bisc Rech Choc 130g", "SKU-1002-OLD"),
])
def test_fuzzy_matching_resolves_common_variations(matcher_engine, customer_text, expected_sku):
    matched_item, score = matcher_engine.find_best_sku_match(customer_desc=customer_text)
    assert matched_item is not None
    assert matched_item.internal_sku == expected_sku
    assert score >= 70.0


def test_direct_sku_match_has_perfect_confidence(matcher_engine):
    matched_item, score = matcher_engine.find_best_sku_match(
        customer_desc="Qualquer texto irrelevante",
        customer_sku="SKU-1001"
    )
    assert matched_item is not None
    assert matched_item.internal_sku == "SKU-1001"
    assert score == 100.0


def test_unknown_sku_returns_none(matcher_engine):
    matched_item, score = matcher_engine.find_best_sku_match(customer_desc="Produto Inexistente XYZ 999g")
    assert matched_item is None
    assert score < 70.0


def test_discontinued_material_swaps_to_active_substitute(matcher_engine, mock_catalog):
    discontinued_item = mock_catalog["SKU-1002-OLD"]
    resolved_item, is_available, reason = matcher_engine.resolve_material_availability(
        item=discontinued_item,
        customer_region="PR"
    )
    assert is_available is True
    assert resolved_item.internal_sku == "SKU-1002-NEW"
    assert "Substituído automaticamente" in reason


def test_blocked_item_without_substitute_is_rejected(matcher_engine, mock_catalog):
    blocked_item = mock_catalog["SKU-1004-BLOCKED"]
    resolved_item, is_available, reason = matcher_engine.resolve_material_availability(
        item=blocked_item,
        customer_region="SP"
    )
    assert is_available is False
    assert resolved_item.internal_sku == "SKU-1004-BLOCKED"
    assert "sem SKU substituto" in reason


def test_regional_restriction_blocks_item(matcher_engine, mock_catalog):
    item = mock_catalog["SKU-1003"]
    _, is_available, reason = matcher_engine.resolve_material_availability(
        item=item,
        customer_region="BA"
    )
    assert is_available is False
    assert "Item bloqueado para a região 'BA'" in reason