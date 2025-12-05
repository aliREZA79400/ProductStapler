# Stapler - Product Clustering & Categorization System

<div align="center">

![alt text](images/mangane_main_page.png)

</div>

Stapler is the answer to this question.

What if instead of pagination of products, we could see them categorized and make a more targeted and intelligent choice?

This Project is an end-to-end system from web scraping to hierarchical product browsing. The project implements a complete data pipeline from extraction to deployment, featuring async web scraping, hierarchical clustering models, REST API, and a modern React frontend.


## Project Overview

Stapler is a full-stack application that:

1. **Scrapes** product data from web APIs using high-performance async operations
2. **Clusters** products using hierarchical nested clustering algorithms
3. **Serves** clustered products through a REST API with hierarchical navigation
4. **Displays** products in a modern web interface with authentication

The system is designed with a microservices architecture, fully containerized with Docker Compose, and implements production-ready patterns for scalability and maintainability.

## System Architecture

```text
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │◀────│    Backend   │◀────│   MongoDB   │◀────│Data Pipeline│
│   (React)   │     │   (FastAPI)  │     │             │     │             │
└─────────────┘     └──────────────┘     └─────────────┘     └─────────────┘
                                                ▲
                                                │
                                        ┌───────┴──────┐
                                        │  ML Pipeline │
                                        │   (MLflow)   │
                                        └──────────────┘
```
## AI Use Note
The entire frontend section is written with LLM (Claude 4.5). Other sections are used for documentation, cleaning, test writing, and using hints.


### Data Flow

1. **Data Pipeline** → Scrapes products → Stores in MongoDB
2. **ML Pipeline** → Reads from MongoDB → Clusters products → Updates MongoDB with cluster assignments
3. **Backend API** → Reads clustered products → Serves hierarchical endpoints
4. **Frontend** → Consumes API → Displays products in hierarchical categories

## Initianl Setup

in project root :

1. docker compose up -d mongodb

2. docker compose up -d data-pipeline

3. check the http://localhost:4200 and run the flow manually for the first time.

4. docker compose up -d mlflow 

5. train the model in lab/model_development.ipynb  and register the model in mlflow.

6. for initial model setup run this command in mlflow container:

docker exec -it mlflow bash

```python3 -m ml.model```

7. docker compose up -d backend frontend


## Project Components

### 📊 Data Pipeline (`data/`)

<div align="center">

![alt text](images/prefect.png)

</div>

**Purpose**: Async web scraping and ETL pipeline for product data extraction and loading.

**Key Features**:

- **Async Web Scraping**: Concurrent HTTP requests using `asyncio` and `httpx`
  - Semaphore-controlled concurrency (5 concurrent requests)
  - Concurrent brand and product processing
  - Pagination handling with concurrent page fetching
- **Async MongoDB Loading**: Motor driver with chunked processing
  - Hybrid model: async I/O + process pools for CPU-bound transformations
  - Producer-consumer pattern for concurrent chunk processing
- **Prefect Automation**: Scheduled pipeline execution
  - Daily automated runs at 2:00 AM UTC
  - Workflow orchestration and monitoring
  - Automatic retry mechanisms

**Key Files**:

- `brand_ex.py`: Brand extraction with concurrent processing
- `product_ex.py`: Product/comment extraction with dual-mode operation
- `etl.py`: Async ETL with chunked MongoDB loading
- `pipeline.py`: Prefect flow orchestration

**Performance**: Processes hundreds of products concurrently, reducing scraping time from hours to minutes.

**See**: [`data/README.md`](data/README.md) for detailed documentation.

### 🤖 Machine Learning Pipeline (`ml/`)

<div align="center">

![alt text](images/mlflow.png)

</div>

**Purpose**: Product clustering using hierarchical nested clustering algorithms.

**Key Features**:

- **Feature Engineering**: Advanced preprocessing pipeline
  - Persian/Arabic text processing and normalization
  - CPU model clustering using TF-IDF + PCA + K-Means
  - Engagement score creation (composite metric)
  - 98-dimensional feature vector output
- **Hierarchical Clustering**: Three-level nested clustering
  - **Flexible Nested System**: Multi-algorithm support (K-Means, Agglomerative, Spectral)
  - **Fixed Hierarchical System**: Linkage matrix-based clustering
  - Level 1 → Level 2 → Level 3 hierarchical structure
- **MLflow Integration**: Experiment tracking and model registry
  - Versioned model storage
  - Metric tracking (Silhouette, Davies-Bouldin, Calinski-Harabasz)
- **Automated Deployment**: Scheduled cluster assignment updates
  - Daily updates via cron (6:23 AM)
  - Nearest-neighbor prediction for new products

**Key Files**:

- `dataset.py`: MongoDB data extraction with specification parsing
- `preprocessing.py`: Feature engineering pipelines
- `model.py`: Model deployment and cluster assignment updates

**Output**: Products organized into hierarchical clusters (Level 1 → Level 2 → Level 3).

**See**: [`ml/README.md`](ml/README.md) for detailed documentation.

### 🔌 Backend API (`backend/`)

**Purpose**: REST API for hierarchical product retrieval and user authentication.

