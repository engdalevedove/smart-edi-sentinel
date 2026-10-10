"""
tests/test_pipeline_e2e.py
Teste de integração ponta a ponta do pipeline de reconciliação.
"""
from src.engine.pipeline import EdiReconciliationPipeline
from src.schemas.order_models import EdiOrder, EdiOrderItem, ResolutionAction


def test_full_pipeline_mixed_order(mock_catalog):
    pipeline = EdiReconciliationPipeline(mock_catalog)

    order = EdiOrder(
            order_id="EDI-TEST-001",
            customer_cnpj="11.222.333/0001-44",
            customer_name="Rede Varejo Teste",
            region="SP",
            created_at="2026-10-10T11:00:00",
            items=[
                # Item 1: Variação de centavo -> Auto ajustado
                EdiOrderItem(
                    line_number=1,
                    customer_description="BISC CREAM CRACK TRAD 350G",
                    requested_quantity=100,
                    customer_unit_price=4.49
                ),
                # Item 2: Item antigo descontinuado enviado pelo cliente -> Auto substituído
                EdiOrderItem(
                    line_number=2,
                    customer_sku_code="SKU-1002-OLD",
                    customer_description="Bisc Rech Choc 130g",
                    requested_quantity=50,
                    customer_unit_price=2.80
                ),
                # Item 3: Violação de piso de preço -> Pendente comercial
                EdiOrderItem(
                    line_number=3,
                    customer_description="Torrada Multigrãos Integral 140g",
                    requested_quantity=20,
                    customer_unit_price=3.50
                )
            ]
        )

    result = pipeline.process_order(order)

    assert result.order_id == "EDI-TEST-001"
    assert result.all_clear_for_sap is False
    assert result.summary["total_items"] == 3
    assert result.summary["auto_resolved"] == 2
    assert result.summary["pending_review"] == 1

    item1 = result.reconciled_items[0]
    assert item1.action == ResolutionAction.AUTO_ADJUSTED_PRICE
    assert item1.resolved_sku == "SKU-1001"
    assert item1.final_price == 4.50

    item2 = result.reconciled_items[1]
    assert item2.action == ResolutionAction.AUTO_SUBSTITUTED_SKU
    assert item2.resolved_sku == "SKU-1002-NEW"

    item3 = result.reconciled_items[2]
    assert item3.action == ResolutionAction.PENDING_COMMERCIAL_APPROVAL