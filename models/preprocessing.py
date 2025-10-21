import pandas as pd
import numpy as np
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer, OrdinalEncoder, OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.model_selection import train_test_split
import os
import re


def find_latest_csv(data_dir, prefix="digikala_products_", postfix=".csv"):
    """
    Finds the latest CSV file in the given directory based on timestamp in the filename.
    Example filename: digikala_products_20251010_091958.csv
    """
    pattern = re.compile(rf"{re.escape(prefix)}(\d{{8}}_\d{{6}}){re.escape(postfix)}")
    candidates = []
    for fname in os.listdir(data_dir):
        m = pattern.fullmatch(fname)
        if m:
            candidates.append((m.group(1), fname))
    if not candidates:
        return None
    # Sort by timestamp string (YYYYMMDD_HHMMSS)
    latest = max(candidates, key=lambda x: x[0])
    return os.path.join(data_dir, latest[1])


def get_dataframe_from_csv(csv_file):
    """
    Reads a CSV file and returns a pandas DataFrame.
    
    Args:
        csv_file (str): Path to the CSV file.
        
    Returns:
        pd.DataFrame: DataFrame containing the CSV data.
    """
    try:
        df = pd.read_csv(csv_file)
        return df
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return pd.DataFrame()


def create_engagement_score(df):
    """
    Creates a composite engagement score from multiple metrics.
    Normalizes each metric to 0-1 scale and combines with weights.
    """
    # Create a copy to avoid modifying original
    df = df.copy()
    
    # Fill NaN values with 0 for these metrics
    engagement_cols = ['rate', 'count_raters', 'popularity', 'num_questions', 'num_comments']
    df[engagement_cols] = df[engagement_cols].fillna(0)
    
    # Normalize each metric to 0-1 scale
    for col in engagement_cols:
        max_val = df[col].max()
        if max_val != 0:  # Avoid division by zero
            df[f'{col}_norm'] = df[col] / max_val
        else:
            df[f'{col}_norm'] = 0
            
    # Create weighted sum
    # Popularity gets highest weight (0.4) since it's most important
    # Rate and count_raters get 0.2 each
    # Questions and comments get 0.1 each
    df['engagement_score'] = (
        0.3 * df['popularity_norm'] +
        0.15 * df['rate_norm'] +
        0.15 * df['count_raters_norm'] +
        0.2 * df['num_questions_norm'] +
        0.2 * df['num_comments_norm']
    )
    
    # Bin the engagement scores into categories
    bins = [-np.inf, 0.2, 0.4, 0.6, 0.8, np.inf] #TODO apply other bins np.inf
    labels = ['very_low', 'low', 'medium', 'high', 'very_high']
    
    df['engagement_level'] = pd.cut(
        df['engagement_score'], 
        bins=bins, 
        labels=labels
    )
    
    # Clean up temporary columns
    df = df.drop([col + '_norm' for col in engagement_cols], axis=1)
    
    return df['engagement_level']


# Extract size features
def extract_size_features(size_str):
    """
    Parse the 'size' string (e.g. '160x75x8.5') and return (thickness, volume).
    Returns (np.nan, np.nan) if parsing fails.
    """
    try:
        # Ensure string and remove spaces
        parts = str(size_str).replace(" ", "").split("x")
        if len(parts) != 3:
            return np.nan, np.nan
        nums = [float(p) for p in parts]
        thickness = min(nums)
        volume = nums[0] * nums[1] * nums[2]
        volume_cm3 = volume / 1000
        return thickness, volume_cm3
    except Exception:
        return np.nan, np.nan

