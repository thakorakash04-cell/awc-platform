"""
AWC Data Manager
Single Source of Truth: Loads and indexes the user's AWCare_Merged.xlsx dataset.
"""

import os
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple


class AWCDataManager:
    def __init__(self, excel_path: str = "data/AWCare_Merged.xlsx"):
        self.excel_path = excel_path
        self.df_main: pd.DataFrame = pd.DataFrame()
        self.prod_images: Dict[str, str] = {}
        self.ind_images: Dict[str, str] = {}
        self.load_data()

    def load_data(self):
        """Loads all sheets from the user's Excel file and builds indices."""
        if not os.path.exists(self.excel_path):
            raise FileNotFoundError(f"Dataset not found at {self.excel_path}")

        xl = pd.ExcelFile(self.excel_path)

        # 1. Main AWC Data
        sheet_name = 'Merged AWC Data' if 'Merged AWC Data' in xl.sheet_names else ('L' if 'L' in xl.sheet_names else xl.sheet_names[0])
        self.df_main = xl.parse(sheet_name)

        # Standardize column names and clean strings
        for col in self.df_main.columns:
            self.df_main[col] = self.df_main[col].astype(str).str.strip().replace('nan', '').replace('None', '')

        # Standardize MOC column name if needed
        if 'Material / Components' in self.df_main.columns and 'Material of Construction/ Components' not in self.df_main.columns:
            self.df_main['Material of Construction/ Components'] = self.df_main['Material / Components']

        if 'Wear Time' in self.df_main.columns and 'Cumulative Wear Time' not in self.df_main.columns:
            self.df_main['Cumulative Wear Time'] = self.df_main['Wear Time']

        # 2. Product Images
        if 'Image-Product ' in xl.sheet_names or 'Image-Product' in xl.sheet_names:
            img_sheet = 'Image-Product ' if 'Image-Product ' in xl.sheet_names else 'Image-Product'
            df_prod_img = xl.parse(img_sheet)
            for _, row in df_prod_img.iterrows():
                pname = str(row.get('Product Name', '')).strip().lower()
                url = str(row.get('URL', '')).strip()
                if pname and url and url != 'nan':
                    self.prod_images[pname] = url

        # 3. Indication Images
        if 'Image-Indication' in xl.sheet_names:
            df_ind_img = xl.parse('Image-Indication')
            for _, row in df_ind_img.iterrows():
                iname = str(row.get('Product Name', '')).strip().lower()
                url = str(row.get('URL', '')).strip()
                if iname and url and url != 'nan':
                    self.ind_images[iname] = url

        # Map images directly into df_main
        self.df_main['Product_Image_URL'] = self.df_main['Product Name'].apply(
            lambda x: self.prod_images.get(str(x).strip().lower(), '')
        )
        self.df_main['Indication_Image_URL'] = self.df_main['Indications (AWC)'].apply(
            lambda x: self.ind_images.get(str(x).strip().lower(), '')
        )

    def get_wound_types(self) -> List[str]:
        val = [str(w).strip() for w in self.df_main['Wound Type'].unique() if str(w).strip() and str(w).strip().lower() != 'nan']
        return sorted(list(set(val)))

    def get_indications(self, wound_type: Optional[str] = None) -> List[str]:
        if wound_type and wound_type != 'All':
            subset = self.df_main[self.df_main['Wound Type'].astype(str).str.lower() == wound_type.lower()]
            val = [str(i).strip() for i in subset['Indications (AWC)'].unique() if str(i).strip() and str(i).strip().lower() != 'nan']
        else:
            val = [str(i).strip() for i in self.df_main['Indications (AWC)'].unique() if str(i).strip() and str(i).strip().lower() != 'nan']
        return sorted(list(set(val)))

    def get_exudate_levels(self) -> List[str]:
        val = [str(e).strip() for e in self.df_main['Exudate Level(Mild/ Moderate/ Heavy)'].unique() if str(e).strip() and str(e).strip().lower() != 'nan']
        # Order logically: Mild, Moderate, Heavy
        order = {"mild": 1, "moderate": 2, "heavy": 3}
        return sorted(list(set(val)), key=lambda x: order.get(str(x).lower(), 99))

    def get_applications(self) -> List[str]:
        val = [str(a).strip() for a in self.df_main['Application'].unique() if str(a).strip() and str(a).strip().lower() != 'nan']
        return sorted(list(set(val)))

    def get_dressing_types(self) -> List[str]:
        val = [str(t).strip() for t in self.df_main['Type of Dressing'].unique() if str(t).strip() and str(t).strip().lower() != 'nan']
        return sorted(list(set(val)))

    def get_healing_phases(self) -> List[str]:
        val = []
        for raw in self.df_main['Healing Phase'].unique():
            if str(raw).strip() and str(raw).strip().lower() != 'nan':
                # Some have multiple lines like 'Phase 2\nPhase 3'
                for part in str(raw).split('\n'):
                    p = part.strip()
                    if p and p.lower() != 'nan':
                        val.append(p)
        return sorted(list(set(val)))

    def get_all_product_names(self) -> List[str]:
        val = [str(p).strip() for p in self.df_main['Product Name'].unique() if str(p).strip() and str(p).strip().lower() != 'nan']
        return sorted(list(set(val)))

    def get_product_details(self, product_name: str) -> Dict[str, Any]:
        """Gets full aggregated details for a specific product name from the dataset."""
        sub = self.df_main[self.df_main['Product Name'].str.lower() == product_name.strip().lower()]
        if sub.empty:
            return {}

        first = sub.iloc[0]

        # Aggregate unique sizes, indications, applications, contraindications
        sizes = [s for s in sub['Size Available'].unique() if s]
        indications = [i for i in sub['Indications (AWC)'].unique() if i]
        applications = [a for a in sub['Application'].unique() if a]
        wound_types = [w for w in sub['Wound Type'].unique() if w]
        exudates = [e for e in sub['Exudate Level(Mild/ Moderate/ Heavy)'].unique() if e]
        dressing_types = [t for t in sub['Type of Dressing'].unique() if t]
        contra = first.get('Contra-indications', '')
        image_url = self.prod_images.get(product_name.strip().lower(), '')

        return {
            "product_name": first.get('Product Name', product_name),
            "image_url": image_url,
            "description": first.get('Description', ''),
            "moc": first.get('Material of Construction/ Components', ''),
            "key_features": first.get('Key Features', ''),
            "dressing_type": ", ".join(dressing_types),
            "sizes_available": sizes,
            "indications": indications,
            "applications": applications,
            "wound_types": wound_types,
            "exudate_levels": exudates,
            "hydration": first.get('Hydration', ''),
            "healing_phase": first.get('Healing Phase', ''),
            "absorbency": first.get('Absorbency', ''),
            "frequency": first.get('Frequency', ''),
            "wear_time": first.get('Cumulative Wear Time', ''),
            "sterilization": first.get('Sterilization', ''),
            "contraindications": contra,
        }

    def filter_products(
        self,
        wound_type: Optional[str] = None,
        indication: Optional[str] = None,
        exudate: Optional[str] = None,
        application: Optional[str] = None,
        dressing_type: Optional[str] = None,
        healing_phase: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Filters products from the dataset based on selected criteria.
        Returns a list of structured product summaries with full metadata and image URLs.
        """
        filtered = self.df_main.copy()

        if wound_type and wound_type != 'All':
            filtered = filtered[filtered['Wound Type'].str.lower() == wound_type.strip().lower()]

        if indication and indication != 'All':
            filtered = filtered[filtered['Indications (AWC)'].str.lower() == indication.strip().lower()]

        if exudate and exudate != 'All':
            filtered = filtered[filtered['Exudate Level(Mild/ Moderate/ Heavy)'].str.lower() == exudate.strip().lower()]

        if application and application != 'All':
            filtered = filtered[filtered['Application'].str.lower() == application.strip().lower()]

        if dressing_type and dressing_type != 'All':
            filtered = filtered[filtered['Type of Dressing'].str.lower() == dressing_type.strip().lower()]

        if healing_phase and healing_phase != 'All':
            filtered = filtered[filtered['Healing Phase'].str.lower().str.contains(healing_phase.strip().lower(), na=False)]

        unique_product_names = [p for p in filtered['Product Name'].unique() if p]

        results = []
        for pname in unique_product_names:
            details = self.get_product_details(pname)
            # Find matching rows for this specific query to get context
            sub_matches = filtered[filtered['Product Name'] == pname]
            details["match_count"] = len(sub_matches)
            results.append(details)

        return results


# Global singleton instance
_data_manager_instance = None


def get_awc_data_manager() -> AWCDataManager:
    global _data_manager_instance
    if _data_manager_instance is None:
        _data_manager_instance = AWCDataManager()
    return _data_manager_instance
