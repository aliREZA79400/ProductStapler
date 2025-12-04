# KASEB - Product Clustering & Categorization System

A comprehensive end-to-end system for web scraping, machine learning-based product clustering, and hierarchical product browsing. The project implements a complete data pipeline from extraction to deployment, featuring async web scraping, hierarchical clustering models, REST API, and a modern React frontend.

## Project Overview

KASEB is a full-stack application that:

1. **Scrapes** product data from web APIs using high-performance async operations
2. **Clusters** products using hierarchical nested clustering algorithms
3. **Serves** clustered products through a REST API with hierarchical navigation
4. **Displays** products in a modern web interface with authentication

The system is designed with a microservices architecture, fully containerized with Docker Compose, and implements production-ready patterns for scalability and maintainability.

## System Architecture

```text
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│    Backend   │◀────│   MongoDB   │◀────│Data Pipeline│
│   (React)   │     │   (FastAPI)  │     │             │     │  (Prefect)  │
└─────────────┘     └──────────────┘     └─────────────┘     └─────────────┘
                                                ▲
                                                │
                                        ┌───────┴──────┐
                                        │  ML Pipeline │
                                        │   (MLflow)   │
                                        └──────────────┘
```

### Data Flow

1. **Data Pipeline** → Scrapes products → Stores in MongoDB
2. **ML Pipeline** → Reads from MongoDB → Clusters products → Updates MongoDB with cluster assignments
3. **Backend API** → Reads clustered products → Serves hierarchical endpoints
4. **Frontend** → Consumes API → Displays products in hierarchical categories

## Project Components

### 📊 Data Pipeline (`data/`)

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

## Docker Compose Setup

The project uses Docker Compose to orchestrate all services with proper dependency management, health checks, and volume persistence.

### Services Overview

The `docker-compose.yml` defines five main services:

1. **MongoDB** (Database)
2. **MLflow** (ML Tracking & Model Registry)
3. **Backend** (FastAPI REST API)
4. **Frontend** (React + Nginx)
5. **Data Pipeline** (Prefect + Scraping Pipeline)

### Service Details

#### 1. MongoDB Service

```yaml
mongodb:
  image: mongo:7
  ports: 27017:27017
  volumes: mongodb_data:/data/db
  healthcheck: MongoDB ping test
```

**Purpose**: Primary database for products, users, and cluster assignments.

**Features**:

- Persistent data storage via Docker volume
- Health checks for service dependency management
- Authentication enabled (root/example - change in production!)

#### 2. MLflow Service

```yaml
mlflow:
  build: ml/Dockerfile
  ports: 5000:5000
  volumes: mlruns, mlartifacts
  depends_on: mongodb (healthy)
```

**Purpose**: MLflow tracking server for experiment tracking and model registry.

**Features**:

- Runs MLflow server on port 5000
- Persistent storage for runs and artifacts
- Automatic cron job for model updates (6:23 AM daily)
- Waits for MongoDB to be healthy before starting

#### 3. Backend Service

```yaml
backend:
  build: backend/Dockerfile
  ports: 8000:8000
  depends_on: mongodb (healthy)
```

**Purpose**: FastAPI REST API server.

**Features**:

- Async FastAPI application
- Auto-reload enabled for development
- Waits for MongoDB to be healthy

#### 4. Frontend Service

```yaml
frontend:
  build: frontend/Dockerfile (multi-stage)
  ports: 8080:80
  depends_on: backend (started)
```

**Purpose**: React application served via Nginx.

**Features**:

- Multi-stage build (deps → build → nginx)
- Production-optimized Nginx configuration
- Waits for backend to start

#### 5. Data Pipeline Service

```yaml
data-pipeline:
  build: data/Dockerfile
  env_file: ./data/.env_data
  volumes: original_data, logs
  depends_on: mongodb (healthy)
```

**Purpose**: Prefect server and automated data pipeline.

**Features**:

- Prefect server on port 4200
- Automated daily pipeline execution
- Persistent volumes for scraped data and logs
- Environment configuration from `.env_data`

### Volume Management

Docker volumes ensure data persistence across container restarts:

- `mongodb_data`: Database files
- `data_original_data`: Scraped JSON files
- `data_logs`: Pipeline execution logs
- `mlruns`: MLflow experiment runs (host-mounted)
- `mlartifacts`: MLflow model artifacts (host-mounted)

### Health Checks & Dependencies

The Compose file implements proper dependency management:

- **Health Checks**: MongoDB has ping-based health check
- **Service Dependencies**:
  - Backend, MLflow, Data Pipeline wait for MongoDB to be healthy
  - Frontend waits for Backend to start
- **Start Order**: Ensures services start in correct sequence

### Build Optimization

Uses YAML anchors to avoid redundant builds:

```yaml
x-ml-build: &ml-build      # Define once
x-backend-build: &backend-build
```

Services reference these anchors, enabling efficient image reuse.

## Quick Start with Docker Compose

### Prerequisites

- **Docker**: Docker Engine 20.10+
- **Docker Compose**: Compose V2 (included with Docker Desktop)

### Setup Steps

#### 1. Clone the Repository

```bash
git clone <repository-url>
cd KASEB
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
- **Backend API**: <http://localhost:8000>
  - **Swagger UI**: <http://localhost:8000/docs>
  - **ReDoc**: <http://localhost:8000/redoc>
- **MLflow UI**: <http://localhost:5000>
- **MongoDB**: `mongodb://localhost:27017`

