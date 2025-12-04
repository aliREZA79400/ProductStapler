# Machine Learning Pipeline - Product Clustering System

This directory contains a comprehensive machine learning pipeline for clustering mobile phone products using hierarchical nested clustering approaches. The system extracts features from product specifications, applies sophisticated preprocessing, and builds multi-level clustering models to categorize products into hierarchical groups.

## Overview

The ML pipeline is designed to:

1. **Extract** product data from MongoDB with rich specification parsing
2. **Transform** raw product data into machine-readable features using advanced preprocessing
3. **Cluster** products using hierarchical nested clustering algorithms
4. **Deploy** trained models and automatically update product cluster assignments

The system uses a three-level hierarchical clustering approach to organize products into progressively more specific categories, enabling fine-grained product categorization and recommendation systems.

## Key Features

### 📊 Data Extraction & Feature Engineering

#### Dataset Module (`dataset.py`)

The `ProductDataReader` class handles sophisticated data extraction from MongoDB with intelligent specification parsing:

- **Persian/Arabic Text Processing**: Converts Persian and Arabic digits to ASCII, handles RTL text encoding
- **Specification Extraction**: Parses nested JSON specifications using keyword matching in both Persian and English
- **Field Extraction**:
  - **Category Mapping**: Maps Persian product categories (پرچمدار, میان‌رده, پایین‌رده) to standardized levels (high/mid/low)
  - **CPU/GPU Models**: Extracts chipset information with text normalization
  - **Display Features**: Screen size, refresh rate, pixel density, display-to-body ratio
  - **Memory**: RAM and storage extraction with unit conversion (GB/TB/MB)
  - **Network Support**: Highest supported network generation (5G/4G/3G/2G)
  - **Camera**: Number of cameras and main camera resolution
  - **Video Recording**: Extracts highest video recording capability (8K@60FPS, 4K@30FPS, etc.)
  - **Battery**: Battery capacity in mAh
  - **Physical Dimensions**: Size parsing (160x75x8.5mm) to extract thickness and volume

- **Business Logic Rules**: Applies rules to assign product categories based on specifications (e.g., devices with <2GB RAM assigned to "low" category)

#### Feature Engineering (`preprocessing.py`)

The preprocessing pipeline performs comprehensive feature transformation:

1. **CPU Model Clustering**:
   - Uses TF-IDF vectorization to convert CPU model names to numerical features
   - Applies PCA for dimensionality reduction (50 components)
   - Clusters CPU models into categories using K-Means (default: 6 clusters)
   - Groups similar processors (e.g., Snapdragon variants) together

2. **Engagement Score Creation**:
   - Composite score combining: ratings, number of raters, popularity, questions, comments
   - Weighted combination: popularity (30%), rate (15%), count_raters (15%), questions (20%), comments (20%)
   - Bins scores into categories: very_low, low, medium, high, very_high

3. **Feature Transformations**:
   - **Size Parsing**: Extracts thickness (minimum dimension) and volume (L×W×H)
   - **Density Calculation**: Weight-to-volume ratio
   - **Log Transformations**: Applied to thickness and density for normalization
   - **Binning**: Categorical binning for display-to-body ratio, refresh rate, price categories
   - **Derived Features**: All pixels (PPI × screen size), price categories (10 bins)

4. **Preprocessing Pipeline**:
   - **Category Pipeline**: Business rules + Ordinal encoding
   - **One-Hot Encoding**: OS, introduction date, display technology, CPU categories, brand
   - **Log + StandardScaler**: Thickness and density
   - **StandardScaler**: Volume, screen features, battery, engagement metrics
   - **Ordinal Encoding**: Display ratios, refresh rates, engagement levels, price categories, internet support, video capabilities
   - **Imputation**: Missing value handling with strategies (mean, constant, zero-fill)

**Output**: 98-dimensional feature vector ready for clustering

### 🎯 Hierarchical Clustering Models

The system implements two sophisticated clustering approaches developed in the model development notebook:

#### 1. Flexible Nested Clustering System

A flexible three-level clustering system that allows different algorithms at each level:

- **Level 1**: Top-level clusters (broad categories)
- **Level 2**: Sub-clusters within each Level 1 cluster
- **Level 3**: Final clusters within each Level 2 cluster