def Initial_Transformation(file_path:str=None , test_size:int = 0.3,cpu_clusters:int =6):

    # Load data
    file = find_latest_csv(file_path)
    df = get_dataframe_from_csv(file)

    # Process rare brands
    brand_counts = df['brand'].value_counts()
    rare_brands = brand_counts[brand_counts <= 2].index.tolist()
    replacement_name = 'other'
    df["brand"] = df['brand'].replace(rare_brands, replacement_name)

    # Train-test split
    mobile, mobile_test = train_test_split(df, stratify=df["brand"], test_size=test_size, random_state=42)

    # CPU
    # Fill NaN values with a placeholder string and convert to lowercase
    mobile['cpu_cats'] = mobile['cpu_model'].fillna('UnKnown')

    # Initialize TF-IDF Vectorizer
    vectorizer = TfidfVectorizer(stop_words=None, token_pattern=r'\b\w+\b')

    # Fit and transform the text data
    tfidf_matrix = vectorizer.fit_transform(mobile['cpu_cats'])


    # --- 3. Dimensionality Reduction (PCA) ---

    # This makes clustering faster and often more stable.
    pca = PCA(n_components=50, random_state=42) # Choosing 50 components as a reasonable number
    tfidf_reduced = pca.fit_transform(tfidf_matrix.toarray())

    # Determine the number of clusters (K).
    # Based on the data, we expect around 5-7 brands (MediaTek, Qualcomm, Exynos, Apple, Unisoc, Other, Missing)
    K = cpu_clusters

    kmeans = KMeans(n_clusters=K, random_state=42, n_init="auto")

    # Fit K-Means to the data
    mobile['cpu_cats'] = kmeans.fit_predict(tfidf_reduced)


    mobile['engagement_level'] = create_engagement_score(mobile)

    mobile[["thickness", "volume"]] = mobile["size"].apply(lambda x: pd.Series(extract_size_features(x)))

    # Create density feature
    mobile["density"] = mobile["weight"] / mobile["volume"]

    # Drop size feature
    mobile = mobile.drop(columns=["size"])
    
    #TODO delete this after change the csv file
    mobile = mobile.drop(columns=["color_diversity"])

    mobile["introduce_date"] = mobile["introduce_date"].astype("str")

    bins_display_to_body_ratio = [0, 50, 89, 100]
    labels = ['low', 'mid', 'high']

    mobile["display_to_body_ratio"] = pd.cut(
        mobile["display_to_body_ratio"],
        bins=bins_display_to_body_ratio,
        labels=labels,
        ordered=False
    )

    bins_display_refresh_rate = [0, 50, 60, 180]

    mobile["refresh_rate"] = pd.cut(
        mobile["refresh_rate"],
        bins=bins_display_refresh_rate,
        labels=labels,
        ordered=False
    )


    mobile["all_pixels"] = mobile["pixel_per_inch"].astype("float64") * mobile["size_screen_inch"].astype("float64")


    # 1. Define the Bin Boundaries (BINS) and Labels
    bins_price = [-np.inf, 50_000_000,100_000_000 ,150_000_000,200_000_000,300_000_000,500_000_000,1000_000_000,1500_000_000,2000_000_000,np.inf]
    labels_price = ['0', '1', '2','3','4','5','6','7','8','9']

    # 2. Apply the cut function
    mobile["price_cat"] = pd.cut(
        mobile["price"],
        bins=bins_price,
        labels=labels_price,
        ordered=True
    )

    return mobile , mobile_test


# ============================================================
#  Feature Pipeline
# ============================================================

def apply_category_rules(X):
    """
    Apply business rules to assign 'low' category based on conditions.
    Input: DataFrame with columns ['category', 'cpu_model', 'ram_gb', 'storage_gb', 'internet', 'price']
    Output: DataFrame with single column ['category']
    """
    X = X.copy()
    
    # Create mask for conditions
    mask = (
        X["cpu_model"].isna() |
        (X["ram_gb"] < 2.) |
        (X["storage_gb"] < 64.) |
        ((X["internet"] == "2G") | (X["internet"] == "3G")) |
        (X["price"] < 150_000_000)
    )
    
    # Assign 'low' to rows matching the mask
    X.loc[mask, "category"] = "low"
    
    # Return only the category column
    return X[["category"]]


def get_category_feature_names(transformer, feature_names_in):
    """Return feature name for the category column."""
    return ["category"]


def category_pipeline():
    """
    Pipeline for category feature:
    """
    return make_pipeline(
        FunctionTransformer(
            apply_category_rules,
            feature_names_out=get_category_feature_names
        ),
        OrdinalEncoder(
            categories=[['low', 'mid', 'high']],
            handle_unknown='use_encoded_value',
            unknown_value=-1,
            encoded_missing_value=-1
        )
    )

# ============================================================


def onehot_pipeline():
    """
    Pipeline for os and introduce_date features:
    - SimpleImputer to fill NaN with "UnKnown"
    - OneHotEncoder
    """
    return make_pipeline(
        SimpleImputer(strategy='constant', fill_value='UnKnown'),
        OneHotEncoder(handle_unknown='ignore')
    )


# ============================================================


def apply_log_transform_thickness(X):
    """Apply log transformation to thickness."""
    X = X.copy()
    X["thickness"] = np.log(X["thickness"])
    return X


