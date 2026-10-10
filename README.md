# 🛡️ SmartEDI-Sentinel

> **Motor Inteligente de Pré-Validação, Reconciliação Semântica e Triagem de Pedidos EDI para SAP (B2B / FMCG)**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/pytest-100%25%20passed-brightgreen.svg)](tests/)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

---

## 📌 Contexto & Dor de Negócio

Na indústria de bens de consumo de giro rápido (FMCG), grandes redes de retalho enviam milhares de ordens de compra em massa via **EDI (Electronic Data Interchange)** para integração direta no **SAP ERP**.

No dia a dia operacional, uma parcela significativa desses pedidos bloqueia na esteira de entrada devido a:
1. **Divergências de Preço:** Arredondamentos de impostos/cêntimos ou defasagem de tabela comercial.
2. **Itens Bloqueados / Descontinuados:** Pedidos emitidos com códigos legados ou produtos em substituição de fórmula.
3. **Restrições Regionais:** SKUs sem extensão cadastral ativa para o centro de distribuição/região do cliente.

**Impacto Real:** Centenas de horas mensais de retrabalho da equipa de Administração de Vendas para redigitar ordens, perda da janela de expedição e risco de penalizações por quebra de *OTIF (On-Time In-Full)*.

O **SmartEDI-Sentinel** atua como um middleware inteligente que interceta, audita e reconcilia os pedidos **antes** do bloqueio no ERP.

---

## 🏗️ Arquitetura do Sistema

```mermaid
graph TD
    A[Pedido EDI Cliente: JSON/IDoc] --> B[SmartEDI Sentinel API]
    B --> C[Fuzzy Matching & Normalização]
    C --> D{Item Bloqueado/Descontinuado?}
    D -- Sim --> E[Auto-Substituição por SKU Ativo]
    D -- Não --> F[Validador de Preço & Tolerância]
    E --> F
    F --> G{Divergência <= 0.5%?}
    G -- Sim --> H[Ajuste Automático de Cêntimos]
    G -- Não --> I{Abaixo do Piso?}
    I -- Sim --> J[Encaminhamento Alçada Comercial]
    I -- Não --> K[Aprovado com Desconto]
    H --> L[Payload Reconciliado Pronto para SAP]
    K --> L
    J --> M[Fila de Auditoria Manual]