**Supported Algorithms**:

- `AgglomerativeClustering`: Hierarchical clustering with various linkage methods (ward, complete, average, single)
- `KMeans`: Partitioning-based clustering
- `MiniBatchKMeans`: Scalable K-Means variant
- `SpectralClustering`: Graph-based clustering

**Key Features**:

- Configurable algorithm per level
- Minimum samples threshold per final cluster (prevents over-fragmentation)
- Automatic hierarchy building with sample assignments
- Detailed hierarchy summary with sample statistics

**Example Configuration**:

```python
level1_config = {
    'algorithm': 'AgglomerativeClustering',
    'n_clusters': 5,
    'linkage': 'complete'
}
level2_config = {
    'algorithm': 'KMeans',
    'n_clusters': 3,
    'random_state': 42
}
level3_config = {
    'algorithm': 'KMeans',
    'n_clusters': 5,
    'random_state': 42
}
```

#### 2. Fixed Single Model Hierarchical Clustering

Uses a single hierarchical clustering model with linkage matrix preservation:

- **Linkage Matrix**: Saves the complete merging process from hierarchical clustering
- **Multi-Level Extraction**: Extracts clusters at different hierarchy levels using `fcluster`
- **Sub-Linkage Creation**: Creates separate linkage matrices for sub-clusters
- **Ward Linkage**: Default method for balanced cluster sizes

**Key Features**:

- Preserves hierarchical relationships through linkage matrix
- More interpretable dendrogram visualization
- Better for understanding product relationships

**Configuration**:

- Level 1 clusters: Top-level groupings
- Level 2 clusters: Sub-groupings within each Level 1 cluster
- Level 3 clusters: Final granular clusters
- Linkage method: ward, complete, average, or single

### 📈 Model Evaluation Metrics

The system calculates multiple clustering quality metrics:

1. **Silhouette Score**: Measures cluster cohesion and separation (-1 to 1, higher is better)
   - Calculated at each level and averaged across levels

2. **Davies-Bouldin Index**: Average similarity ratio of clusters (lower is better)
   - Measures intra-cluster distance vs inter-cluster distance

3. **Calinski-Harabasz Index**: Ratio of between-cluster to within-cluster variance (higher is better)
   - Also known as Variance Ratio Criterion

**Nested Metric Calculation**:

- Metrics computed separately for Level 1, Level 2, and Level 3
- Level 2/3 metrics aggregated across all sub-clusters
- Overall average provides holistic view of clustering quality

### 🔬 MLflow Integration

The system uses MLflow for experiment tracking and model management:

- **Experiment Tracking**: Separate experiments for different clustering approaches (K-means, Linkage)
- **Model Registry**: Versioned model storage and retrieval
- **Parameter Logging**: All clustering configurations logged as parameters
- **Metric Logging**: Clustering quality metrics tracked per experiment
- **Model Artifacts**: Complete model objects saved for deployment

**Model Deployment**:

- Models loaded from MLflow Model Registry by name and version
- Supports model versioning and A/B testing
- Automatic model loading with configuration

### 🚀 Automated Model Deployment

The `model.py` module handles automated cluster assignment updates:

- **Model Loading**: Loads trained clustering model from MLflow registry
- **Batch Updates**: Updates MongoDB products with cluster assignments
- **Prediction Fallback**: For new products not in training data, uses nearest-neighbor prediction
- **Async MongoDB Operations**: Efficient async updates using Motor driver

**Cluster Assignment Structure**:

```python
{
    "level1_id": 0,  # Top-level category
    "level2_id": 2,  # Sub-category
    "level3_id": 1   # Final cluster
}
```

## Project Structure

```text
ml/
├── README.md              # This file
├── dataset.py             # MongoDB data extraction and specification parsing
├── preprocessing.py       # Feature engineering and transformation pipelines
├── model.py              # Model deployment and cluster assignment updates
├── config.py             # Configuration management
├── start.sh              # MLflow server startup script
├── crontab               # Scheduled model updates
├── Dockerfile            # Container configuration
├── requirements.txt      # Python dependencies
└── dataset/              # Extracted CSV datasets
    └── digikala_products_*.csv
```

