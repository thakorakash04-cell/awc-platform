"""
Product Catalog Manager & Importer/Exporter
Handles dataset persistence, CSV/Excel loading, and dynamic product queries.
"""

import os
import pandas as pd
from typing import List, Optional, Dict, Any, Tuple
from core.models import (
    AWCProduct,
    ProductSKU,
    DressingCategory,
    DressingRole,
    AdhesiveType,
    FormatType,
)
from data.seed_data import get_seed_products


class CatalogManager:
    def __init__(self):
        self._products: Dict[str, AWCProduct] = {}
        self.load_seed_catalog()

    def load_seed_catalog(self):
        """Loads default verified clinical seed products."""
        seeds = get_seed_products()
        for p in seeds:
            self._products[p.id] = p

    def get_all_products(self) -> List[AWCProduct]:
        return list(self._products.values())

    def get_product_by_id(self, product_id: str) -> Optional[AWCProduct]:
        return self._products.get(product_id)

    def add_or_update_product(self, product: AWCProduct):
        self._products[product.id] = product

    def filter_products(
        self,
        category: Optional[DressingCategory] = None,
        role: Optional[DressingRole] = None,
        otc_only: bool = False,
        search_query: Optional[str] = None,
    ) -> List[AWCProduct]:
        results = list(self._products.values())

        if category:
            results = [p for p in results if p.category == category]

        if role:
            results = [p for p in results if p.role == role]

        if otc_only:
            results = [p for p in results if not p.is_rx_only]

        if search_query:
            q = search_query.lower()
            results = [
                p for p in results
                if q in p.brand_name.lower()
                or q in p.manufacturer.lower()
                or q in p.generic_moc.lower()
                or q in p.hcpcs_base_code.lower()
                or any(q in ind.lower() for ind in p.indications)
            ]

        return results

    def import_from_dataframe(self, df: pd.DataFrame) -> Tuple[int, List[str]]:
        """
        Imports and maps custom CSV/Excel DataFrame to AWCProduct instances.
        Returns (count_imported, list_of_errors).
        """
        imported_count = 0
        errors: List[str] = []

        # Required or fallback columns
        for idx, row in df.iterrows():
            try:
                brand = str(row.get("brand_name", row.get("Brand", row.get("Product Name", f"Custom Product {idx+1}")))).strip()
                manufacturer = str(row.get("manufacturer", row.get("Manufacturer", "Generic / Custom"))).strip()
                cat_str = str(row.get("category", row.get("Category", row.get("Dressing Type", "foam_bordered")))).lower().strip()

                # Map category safely
                matched_category = DressingCategory.POLYURETHANE_FOAM_BORDERED
                for cat in DressingCategory:
                    if cat.value in cat_str or cat_str in cat.value:
                        matched_category = cat
                        break

                prod_id = f"IMPORT-{idx+1:03d}-{brand[:4].upper()}"
                generic_moc = str(row.get("generic_moc", row.get("MOC", row.get("Material", "Standard wound care dressing"))))
                hcpcs = str(row.get("hcpcs_base_code", row.get("HCPCS", row.get("Billing Code", "A6212")))).strip()
                rx_val = str(row.get("is_rx_only", row.get("Rx", "False"))).lower() in ["true", "1", "yes", "rx"]

                prod = AWCProduct(
                    id=prod_id,
                    brand_name=brand,
                    manufacturer=manufacturer,
                    category=matched_category,
                    generic_moc=generic_moc,
                    role=DressingRole.COMPOSITE if "bordered" in cat_str else DressingRole.PRIMARY,
                    adhesive_type=AdhesiveType.SOFT_SILICONE if "silicone" in cat_str or "silicone" in generic_moc.lower() else AdhesiveType.NON_ADHERENT,
                    format=FormatType.BORDERED_ISLAND if "bordered" in cat_str else FormatType.PAD,
                    fluid_handling_capacity=str(row.get("fluid_handling_capacity", row.get("Absorption", "Moderate"))),
                    dynamic_mvtr="Moderate",
                    waterproof_barrier=True,
                    active_antimicrobial=row.get("active_antimicrobial", row.get("Antimicrobial", None)),
                    wear_time_days_max=int(row.get("wear_time_days_max", row.get("Max Wear Time", 7))),
                    wear_time_recommended_days=int(row.get("wear_time_recommended_days", 3)),
                    is_rx_only=rx_val,
                    hcpcs_base_code=hcpcs,
                    indications=[str(row.get("indications", row.get("Indication", "General wound management")))],
                    contraindications=[str(row.get("contraindications", row.get("Contraindication", "None specified")))],
                    clinical_pearls=str(row.get("clinical_pearls", row.get("Notes", "Imported from custom product catalog."))),
                    application_instructions=["Follow manufacturer package insert."],
                    skus=[
                        ProductSKU(
                            sku_id=f"SKU-{prod_id}-1",
                            dimensions=str(row.get("dimensions", row.get("Size", '4" x 4"'))),
                            hcpcs_code=hcpcs,
                            estimated_retail_usd=float(row.get("price", row.get("Retail Price", 45.0))),
                            otc_available=not rx_val,
                        )
                    ],
                )
                self.add_or_update_product(prod)
                imported_count += 1
            except Exception as e:
                errors.append(f"Row {idx+1} failed: {str(e)}")

        return imported_count, errors

    def to_dataframe(self) -> pd.DataFrame:
        """Exports entire current catalog into a structured pandas DataFrame."""
        rows = []
        for p in self._products.values():
            sku_dims = ", ".join([s.dimensions for s in p.skus]) if p.skus else ""
            sku_price = p.skus[0].estimated_retail_usd if p.skus else 0.0
            rows.append({
                "Product ID": p.id,
                "Brand Name": p.brand_name,
                "Manufacturer": p.manufacturer,
                "Category": p.category.value,
                "Role": p.role.value,
                "Generic MOC": p.generic_moc,
                "HCPCS Code": p.hcpcs_base_code,
                "Fluid Absorption": p.fluid_handling_capacity,
                "Adhesive Type": p.adhesive_type.value,
                "Max Wear Time (Days)": p.wear_time_days_max,
                "Recommended Change (Days)": p.wear_time_recommended_days,
                "Rx Only": p.is_rx_only,
                "Active Antimicrobial": p.active_antimicrobial or "None",
                "Available Sizes": sku_dims,
                "Est Retail USD": sku_price,
                "Indications": "; ".join(p.indications),
                "Contraindications": "; ".join(p.contraindications),
                "Clinical Pearls": p.clinical_pearls,
            })
        return pd.DataFrame(rows)


# Global singleton instance
_catalog_instance = None


def get_catalog() -> CatalogManager:
    global _catalog_instance
    if _catalog_instance is None:
        _catalog_instance = CatalogManager()
    return _catalog_instance
