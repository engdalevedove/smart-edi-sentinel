"""
src/engine/material_matcher.py
Reconciliação semântica e de-para de produtos com catálogo SAP mestre.
"""
from typing import Dict, Optional, Tuple
from rapidfuzz import fuzz, process
from src.schemas.order_models import MasterCatalogItem, MaterialStatus


class MaterialReconciliationEngine:
    def __init__(self, master_catalog: Dict[str, MasterCatalogItem], min_confidence_threshold: float = 75.0):
        self.catalog = master_catalog
        self.min_confidence = min_confidence_threshold
        self._descriptions = {item.description.lower(): item.internal_sku for item in master_catalog.values()}

    def find_best_sku_match(self, customer_desc: str, customer_sku: Optional[str] = None) -> Tuple[Optional[MasterCatalogItem], float]:
        if customer_sku and customer_sku in self.catalog:
            return self.catalog[customer_sku], 100.0

        cleaned_query = customer_desc.strip().lower()
        match_result = process.extractOne(
            cleaned_query,
            self._descriptions.keys(),
            scorer=fuzz.token_set_ratio
        )

        if match_result:
            best_desc, score, _ = match_result
            if score >= self.min_confidence:
                matched_sku = self._descriptions[best_desc]
                return self.catalog[matched_sku], float(score)

        return None, 0.0

    def resolve_material_availability(
        self,
        item: MasterCatalogItem,
        customer_region: str
    ) -> Tuple[MasterCatalogItem, bool, str]:
        if customer_region not in item.allowed_regions:
            return item, False, f"Item bloqueado para a região '{customer_region}' (Restrição de extensão SAP)"

        if item.status == MaterialStatus.ACTIVE:
            return item, True, "Item ativo e elegível para faturamento"

        if item.substitute_sku and item.substitute_sku in self.catalog:
            substitute = self.catalog[item.substitute_sku]
            if substitute.status == MaterialStatus.ACTIVE and customer_region in substitute.allowed_regions:
                return substitute, True, f"Item original {item.status.value}. Substituído automaticamente pelo SKU ativo {substitute.internal_sku}"

        return item, False, f"Item {item.status.value} sem SKU substituto válido cadastrado"