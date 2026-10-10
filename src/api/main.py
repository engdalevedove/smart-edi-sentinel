"""
src/api/main.py
API FastAPI para pré-validação e reconciliação de pedidos EDI em tempo real.
"""
import json
from pathlib import Path
from typing import Dict
from fastapi import FastAPI, HTTPException
from src.schemas.order_models import EdiOrder, MasterCatalogItem, ReconciledOrderResult
from src.engine.pipeline import EdiReconciliationPipeline

app = FastAPI(
    title="SmartEDI Sentinel API",
    description="Motor de pré-validação e reconciliação autônoma de pedidos EDI integrado ao SAP",
    version="1.0.0"
)

# Carrega o catálogo mestre a partir do JSON gerado
CATALOG_PATH = Path("data/master_catalog.json")

def load_catalog() -> Dict[str, MasterCatalogItem]:
    if not CATALOG_PATH.exists():
        return {}
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    return {sku: MasterCatalogItem(**item) for sku, item in raw_data.items()}

# Instancia o pipeline na inicialização
master_catalog = load_catalog()
pipeline = EdiReconciliationPipeline(master_catalog)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "loaded_skus": len(master_catalog),
        "version": "1.0.0"
    }


@app.post("/api/v1/reconcile", response_model=ReconciledOrderResult)
def reconcile_order(order: EdiOrder):
    """
    Recebe um payload de pedido EDI, executa matching semântico de SKU,
    validação de alçada de preços e verificação de bloqueios SAP.
    """
    if not master_catalog:
        raise HTTPException(
            status_code=500,
            detail="Catálogo mestre não carregado. Execute 'python src/data_generator.py' primeiro."
        )
    return pipeline.process_order(order)