def log_pipeline():
    """
    Pipeline for thickness feature:
    - Apply log transform
    - Apply StandardScaler
    """
    return make_pipeline(
        FunctionTransformer(apply_log_transform_thickness),
        SimpleImputer(),
        StandardScaler()
    )


# ============================================================


def volume_pipeline():
    """
    Pipeline for volume feature:
    - Apply StandardScaler
    """
    return make_pipeline(
        SimpleImputer(),
        StandardScaler()
    )


# ============================================================


def apply_log_transform_density(X):
    """Apply log transformation to density."""
    X = X.copy()
    X["density"] = np.log(X["density"])
    return X



def ordinal_pipeline():
    return make_pipeline(
        OrdinalEncoder(
            categories=[['low', 'mid', 'high']],
            handle_unknown='use_encoded_value',
            unknown_value=-1,
            encoded_missing_value=-1
        ))

def internet_pipeline():
    return make_pipeline(
        OrdinalEncoder(
            categories=[['no', '2G', '3G','4G','5G']],
            handle_unknown='use_encoded_value',
            unknown_value=-1,
            encoded_missing_value=-1
            
        ))


def mean_pipeline():
    return make_pipeline(
        SimpleImputer(),
        StandardScaler()
    )

def ordinal_zero_fill_pipeline():
    return make_pipeline(
        SimpleImputer(strategy="constant",fill_value=0),
        OrdinalEncoder()
    )

def video_pipeline():
    return make_pipeline(
        OrdinalEncoder(
            categories=[[
                '480p@15FPS',
                '720p@30FPS',
                '720p@480FPS' #TODO solve
                '1080p@30FPS',
                "1080p@720FPS" #TODO solve
                '1440p@30FPS', # 1440p is usually 2.5K
                '1080p@60FPS',
                '4K@24FPS',
                '2160p@30FPS', # Alias for 4K
                '4K@30FPS',
                '4K@60FPS',
                '4K@120FPS',
                '8K@24FPS', 
                '8K@30FPS',
            ]],
            handle_unknown='use_encoded_value',
            unknown_value=-1,
            encoded_missing_value=-1
        ))

def engagement_pipeline():
    return make_pipeline(
        OrdinalEncoder(
            categories=[['very_low', 'low', 'medium', 'high', 'very_high']],
            handle_unknown='use_encoded_value',
            unknown_value=-1,
            encoded_missing_value=-1
        )
    )
def price_pipeline():
    return make_pipeline(
            OrdinalEncoder(
            categories=[['0', '1', '2','3','4','5','6','7','8','9']],
            handle_unknown='use_encoded_value',
            unknown_value=-1,
            encoded_missing_value=-1
        ))


#TODO add features names

# ============================================================
# Main Preprocessing Pipeline
# ============================================================

def Preprocessor():

    return ColumnTransformer(
        transformers=[
            ("category", category_pipeline(), ["category", "cpu_model", "ram_gb", "storage_gb", "internet", "price"]),
            ("onehot", onehot_pipeline(), ["os", "introduce_date","display_technology","cpu_cats","brand"]),
            ("thickness", log_pipeline(), ["thickness","density"]),
            ("volume", volume_pipeline(), ["volume"]),
            ("display_to_body_ratio",ordinal_pipeline(),["display_to_body_ratio"]),
            ("refresh_rate",ordinal_pipeline(),["refresh_rate"]),
            ("mean",mean_pipeline(),["size_screen_inch","pixel_per_inch","all_pixels","battery_power_mah",'rate', 'count_raters', 'popularity', 'num_questions', 'num_comments',"suggestions_count",'suggestions_percentage']),
            ("ordinal_zero_fill",ordinal_zero_fill_pipeline(),["storage_gb","ram_gb","camera_num","camera_resolution_mp"]),
            ("internet",internet_pipeline(),["internet"]),
            ("video",video_pipeline(),["video"]),
            ("price_cat",price_pipeline(),["price_cat"]),
            ("engagement_level",engagement_pipeline(),["engagement_level"])
        ],
        remainder='drop'  
    )


    



if __name__ == "__main__":
    # Fit and transform
    mobile , _ = Initial_Transformation()
    preprocessing = Preprocessor()

    preprocessing.fit(mobile)
    transformed = preprocessing.transform(mobile)
    
    print("=" * 60)
    print("FEATURE TRANSFORMATION RESULTS")
    print("=" * 60)
    
   
    print(transformed[50:60])
    print(transformed.shape)