## Workflow

### 1. Data Extraction (`dataset.py`)

```python
from ml.dataset import ProductDataReader

reader = ProductDataReader(mongo_uri, db_name)
df = reader.read_products_to_dataframe(limit=None)
df.to_csv("dataset/digikala_products_TIMESTAMP.csv")
```

**Process**:

- Connects to MongoDB products collection
- Extracts and flattens nested specifications
- Parses Persian/English text fields
- Converts to pandas DataFrame
- Saves timestamped CSV file

### 2. Feature Preprocessing (`preprocessing.py`)

```python
from ml.preprocessing import Initial_Transformation, Preprocessor

# Load and transform data
mobile, df = Initial_Transformation(file_path="dataset", cpu_clusters=6)

# Create and fit preprocessing pipeline
preprocessor = Preprocessor()
preprocessor.fit(mobile)

# Transform to feature vectors
X_transformed = preprocessor.transform(mobile)
```

**Process**:

- Loads latest CSV from dataset directory
- Applies feature engineering (CPU clustering, engagement scores, etc.)
- Fits preprocessing pipeline
- Outputs 98-dimensional feature matrix

### 3. Model Training (Development Notebook)

Model development happens in `lab/model_development.ipynb`:

**K-Means Nested Clustering**:

```python
from lab.model_development import FlexibleNestedClusteringSystem

model = FlexibleNestedClusteringSystem(
    level1_config={'algorithm': 'KMeans', 'n_clusters': 3},
    level2_config={'algorithm': 'KMeans', 'n_clusters': 4},
    level3_config={'algorithm': 'KMeans', 'n_clusters': 5},
    original_data=mobile
)

model.fit(X_transformed)
metrics = calculate_all_clustering_metrics(model, X_transformed)
```

**Hierarchical Linkage Clustering**:

```python
from lab.model_development import FixedSingleModelHierarchicalClustering

model = FixedSingleModelHierarchicalClustering(
    n_level1_clusters=3,
    n_level2_clusters=4,
    n_level3_clusters=5,
    linkage_method='ward',
    original_data=mobile
)

model.fit(X_transformed)
```

**MLflow Logging**:

```python
import mlflow

with mlflow.start_run():
    mlflow.log_params(config)
    mlflow.log_metrics(metrics)
    mlflow.sklearn.log_model(model, artifact_path="model")
```

### 4. Model Deployment (`model.py`)

```python
from ml.model import update_products_cluster_info

# Automatically loads model from MLflow registry
# Updates MongoDB products with cluster assignments
await update_products_cluster_info()
```

**Process**:

- Loads model from MLflow registry (configurable name/version)
- Queries MongoDB for products without cluster_info
- For each product:
  - If in training data: uses pre-computed cluster assignment
  - If new product: predicts using nearest-neighbor approach
- Updates MongoDB documents with cluster_info field

### 5. Automated Scheduling

The system supports automated updates via cron:

```bash
# Runs model.py daily at 6:23 AM
23 6 * * * cd /app && python3 -m ml.model
```

This ensures cluster assignments stay up-to-date as new products are added.

## Configuration

All configuration is managed through environment variables:

- **MLflow Configuration**:
  - `MLFLOW_TRACKING_URI`: MLflow server URL (default: `http://localhost:5000`)
  - `MODEL_NAME`: Model name in MLflow registry
  - `MODEL_VERSION`: Model version to deploy

- **MongoDB Configuration**:
  - `MONGO_URI`: MongoDB connection string
  - `DB_NAME`: Database name
  - `PRODUCTS_COLLECTION`: Products collection name

See `config.py` for configuration loading.

## Model Development Notebook

The `lab/model_development.ipynb` notebook contains:

1. **Data Loading**: Product data loading and initial exploration
2. **Preprocessing**: Feature transformation pipeline demonstration
3. **MLflow Setup**: Experiment tracking configuration
4. **Flexible Clustering System**: Implementation and testing
5. **Metrics Calculation**: Clustering quality evaluation functions
6. **Experiments**:
   - **K-Means Experiment**: 3-level K-Means nested clustering
   - **Linkage Experiment**: Hierarchical clustering with ward linkage
7. **Model Logging**: MLflow integration for model versioning