**Key Features**:

- **Hierarchical Endpoints**: Three-level clustering navigation
  - `GET /`: Sample products by Level 1 clusters
  - `GET /sub/{level1_id}`: Sample products by Level 2 clusters
  - `GET /sub/{level1_id}/sub-sub/{level2_id}`: Sample products by Level 3 clusters
- **Router-Based Architecture**: Modular FastAPI design
  - `/auth/*`: OAuth2 authentication endpoints
  - `/product/*`: Product retrieval endpoints
- **Async Operations**: Fully async MongoDB operations with Motor
- **Configurable Field Filtering**: Selective field exposure via `KEYS_TO_SHOW`
- **OAuth2 Security**: JWT token authentication with Argon2 password hashing

**Key Files**:

- `main.py`: FastAPI app with root endpoints and serialization
- `routers/users.py`: Authentication router
- `routers/product.py`: Product router

**API Design**: RESTful hierarchical structure matching the clustering model.

**See**: [`backend/README.md`](backend/README.md) for detailed documentation.

### 🎨 Frontend (`frontend/`)

**Purpose**: React web application for product browsing and authentication.

**Key Features**:

- **Hierarchical Navigation**: Browse products through three clustering levels
- **User Authentication**: Registration and login with JWT tokens
- **Product Details**: Individual product view with full specifications
- **Responsive Design**: Modern UI built with Tailwind CSS
- **Protected Routes**: Authentication-required pages

**Tech Stack**:

- React 18, Vite, React Router 6
- Axios for API calls
- Tailwind CSS for styling

**Key Components**:

- `Home.jsx`: Level 1 category browsing
- `Level2.jsx`, `Level3.jsx`: Sub-category navigation
- `ProductDetail.jsx`: Product information display
- `Login.jsx`, `Register.jsx`: Authentication

**See**: [`frontend/README.md`](frontend/README.md) for detailed documentation.

### 🔬 Lab (`lab/`)

**Purpose**: Jupyter notebooks for model development and experimentation.

- `model_development.ipynb`: Clustering algorithm development and evaluation
- `preprocessing.ipynb`: Feature engineering experimentation


## Quick Start with Docker Compose

### Prerequisites

- **Docker**: Docker Engine 20.10+
- **Docker Compose**: Compose V2 (included with Docker Desktop)

### Setup Steps

#### 1. Clone the Repository

```bash
git clone <repository-url>
cd Stapler
```

#### 2. Configure Environment Variables

Create environment files for each service:

**For Data Pipeline** (`data/.env_data`):

```env
URL=https://api.example.com
PRODUCT_BASE_URL=https://api.example.com/products/
COMMENTS_BASE_URL=https://api.example.com/comments/
TIMEOUT=400
ENABLE_LOGGING=1
MONGO_URI=mongodb://root:example@mongodb:27017/?authSource=admin
DB_NAME=digikala
CHUNK_SIZE=100
PRODUCTS_COLLECTION=products
COMMENTS_COLLECTION=comments
PREFECT_HOST=0.0.0.0
PREFECT_PORT=4200
```

**For Backend** (create `.env` file or set environment variables):

```env
MONGO_URI=mongodb://root:example@mongodb:27017/?authSource=admin
DB_NAME=digikala
PRODUCTS_COLLECTION=products
USERS_COLLECTION=users
SECRET_KEY=your-secure-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
KEYS_TO_SHOW=_id,title_en,price,cluster_info.level1_id
```

**Optional Environment Variables** (can be set in shell):

```bash
export UID=$(id -u)
export GID=$(id -g)
export MODEL_NAME=Linkage
export MODEL_VERSION=2
export FRONTEND_PORT=8080
```

#### 3. Build and Start All Services

```bash
# Build all images and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Check service status
docker-compose ps
```

#### 4. Verify Services

After starting, verify all services are running:

```bash
# Check MongoDB
docker-compose exec mongodb mongosh --eval "db.runCommand({ ping: 1 })"

# Check Backend API
curl http://localhost:8000/docs

# Check MLflow
curl http://localhost:5000/health

# Check Frontend
curl http://localhost:8080

# Check Data Pipeline (Prefect)
curl http://localhost:4200/health
```

#### 5. Access Services

- **Frontend**: <http://localhost:8080>
- **Prefect UI**: <http://localhost:4200>
- **Backend API**: <http://localhost:8000>
  - **Swagger UI**: <http://localhost:8000/docs>
  - **ReDoc**: <http://localhost:8000/redoc>
- **MLflow UI**: <http://localhost:5000>
- **MongoDB**: `mongodb://localhost:27017`


## Project Structure

