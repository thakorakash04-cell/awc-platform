"""
Unit tests for Catalog Manager & Import/Export
"""

import pytest
import pandas as pd
from data.catalog_manager import get_catalog
from core.models import DressingCategory


def test_catalog_loads_seed_products():
    catalog = get_catalog()
    prods = catalog.get_all_products()
    assert len(prods) >= 10


def test_catalog_filtering_by_category():
    catalog = get_catalog()
    foams = catalog.filter_products(category=DressingCategory.POLYURETHANE_FOAM_BORDERED)
    assert len(foams) >= 2
    assert all(p.category == DressingCategory.POLYURETHANE_FOAM_BORDERED for p in foams)


def test_catalog_dataframe_export():
    catalog = get_catalog()
    df = catalog.to_dataframe()
    assert isinstance(df, pd.DataFrame)
    assert "Brand Name" in df.columns
    assert "HCPCS Code" in df.columns
    assert len(df) >= 10


def test_catalog_import_from_dataframe():
    catalog = get_catalog()
    sample_data = pd.DataFrame([
        {
            "brand_name": "Test Custom Foam",
            "manufacturer": "Acme Medical",
            "category": "foam_bordered",
            "generic_moc": "Custom polyurethane matrix",
            "hcpcs_base_code": "A6212",
            "is_rx_only": "False",
            "indications": "Moderate exudate wounds",
        }
    ])
    imported, errors = catalog.import_from_dataframe(sample_data)
    assert imported == 1
    assert len(errors) == 0
    test_prod = [p for p in catalog.get_all_products() if "Test Custom Foam" in p.brand_name]
    assert len(test_prod) == 1