**Key Notebook Components**:

- `FlexibleNestedClusteringSystem`: Multi-algorithm nested clustering
- `FixedSingleModelHierarchicalClustering`: Single hierarchical model with linkage preservation
- Metric calculation functions for nested clustering evaluation
- Visualization of cluster hierarchies and sample assignments

## Usage Examples

### Extract Data from MongoDB

```bash
python -m ml.dataset
```

Outputs CSV file to `dataset/` directory with timestamp.

### Run Preprocessing Pipeline

```bash
python -m ml.preprocessing
```

Fits and transforms data, prints feature transformation results.

### Deploy Model and Update Cluster Assignments

```bash
python -m ml.model
```

Loads model from MLflow and updates MongoDB products.

### Start MLflow Server

```bash
./start.sh
```

Starts MLflow server on port 5000 for experiment tracking.

## Clustering Hierarchy Example

The three-level hierarchy enables fine-grained product organization:

```text
Level 1 Cluster 0: Budget Phones (109 samples)
  Level 2 Cluster 0: Basic Models (16 samples)
    Level 3 Cluster 0: Entry-level (1 sample)
    Level 3 Cluster 1: Standard (8 samples)
    Level 3 Cluster 2: Enhanced (3 samples)
  Level 2 Cluster 1: Mid-Range Budget (40 samples)
    Level 3 Cluster 0: Feature-rich (8 samples)
    Level 3 Cluster 1: Balanced (7 samples)
    ...

Level 1 Cluster 1: Premium Phones (225 samples)
  Level 2 Cluster 0: Flagship Models (54 samples)
    ...
```

This hierarchy enables:

- **Recommendation Systems**: Find similar products at different granularities
- **Market Segmentation**: Analyze product categories at multiple levels
- **Search Enhancement**: Filter products by cluster hierarchy
- **Price Analysis**: Compare products within same cluster levels

## Performance Characteristics

### Feature Engineering

- **CPU Clustering**: Groups 100+ unique CPU models into 6 categories
- **Feature Dimensionality**: 98 features after transformation
- **Missing Value Handling**: Robust imputation strategies for all feature types
- **Processing Time**: ~2-5 seconds for 500 products

### Clustering Performance

Typical clustering results (from development notebook):

- **Level 1 Silhouette Score**: ~0.40 (good separation)
- **Average Silhouette Score**: ~0.27-0.32 (acceptable for nested clustering)
- **Final Clusters**: 50-60 clusters for ~500 products
- **Average Samples per Cluster**: 8-10 products

### Model Deployment

- **Update Speed**: ~100-200 products/second
- **Memory Usage**: ~200-500MB (depends on model size)
- **Prediction Time**: <1ms per product for nearest-neighbor prediction

## Dependencies

Key dependencies (see `requirements.txt` for full list):

- `pandas`: Data manipulation
- `numpy`: Numerical computations
- `scikit-learn`: Machine learning algorithms and preprocessing
- `mlflow`: Experiment tracking and model registry
- `motor`: Async MongoDB driver
- `pymongo`: MongoDB operations
- `python-decouple`: Configuration management

## Future Enhancements

Potential improvements:

- **Incremental Learning**: Update clusters as new products arrive
- **Alternative Algorithms**: DBSCAN, Gaussian Mixture Models, etc.
- **Feature Selection**: Automatically identify most important features
- **Hyperparameter Optimization**: Automated tuning of cluster numbers
- **Real-time Prediction**: API endpoint for cluster prediction
- **Visualization**: Interactive dendrograms and cluster exploration
- **Multi-model Ensemble**: Combine multiple clustering approaches

## Troubleshooting

### Common Issues

1. **Missing MLflow Server**:
   - Ensure MLflow server is running: `./start.sh`
   - Check `MLFLOW_TRACKING_URI` in configuration

2. **Model Not Found**:
   - Verify `MODEL_NAME` and `MODEL_VERSION` in config
   - Check MLflow registry for available models

3. **Preprocessing Errors**:
   - Ensure CSV file exists in `dataset/` directory
   - Check for missing required columns in data

4. **MongoDB Connection**:
   - Verify `MONGO_URI` is correct
   - Check network connectivity to MongoDB server
