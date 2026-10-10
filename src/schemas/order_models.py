"""
src/schemas/order_models.py
Define os esquemas de validação de dados para pedidos EDI e resultados de reconciliação.
"""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class MaterialStatus(str, Enum):
    ACTIVE = "ATIVO"
    BLOCKED_COMMERCIAL = "BLOQUEADO_COMERCIAL"
    DISCONTINUED = "DESCONTINUADO"
    REGIONAL_RESTRICTION = "RESTRICAO_REGIONAL"


class ResolutionAction(str, Enum):
    APPROVED = "APROVADO_DIRETO"
    AUTO_ADJUSTED_PRICE = "AJUSTE_AUTOMATICO_PRECO"
    AUTO_SUBSTITUTED_SKU = "SUBSTITUICAO_AUTOMATICA_SKU"
    PENDING_COMMERCIAL_APPROVAL = "PENDENTE_APROVACAO_COMERCIAL"
    BLOCKED_REJECTED = "BLOQUEADO_REJEITADO"


class EdiOrderItem(BaseModel):
    line_number: int
    customer_sku_code: Optional[str] = Field(None, description="Código do item informado pelo cliente")
    customer_description: str = Field(..., description="Descrição textual enviada no EDI")
    requested_quantity: int = Field(..., gt=0)
    customer_unit_price: float = Field(..., gt=0)
    customer_uom: str = Field("CX", description="Unidade de medida: CX, UN, FD, PL")


class EdiOrder(BaseModel):
    order_id: str
    customer_cnpj: str
    customer_name: str
    region: str
    created_at: str
    items: List[EdiOrderItem]


class MasterCatalogItem(BaseModel):
    internal_sku: str
    description: str
    status: MaterialStatus
    base_price: float
    min_allowed_price: float
    max_discount_pct: float
    allowed_regions: List[str]
    substitute_sku: Optional[str] = None
    uom: str = "CX"


class ReconciledItem(BaseModel):
    line_number: int
    original_description: str
    original_price: float
    resolved_sku: Optional[str]
    resolved_description: Optional[str]
    catalog_price: Optional[float] = None
    final_price: Optional[float] = None
    price_variance_pct: float = 0.0
    action: ResolutionAction
    status_reason: str
    confidence_score: float = 1.0


class ReconciledOrderResult(BaseModel):
    order_id: str
    customer_name: str
    all_clear_for_sap: bool
    total_original_value: float
    total_reconciled_value: float
    summary: dict
    reconciled_items: List[ReconciledItem]