```text
Stapler/
├── README.md                 # This file
├── docker-compose.yml        # Docker Compose orchestration
├── pyproject.toml           # Python project configuration
│
├── data/                     # Data Pipeline
│   ├── README.md            # Detailed data pipeline docs
│   ├── pipeline.py          # Prefect flow orchestration
│   ├── brand_ex.py          # Brand extraction
│   ├── product_ex.py        # Product extraction
│   ├── etl.py               # ETL with MongoDB loading
│   ├── Dockerfile           # Data pipeline container
│   └── .env_data            # Environment configuration
│
├── ml/                       # Machine Learning Pipeline
│   ├── README.md            # Detailed ML pipeline docs
│   ├── dataset.py           # MongoDB data extraction
│   ├── preprocessing.py     # Feature engineering
│   ├── model.py             # Model deployment
│   ├── Dockerfile           # ML pipeline container
│   └── start.sh             # MLflow server startup
│
├── backend/                  # Backend API
│   ├── README.md            # Detailed backend API docs
│   ├── main.py              # FastAPI application
│   ├── routers/             # API routers
│   │   ├── product.py      # Product endpoints
│   │   └── users.py        # Auth endpoints
│   ├── Dockerfile           # Backend container
│   └── config.py            # Configuration
│
├── frontend/                 # Frontend Application
│   ├── README.md            # Detailed frontend docs
│   ├── src/                 # React source code
│   ├── Dockerfile           # Multi-stage frontend build
│   └── nginx.conf           # Nginx configuration
│
├── lab/                      # Jupyter Notebooks
│   ├── model_development.ipynb  # Clustering experiments
│   └── preprocessing.ipynb      # Feature engineering
│
├── mlruns/                   # MLflow experiment runs (host-mounted)
├── mlartifacts/              # MLflow model artifacts (host-mounted)
└── LICENSE                   # Project license
```

## System Workflow

### 1. Data Collection Phase

The data pipeline scrapes product information:

1. **Brand Extraction**: Fetches all available brands concurrently
2. **Product Extraction**: Fetches product details for each brand concurrently
3. **Data Storage**: Saves scraped data to JSON files
4. **ETL Process**: Transforms and loads data into MongoDB
   - Chunked processing for memory efficiency
   - Concurrent chunk loading to MongoDB
   - Schema validation

**Automation**: Prefect schedules daily execution at 2:00 AM UTC.

### 2. Machine Learning Phase

The ML pipeline processes products and assigns clusters:

1. **Data Extraction**: Reads products from MongoDB
2. **Feature Engineering**: Transforms raw data into 98-dimensional feature vectors
3. **Clustering**: Applies hierarchical nested clustering
4. **Cluster Assignment**: Updates MongoDB products with cluster_info field

**Automation**: Cron job updates cluster assignments daily at 6:23 AM.

### 3. API Serving Phase

The backend API serves clustered products:

1. **Request Handling**: Receives API requests
2. **Data Retrieval**: Queries MongoDB with clustering filters
3. **Sampling**: Randomly samples products from clusters
4. **Response**: Returns hierarchical product groups

**Endpoints**: Hierarchical structure matching clustering levels.

### 4. Frontend Display Phase

The frontend displays products to users:

1. **Authentication**: User login/registration
2. **Navigation**: Browse through clustering hierarchy
3. **Product View**: Display individual product details
4. **API Integration**: Communicates with backend API

## Key Technical Highlights

### Async Operations Throughout

- **Data Pipeline**: Async HTTP requests, async file I/O, async MongoDB operations
- **ML Pipeline**: Async MongoDB reads and writes
- **Backend API**: Fully async FastAPI with Motor driver
- **Result**: High concurrency and efficient resource utilization

### Hierarchical Architecture

The entire system follows a three-level hierarchy:

- **Data**: Organized by brands → products
- **ML**: Level 1 → Level 2 → Level 3 clusters
- **API**: `/sub/{level1}` → `/sub/{level1}/sub-sub/{level2}`
- **Frontend**: Home → Level2 → Level3 pages

### Production-Ready Features

- **Containerization**: All services containerized
- **Orchestration**: Docker Compose with health checks
- **Monitoring**: MLflow tracking, Prefect monitoring
- **Security**: OAuth2, JWT tokens, password hashing
- **Scalability**: Async operations, chunked processing
- **Persistence**: Docker volumes for data retention


## Service-Specific Issues

See individual README files:

- [`data/README.md`](data/README.md) - Data pipeline troubleshooting
- [`ml/README.md`](ml/README.md) - ML pipeline troubleshooting
- [`backend/README.md`](backend/README.md) - API troubleshooting
- [`frontend/README.md`](frontend/README.md) - Frontend troubleshooting


## Security Considerations

### Production Checklist

- [ ] Change MongoDB root password
- [ ] Generate strong `SECRET_KEY` for JWT
- [ ] Use environment variables (not `.env` files in production)
- [ ] Enable MongoDB authentication
- [ ] Set up HTTPS/TLS for frontend and backend
- [ ] Configure firewall rules
- [ ] Review and restrict `KEYS_TO_SHOW` for sensitive data
- [ ] Implement rate limiting on API endpoints
- [ ] Regular security updates for base images

### Current Defaults (Development Only)

- MongoDB: `root/example` (change in production!)
- JWT Secret: `change-me-to-a-secure-secret-key-in-production`
- All services exposed on default ports

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with Docker Compose
5. Submit a pull request

## License

See [LICENSE](LICENSE) file for details.

## Support

For issues or questions:

1. Check service-specific README files
2. Review Docker Compose logs
3. Check individual service health endpoints
4. Consult troubleshooting sections in component READMEs
