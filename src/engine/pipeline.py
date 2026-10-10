"""
src/engine/pipeline.py
Pipeline principal que recebe ordens EDI e consolida a reconciliação.
"""
from typing import Dict
from src.schemas.order_models import (
    EdiOrder,
    MasterCatalogItem,
    ReconciledItem,
    ReconciledOrderResult,
    ResolutionAction
)
from src.engine.material_matcher import MaterialReconciliationEngine
from src.engine.price_validator import PriceValidationEngine


class EdiReconciliationPipeline:
    def __init__(self, catalog: Dict[str, MasterCatalogItem]):
        self.matcher = MaterialReconciliationEngine(catalog)
        self.price_validator = PriceValidationEngine(rounding_tolerance_pct=0.5)

    def process_order(self, order: EdiOrder) -> ReconciledOrderResult:
        reconciled_items = []
        all_clear = True
        total_orig = 0.0
        total_rec = 0.0

        for item in order.items:
            orig_value = item.customer_unit_price * item.requested_quantity
            total_orig += orig_value

            # 1. Matching de SKU (Código ou Fuzzy Matching)
            matched_catalog_item, score = self.matcher.find_best_sku_match(
                customer_desc=item.customer_description,
                customer_sku=item.customer_sku_code
            )

            if not matched_catalog_item:
                all_clear = False
                reconciled_items.append(ReconciledItem(
                    line_number=item.line_number,
                    original_description=item.customer_description,
                    original_price=item.customer_unit_price,
                    resolved_sku=None,
                    resolved_description=None,
                    action=ResolutionAction.BLOCKED_REJECTED,
                    status_reason=f"SKU não identificado na base mestra (Similaridade máx: {score:.1f}%)",
                    confidence_score=score
                ))
                continue

            # 2. Resolução de disponibilidade de material, restrições e substitutos
            final_catalog_item, is_available, status_msg = self.matcher.resolve_material_availability(
                matched_catalog_item,
                customer_region=order.region
            )

            was_substituted = final_catalog_item.internal_sku != matched_catalog_item.internal_sku

            if not is_available:
                all_clear = False
                reconciled_items.append(ReconciledItem(
                    line_number=item.line_number,
                    original_description=item.customer_description,
                    original_price=item.customer_unit_price,
                    resolved_sku=final_catalog_item.internal_sku,
                    resolved_description=final_catalog_item.description,
                    catalog_price=final_catalog_item.base_price,
                    action=ResolutionAction.BLOCKED_REJECTED,
                    status_reason=status_msg,
                    confidence_score=score
                ))
                continue

            # 3. Validação de divergência de preço
            final_price, var_pct, price_action, price_msg = self.price_validator.validate_price(
                customer_price=item.customer_unit_price,
                catalog_item=final_catalog_item
            )

            if price_action == ResolutionAction.PENDING_COMMERCIAL_APPROVAL:
                final_action = ResolutionAction.PENDING_COMMERCIAL_APPROVAL
                all_clear = False
            elif was_substituted:
                final_action = ResolutionAction.AUTO_SUBSTITUTED_SKU
            elif price_action == ResolutionAction.AUTO_ADJUSTED_PRICE:
                final_action = ResolutionAction.AUTO_ADJUSTED_PRICE
            else:
                final_action = ResolutionAction.APPROVED

            item_total = final_price * item.requested_quantity
            total_rec += item_total

            reconciled_items.append(ReconciledItem(
                line_number=item.line_number,
                original_description=item.customer_description,
                original_price=item.customer_unit_price,
                resolved_sku=final_catalog_item.internal_sku,
                resolved_description=final_catalog_item.description,
                catalog_price=final_catalog_item.base_price,
                final_price=final_price,
                price_variance_pct=var_pct,
                action=final_action,
                status_reason=f"{status_msg} | {price_msg}",
                confidence_score=score
            ))

        # Contabilização de ações resolvidas automaticamente vs pendentes de revisão
        auto_resolved_count = sum(
            1 for i in reconciled_items
            if i.action in (
                ResolutionAction.APPROVED,
                ResolutionAction.AUTO_ADJUSTED_PRICE,
                ResolutionAction.AUTO_SUBSTITUTED_SKU
            )
        )

        pending_review_count = sum(
            1 for i in reconciled_items
            if i.action in (
                ResolutionAction.PENDING_COMMERCIAL_APPROVAL,
                ResolutionAction.BLOCKED_REJECTED
            )
        )

        return ReconciledOrderResult(
            order_id=order.order_id,
            customer_name=order.customer_name,
            all_clear_for_sap=all_clear,
            total_original_value=round(total_orig, 2),
            total_reconciled_value=round(total_rec, 2),
            summary={
                "total_items": len(order.items),
                "auto_resolved": auto_resolved_count,
                "pending_review": pending_review_count
            },
            reconciled_items=reconciled_items
        )