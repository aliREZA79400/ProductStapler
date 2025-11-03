import os
from pymongo import MongoClient
from typing import Dict, List, Any, Optional 
from datetime import datetime
import json
import re
import pandas as pd

class ProductDataReader:
    """
    A class to read product data from Digikala MongoDB database and convert to pandas DataFrame.
    """
    
    def __init__(self, mongo_uri: str , db_name: str ):
        """
        Initialize the MongoDB connection.
        
        Args:
            mongo_uri: MongoDB connection string
            db_name: Database name
        """
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.products_collection = self.db[PRODUCTS_COLLECTION]
        
    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get basic information about the products collection.
        
        Returns:
            Dictionary containing collection statistics
        """
        try:
            total_docs = self.products_collection.count_documents({})
            sample_doc = self.products_collection.find_one()
            
            return {
                "total_documents": total_docs,
                "sample_document": sample_doc,
                "collection_name": PRODUCTS_COLLECTION,
                "database_name": DB_NAME
            }
        except Exception as e:
            print(f"Error getting collection info: {e}")
            return {}
    
    def get_specifications(self , spec_groups: List[Dict[str, Any]]) -> Dict[str, str]:
        # ---------- helpers ----------
        persian_digits = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
        arabic_digits = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

        def to_ascii(s: Any) -> str:
            if s is None:
                return ""
            s = str(s).translate(persian_digits).translate(arabic_digits)
            return "".join(ch for ch in s if 32 <= ord(ch) <= 126)

        def join_vals(v):
            if not v:
                return ""
            if isinstance(v, (list, tuple)):
                return ", ".join([str(x) for x in v if x is not None])
            return str(v)

        def first_number(text: str) -> str:
            t = to_ascii(text)
            m = re.search(r"(\d+(?:\.\d+)?)", t)
            return m.group(1) if m else ""

        def extract_year(text: str) -> str:
            t = to_ascii(text)
            m = re.search(r"\b(20\d{2}|19\d{2})\b", t)
            return m.group(1) if m else ""

        def extract_size_3nums_mm(text: str) -> str:
            # Replace ×, X, * with x BEFORE to_ascii
            t = re.sub(r"[×X*]", "x", str(text))
            t = to_ascii(t)
            t = re.sub(r"\s*میلی[\u200c\s]*متر\s*", "", t)
            t = re.sub(r"[\u200e\u200f\u202a-\u202e]", "", t)
            nums = re.findall(r"\d+(?:\.\d+)?", t)
            if len(nums) == 3:
                return "x".join(nums)
            return ""

        def extract_inch(text: str) -> str:
            t = to_ascii(text).lower()
            m = re.search(r"(\d+(?:\.\d+)?)\s*(inch|in|'|\")", t)
            if m:
                return m.group(1)
            m = re.search(r"\b(\d+(?:\.\d+)?)\b", t)
            return m.group(1) if m else ""

        # NEW: map Persian category to high/mid/low
        def map_category(value: str) -> str:
            raw = (value or "").replace("\u200c", "").strip().lower()
            # Keep Persian for matching before ASCII stripping
            if any(k in raw for k in ["پرچم", "پرچمدار", "پرچم دار","بالا رده"]):
                return "high"
            if any(k in raw for k in ["ميان رده", "میان رده", "میانرده", "ميان‌رده", "میان‌رده"]):
                return "mid"
            if any(k in raw for k in ["پايين رده", "پایین رده", "پایینرده","اقتصادی"]):
                return "low"
            # English fallbacks
            t = to_ascii(raw)
            if "flagship" in t:
                return "high"
            if "mid" in t:
                return "mid"
            if "low" in t or "entry" in t:
                return "low"
            return ""

        def extract_storage_gb(text: str) -> str:
            t_raw = text or ""
            t = to_ascii(t_raw).lower()

            # TB
            m_tb = re.search(r"\b(\d{1,2})\s*(tb|tib|ترابایت|ترابايت|terabyte|terabytes)\b", t)
            if m_tb:
                gb_val = float(m_tb.group(1)) * 1024
                return str(gb_val)

            # GB
            m_gb = re.search(r"\b(\d{1,4})\s*(gb|gib|گیگابایت|گيگابايت|gigabyte|gigabytes)\b", t)
            if m_gb:
                return str(float(m_gb.group(1)))

            # MB
            m_mb = re.search(r"\b(\d{1,5})\s*(mb|mib|مگابایت|مگابايت)\b", t)
            if m_mb:
                gb_val = float(m_mb.group(1)) / 1024
                return str(round(gb_val, 3))

            # Fallback: Persian-only or number-only (if no unit found)
            n_gb = first_number(t_raw) if "گیگ" in t_raw or "g" in t else ""
            if n_gb:
                return str(float(n_gb))
            n_mb = first_number(t_raw) if "مگ" in t_raw or "m" in t else ""
            if n_mb:
                gb_val = float(n_mb) / 1024
                return str(round(gb_val, 3))
            n_tb = first_number(t_raw) if "ترا" in t_raw or "t" in t else ""
            if n_tb:
                gb_val = float(n_tb) * 1024
                return str(gb_val)

            return ""

        # ---------- flatten spec table ----------
        flat = {}
        try:
            for group in spec_groups if isinstance(spec_groups, list) else []:
                for attr in group.get("attributes", []) or []:
                    t = str(attr.get("title", "")).strip()
                    v = join_vals(attr.get("values", []))
                    if t and v and t not in flat:
                        flat[t] = v
        except Exception:
            pass

        norm = lambda s: str(s).strip().lower()  # noqa: E731
        def vby(keys: List[str]) -> str:
            keys_normed = [norm(x) for x in keys]
            for k in list(flat.keys()):
                if norm(k) in keys_normed:
                    return flat[k]
            return ""

        # ---------- outputs (edited) ----------
        out = {
            "os": "",
            "introduce_date": "",
            "category": "",
            "size": "",
            "weight": "",
            "display_technology": "",
            "refresh_rate": "",
            "size_screen_inch": "",
            "display_to_body_ratio": "",
            "pixel_per_inch": "",
            "cpu_model": "",
            "storage_gb": "",
            "ram_gb": "",
            "internet": "no",
            "camera_num": "",
            "camera_resolution_mp": "",
            "video": "",
            "battery_power_mah": "",        }

        # simple direct
        out["size"] = extract_size_3nums_mm(vby(["ابعاد", "size", "dimension", "dimensions"]))
        out["weight"] = first_number(vby(["وزن", "weight"]))

        # category mapping (high/mid/low)
        cat_raw = vby(["دسته ‌بندی", "دسته بندی", "category"])
        out["category"] = map_category(cat_raw)

        # os
        os_val = to_ascii(vby(["سیستم عامل", "os", "operating system"]))
        if not os_val:
            any_text = to_ascii(" ".join(flat.values())).lower()
            if "android" in any_text:
                os_val = "Android"
            elif "ios" in any_text or "i os" in any_text:
                os_val = "iOS"
        out["os"] = os_val

        # introduce year
        out["introduce_date"] = extract_year(vby(["تاریخ معرفی", "زمان معرفی", "introduce date", "introduction date"]))

        # display
        out["display_technology"] = to_ascii(vby(["فناوری صفحه‌ نمایش", "فناوری صفحه نمایش", "display technology", "panel", "فناوری نمایش"]))
        out["refresh_rate"] = first_number(vby(["نرخ به‌روزرسانی تصویر", "نرخ بروزرسانی", "refresh rate"]))
        out["size_screen_inch"] = extract_inch(vby(["اندازه", "اندازه صفحه", "اندازه صفحه نمایش", "display size"]))
        dbr_txt = vby(["نسبت صفحه‌ نمایش به بدنه", "نسبت نمایشگر به بدنه", "screen-to-body ratio", "display to body ratio"])
        out["display_to_body_ratio"] = first_number(dbr_txt)
        out["pixel_per_inch"] = first_number(vby(["تراکم پیکسلی", "ppi", "pixel density"]))

        # CPU/GPU
        out["cpu_model"] = to_ascii(vby(["تراشه", "چیپست", "chipset", "soc", "پردازنده", "cpu"]))


        # Memory (robust)
        out["storage_gb"] = extract_storage_gb(vby(["حافظه داخلی", "storage", "internal storage"]))
        out["ram_gb"] = extract_storage_gb(vby(["مقدار RAM", "ram", "حافظه رم"]))

      
        # Networks
        nets_txt = " ".join([
            vby(["شبکه‌های مخابراتی", "network", "networks"]),
            vby(["شبکه‌های ارتباطی قابل پشتیبانی", "communication networks"]),
        ])
        def highest_network(text: str) -> str:
            t = to_ascii(text).lower()
            if "5g" in t:
                return "5G"
            if "4g" in t or "lte" in t:
                return "4G"
            if "3g" in t:
                return "3G"
            if "2g" in t:
                return "2G"
            return "no"
        out["internet"] = highest_network(nets_txt)

        # Cameras
        out["camera_num"] = first_number(vby(["تعداد دوربین‌های پشت گوشی", "تعداد دوربین های پشت گوشی", "rear cameras", "number of rear cameras"]))
        out["camera_resolution_mp"] = first_number(vby(["رزولوشن دوربین اصلی", "دوربین اصلی", "main camera resolution"]))

        # Video capability: keep only the single highest resolution@fps found
        video_text = to_ascii(vby(["سایر مشخصات فیلمبرداری", "کیفیت فیلمبرداری", "video", "video recording"]))
        # Keep a spaced version for windowed searches; also a compact version for @fps patterns
        t_sp = video_text.lower().replace("×", "x")
        t_cp = t_sp.replace(" ", "")
        
        # Extract candidates like 8k@60fps, 4k@30fps, 1080p@60fps, 720p@240fps, etc.
        # Special handling: if fps appears as a slash-list (e.g., 30/60fps), choose the MIN (e.g., 30)
        res_tokens = ["8k","6k","5k","4k","4320p","2160p","1440p","1080p","720p","480p"]
        res_rank = {
            "8k": 4320, "6k": 3160, "5k": 2880, "4k": 2160,
            "4320p": 4320, "2160p": 2160, "1440p": 1440,
            "1080p": 1080, "720p": 720, "480p": 480,
        }
        # 1) First capture slash lists and prefer their MIN fps per resolution
        res_to_fps = {}
        slash_patterns = [
            r"(?P<res>(8k|6k|5k|4k))@(?P<fpslist>\d{1,3}(?:/\d{1,3})+)fps",
            r"(?P<res>(4320p|2160p|1440p|1080p|720p|480p))@(?P<fpslist>\d{1,3}(?:/\d{1,3})+)fps",
            r"(?P<res>(8k|6k|5k|4k))\s*\(?(?P<fpslist>\d{1,3}(?:/\d{1,3})+)fps\)?",
            r"(?P<res>(4320p|2160p|1440p|1080p|720p|480p))\s*\(?(?P<fpslist>\d{1,3}(?:/\d{1,3})+)fps\)?",
        ]
        for pat in slash_patterns:
            for m in re.finditer(pat, t_cp):
                res = m.group("res").lower()
                fps_vals = [int(x) for x in m.group("fpslist").split("/") if x]
                if fps_vals:
                    fps_min = min(fps_vals)
                    # store min fps for this res; keep the smallest if multiple slash lists exist
                    if res not in res_to_fps or fps_min < res_to_fps[res]:
                        res_to_fps[res] = fps_min
        
        # 2) Then capture single-fps patterns (only if no slash list decided for that res)
        single_patterns = [
            r"(?P<res>(8k|6k|5k|4k))@(?P<fps>\d{1,3})fps",
            r"(?P<res>(4320p|2160p|1440p|1080p|720p|480p))@(?P<fps>\d{1,3})fps",
            r"(?P<res>(8k|6k|5k|4k))\s*\(?(?P<fps>\d{1,3})fps\)?",
            r"(?P<res>(4320p|2160p|1440p|1080p|720p|480p))\s*\(?(?P<fps>\d{1,3})fps\)?",
        ]
        for pat in single_patterns:
            for m in re.finditer(pat, t_cp):
                res = m.group("res").lower()
                fps = int(m.group("fps"))
                if res not in res_to_fps:
                    res_to_fps[res] = fps
                else:
                    # without slash context, keep the max single fps seen
                    res_to_fps[res] = max(res_to_fps[res], fps)
        
        # 3) Persian-format fallback: after a resolution token, take the next number as fps (if not set yet)
        for rt in res_tokens:
            for m in re.finditer(rf"{rt}", t_sp):
                if rt in res_to_fps:
                    continue
                window = t_sp[m.end(): m.end()+60]
                mnum = re.search(r"(\d{1,3})", window)
                if mnum:
                    try:
                        res_to_fps[rt] = int(mnum.group(1))
                    except Exception:
                        pass
        
        # Choose best by resolution rank, then fps
        if res_to_fps:
            best_res = max(res_to_fps.keys(), key=lambda r: (res_rank.get(r, 0), res_to_fps[r]))
            best_fps = res_to_fps[best_res]
            label = best_res.upper() if best_res.endswith("k") else best_res
            out["video"] = f"{label}@{best_fps}FPS"
        else:
            out["video"] = ""



        # Battery / charging
        out["battery_power_mah"] = first_number(vby(["ظرفیت باتری", "battery capacity"]) or vby(["مشخصات باتری"]))
        # charging_power_w removed; keep if needed as helper:
        # out["charging_power_w"] = watt_number_max(bat_specs)

        # final ASCII clean + field trims
        for k, v in list(out.items()):
            v = to_ascii(v)
            if k in ["internet"]:
                v = v.replace("Lte", "4G")
            out[k] = v.strip()

        return out

    
    def process_suggestions(self, suggestions: Dict) -> Dict[str, float]:
        """
        Process suggestions dictionary into count and percentage features.
        
        Args:
            suggestions: Suggestions dictionary with 'count' and 'percentage' keys
            
        Returns:
            Dictionary with 'suggestions_count' and 'suggestions_percentage' features
        """
        if not suggestions:
            return {"suggestions_count": 0.0, "suggestions_percentage": 0.0}
        
        count = suggestions.get("count", 0)
        percentage = suggestions.get("percentage", 0.0)
        
        return {
            "suggestions_count": float(count),
            "suggestions_percentage": float(percentage)
        }
    

    
    def read_products_to_dataframe(self, 
                                 limit: Optional[int] = None,
                                 filter_query: Optional[Dict] = None,
                                 include_specifications: bool = True) -> pd.DataFrame:
        """
        Read product data from MongoDB and convert to pandas DataFrame.
        
        Args:
            limit: Maximum number of documents to retrieve (None for all)
            filter_query: MongoDB filter query to apply
            include_specifications: Whether to flatten and include specifications
            
        Returns:
            pandas DataFrame containing product data
        """
        try:
            # Build query
            query = filter_query or {}
            
            # Get cursor
            cursor = self.products_collection.find(query)
            if limit:
                cursor = cursor.limit(limit)
            
            # Convert to list
            documents = list(cursor)
            
            if not documents:
                print("No documents found matching the criteria.")
                return pd.DataFrame()
            
            print(f"Retrieved {len(documents)} documents from MongoDB.")
            
            # Process documents
            processed_docs = []
            
            for doc in documents:
                # Basic fields
                processed_doc = {
                    "id" : doc.get("_id"),
                    "brand": doc.get("brand"),
                    "category": doc.get("category"),
                    "price": doc.get("price"),
                    "rate": doc.get("rate"),
                    "count_raters": doc.get("count_raters"),
                    "popularity": doc.get("popularity"),
                    "num_questions": doc.get("num_questions"),
                    "num_comments": doc.get("num_comments"),
                }
                
                # Process complex fields
                # Process suggestions into separate features
                suggestions_data = self.process_suggestions(doc.get("suggestions", {}))
                processed_doc.update(suggestions_data)
                
                
                # Process specifications if requested
                if include_specifications:
                    flattened_specs = self.get_specifications(doc.get("specifications", []))
                    processed_doc.update(flattened_specs)
                
                processed_docs.append(processed_doc)
            
            # Create DataFrame
            df = pd.DataFrame(processed_docs)
            
            # No need to separate features into numeric or other categories
            
            print(f"Created DataFrame with shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            
            return df
            
        except Exception as e:
            print(f"Error reading data from MongoDB: {e}")
            return pd.DataFrame()
    
    def get_data_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Get summary statistics of the DataFrame.
        
        Args:
            df: pandas DataFrame
            
        Returns:
            Dictionary containing summary statistics
        """
        if df.empty:
            return {"error": "DataFrame is empty"}
        
        summary = {
            "shape": df.shape,
            "columns": list(df.columns),
            "missing_values": df.isnull().sum().to_dict(),
            "data_types": df.dtypes.to_dict(),
            "numeric_summary": df.describe().to_dict() if not df.select_dtypes(include=['number']).empty else {},
            "categorical_summary": {}
        }
        
        # Categorical columns summary
        categorical_cols = df.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            if col in df.columns:
                summary["categorical_summary"][col] = {
                    "unique_values": df[col].nunique(),
                    "most_common": df[col].value_counts().head().to_dict()
                }
        
        return summary
    
    def close_connection(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            print("MongoDB connection closed.")


if __name__ == "__main__":

    # Configuration
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DB_NAME = "digikala"
    PRODUCTS_COLLECTION = "products"
    reader = ProductDataReader(mongo_uri=MONGO_URI,db_name=DB_NAME)

    try:
    # Get collection info
        print("=== Collection Information ===")
        info = reader.get_collection_info()
        print(f"Total documents: {info.get('total_documents', 'Unknown')}")
        print(f"Database: {info.get('database_name', 'Unknown')}")
        print(f"Collection: {info.get('collection_name', 'Unknown')}")
        

        print("=== Random Sample Specifications ===")
        pipeline = [
            {"$match": {}},
            {"$sample": {"size":1}},
            {"$project": {"_id": 1, "title_en": 1, "title_fa": 1, "specifications": 1}},
        ]
        for i, doc in enumerate(reader.products_collection.aggregate(pipeline), 1):
            print(f"\n--- Sample #{i} ---")
            print(f"_id: {doc.get('_id')}")
            print(f"title_en: {doc.get('title_en') or ''}")
            print(f"title_fa: {doc.get('title_fa') or ''}")

            # Original specification data (as stored)
            print("Original specifications:")
            print(json.dumps(doc.get("specifications", []), indent=2, ensure_ascii=False))

            spec = reader.get_specifications(doc.get("specifications", []))
            print("Normalized specifications:")
            print(json.dumps(spec, indent=2, ensure_ascii=True))

        
        print("=== Reading Product Data ===")
        mobile = reader.read_products_to_dataframe()  
        
        if not mobile.empty:            
            # Get summary
            print("=== Data Summary ===")
            summary = reader.get_data_summary(mobile)

            
            # Save to CSV (optional)
            output_file = f"ml/dataset/digikala_products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            mobile.to_csv(output_file, index=False, encoding='utf-8')
            print(f"Data saved to: {output_file}")
            
        else:
            print("No data retrieved.")
            
    except Exception as e:
        print(f"Error: {e}")

    finally:
        # Close connection
        reader.close_connection()
