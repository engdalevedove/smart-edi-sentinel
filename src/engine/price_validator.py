"""
src/engine/price_validator.py
Validador de regras de precificação e tolerância financeira.
"""
from typing import Tuple
from src.schemas.order_models import MasterCatalogItem, ResolutionAction


class PriceValidationEngine:
    def __init__(self, rounding_tolerance_pct: float = 0.5):
        self.rounding_tolerance_pct = rounding_tolerance_pct

    def validate_price(
        self,
        customer_price: float,
        catalog_item: MasterCatalogItem
    ) -> Tuple[float, float, ResolutionAction, str]:
        target_price = catalog_item.base_price
        diff = customer_price - target_price
        variance_pct = round((diff / target_price) * 100, 2)

        if abs(variance_pct) == 0.0:
            return customer_price, 0.0, ResolutionAction.APPROVED, "Preço em total conformidade"

        if abs(variance_pct) <= self.rounding_tolerance_pct:
            return (
                target_price,
                variance_pct,
                ResolutionAction.AUTO_ADJUSTED_PRICE,
                f"Variação irrelevante ({variance_pct}%). Ajustado automaticamente para tabela vigente (R$ {target_price:.2f})"
            )

        if variance_pct > 0:
            return customer_price, variance_pct, ResolutionAction.APPROVED, f"Preço do cliente superior à tabela ({variance_pct}% acima)"

        if customer_price < catalog_item.min_allowed_price:
            return (
                customer_price,
                variance_pct,
                ResolutionAction.PENDING_COMMERCIAL_APPROVAL,
                f"Divergência de preço ({variance_pct}% abaixo). Inferior ao piso permitido de R$ {catalog_item.min_allowed_price:.2f}"
            )

        return (
            customer_price,
            variance_pct,
            ResolutionAction.APPROVED,
            f"Preço aceito dentro da alçada comercial de desconto ({variance_pct}%)"
        )