### Docker Compose Commands

```bash
# Start all services in background
docker-compose up -d

# Start and view logs
docker-compose up

# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ deletes data)
docker-compose down -v

# Rebuild specific service
docker-compose build backend

# Restart specific service
docker-compose restart backend

# View logs for specific service
docker-compose logs -f backend

# Execute command in service container
docker-compose exec backend bash

# Check service health
docker-compose ps
```

### Development Workflow

For development, you may want to run services individually:

```bash
# Start only MongoDB and MLflow
docker-compose up -d mongodb mlflow

# Run backend locally with auto-reload
cd backend && uvicorn main:app --reload

# Run frontend locally
cd frontend && npm run dev

# Run data pipeline locally
cd data && python -m pipeline --stage Products
```

## Project Structure

```text
KASEB/
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

## Configuration Summary

### Environment Variables by Service

#### MongoDB

- `MONGO_INITDB_ROOT_USERNAME`: Database root username
- `MONGO_INITDB_ROOT_PASSWORD`: Database root password

#### Backend

- `MONGO_URI`: MongoDB connection string
- `DB_NAME`: Database name
- `SECRET_KEY`: JWT signing key (change in production!)
- `KEYS_TO_SHOW`: Comma-separated fields to expose

#### MLflow

- `MLFLOW_TRACKING_URI`: MLflow server URL
- `MODEL_NAME`: Model name in registry
- `MODEL_VERSION`: Model version to use

#### Data Pipeline

- `URL`, `PRODUCT_BASE_URL`, `COMMENTS_BASE_URL`: API endpoints
- `PREFECT_HOST`, `PREFECT_PORT`: Prefect server configuration

See individual README files for complete configuration details.

## Development Setup (Without Docker)

If you prefer running services locally:

### Local Development Prerequisites

- Python 3.13+
- Node.js 20+
- MongoDB 7+
- Git

### Local Setup

```bash
# 1. Install Python dependencies (using uv or pip)
pip install -r backend/requirements.txt
pip install -r data/requirements.txt
pip install -r ml/requirements.txt

# 2. Install Node.js dependencies
cd frontend && npm install

# 3. Start MongoDB locally
mongod

# 4. Start services in separate terminals

# Terminal 1: Backend
cd backend && uvicorn main:app --reload

# Terminal 2: MLflow
cd ml && ./start.sh

# Terminal 3: Data Pipeline
cd data && ./start.sh

# Terminal 4: Frontend
cd frontend && npm run dev
```

**Note**: Docker Compose is the recommended approach for consistent development and deployment.

## Usage Examples

### Accessing the Application

1. **Frontend**: Navigate to <http://localhost:8080>
   - Register a new user
   - Login to access protected routes
   - Browse products through hierarchical categories

2. **API Documentation**: Visit <http://localhost:8000/docs>
   - Interactive Swagger UI
   - Test endpoints directly
   - View request/response schemas

3. **MLflow UI**: Visit <http://localhost:5000>
   - View experiment runs
   - Compare model metrics
   - Access model registry

### API Usage

```bash
# Get Level 1 product samples
curl "http://localhost:8000/?sample_size=5"

# Get Level 2 samples for Level 1 cluster 0
curl "http://localhost:8000/sub/0?sample_size=3"

# Get product by ID
curl "http://localhost:8000/product/8860414"

# Register user
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "user1", "password": "password123"}'

# Login
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user1&password=password123"
```

## Troubleshooting

### Common Docker Issues

**Services won't start**:

```bash
# Check logs
docker-compose logs

# Check if ports are already in use
netstat -tulpn | grep -E '27017|8000|5000|8080'

# Rebuild images
docker-compose build --no-cache
```

**MongoDB connection errors**:

- Verify MongoDB is healthy: `docker-compose ps mongodb`
- Check connection string format in environment variables
- Ensure authentication credentials match

**Volume permission issues**:

```bash
# Set UID/GID environment variables
export UID=$(id -u)
export GID=$(id -g)
docker-compose up -d
```

**Frontend can't connect to backend**:

- Verify backend is running: `curl http://localhost:8000/docs`
- Check nginx.conf proxy configuration
- Verify frontend container logs

### Service-Specific Issues

See individual README files:

- [`data/README.md`](data/README.md) - Data pipeline troubleshooting
- [`ml/README.md`](ml/README.md) - ML pipeline troubleshooting
- [`backend/README.md`](backend/README.md) - API troubleshooting
- [`frontend/README.md`](frontend/README.md) - Frontend troubleshooting

## Performance Optimization

### Recommended MongoDB Indexes

Create indexes for optimal query performance:

```javascript
db.products.createIndex({ "cluster_info.level1_id": 1 })
db.products.createIndex({ "cluster_info.level2_id": 1 })
db.products.createIndex({ "cluster_info.level3_id": 1 })
db.products.createIndex({ "_id": 1 })
```

### Resource Limits

Consider setting resource limits in `docker-compose.yml` for production:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

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

## Additional Resources

- [`data/README.md`](data/README.md) - Async scraping & ETL details
- [`ml/README.md`](ml/README.md) - Clustering models & feature engineering
- [`backend/README.md`](backend/README.md) - API design & endpoints
- [`frontend/README.md`](frontend/README.md) - Frontend architecture

## Support

For issues or questions:

1. Check service-specific README files
2. Review Docker Compose logs
3. Check individual service health endpoints
4. Consult troubleshooting sections in component READMEs
