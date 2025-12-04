# Backend API - FastAPI Product Service

This directory contains a FastAPI-based REST API service designed to provide hierarchical product clustering and retrieval capabilities. The API leverages MongoDB for data storage and implements a modular router-based architecture with comprehensive authentication and authorization.

## Overview

The backend API is built using FastAPI and provides endpoints for:

1. **Hierarchical Product Sampling**: Navigate products through a three-level clustering hierarchy (Level 1 → Level 2 → Level 3)
2. **Product Retrieval**: Get individual product details by ID
3. **User Authentication**: OAuth2-based authentication with JWT tokens
4. **Configurable Field Filtering**: Selective field exposure via environment configuration

The API design emphasizes:

- **Modular Architecture**: Router-based separation of concerns
- **Async Operations**: Fully asynchronous MongoDB operations using Motor
- **RESTful Design**: Clear, hierarchical URL structure matching the clustering model
- **Type Safety**: Pydantic models for request/response validation
- **Security**: OAuth2 password flow with JWT token authentication

## API Design Architecture

### Framework & Technology Stack

- **FastAPI**: Modern, fast web framework with automatic OpenAPI documentation
- **Motor**: Async MongoDB driver for non-blocking database operations
- **PyJWT**: JWT token generation and validation
- **Pwdlib**: Secure password hashing with Argon2
- **Pydantic**: Data validation and serialization

### Router-Based Architecture

The API follows a modular router pattern, separating functionality into distinct modules:

```text
backend/
├── main.py              # Application entry point, root endpoints
├── routers/
│   ├── product.py      # Product-specific endpoints
│   └── users.py        # Authentication endpoints
└── internal/           # Internal utilities
```

**Design Principles**:

1. **Separation of Concerns**: Each router handles a specific domain (products, authentication)
2. **Prefix-Based Routing**: Routers use prefixes (`/auth`, `/product`) for clear URL structure
3. **Tag-Based Organization**: OpenAPI tags for endpoint grouping in documentation
4. **Centralized Configuration**: Shared MongoDB clients and configuration via `config.py`

### Hierarchical Endpoint Structure

The API design mirrors the three-level clustering hierarchy, enabling natural navigation through product categories:

```text
GET  /                           # Level 1 sampling (all top-level clusters)
GET  /sub/{level1_id}           # Level 2 sampling (sub-clusters of Level 1)
GET  /sub/{level1_id}/sub-sub/{level2_id}  # Level 3 sampling (final clusters)
```

**Design Rationale**:

- **Path-Based Hierarchy**: URL structure reflects the clustering hierarchy (`/sub/` → `/sub-sub/`)
- **Progressive Filtering**: Each level narrows down the product selection
- **Consistent Response Format**: All levels return similar structured responses
- **Sample-Based Exploration**: Random sampling prevents overwhelming responses

### Core Components

#### 1. Application Entry Point (`main.py`)

**FastAPI Application Setup**:

```python
app = FastAPI()
app.include_router(users_router)    # /auth/* endpoints
app.include_router(product_router)  # /product/* endpoints
```

**Root-Level Endpoints**:

The main application provides three hierarchical sampling endpoints that leverage the clustering structure:

- **`GET /`**: Sample products grouped by Level 1 clusters
- **`GET /sub/{level1_id}`**: Sample products grouped by Level 2 clusters within a Level 1 cluster
- **`GET /sub/{level1_id}/sub-sub/{level2_id}`**: Sample products grouped by Level 3 clusters

**Key Design Features**:

1. **Aggregation Pipeline**: Uses MongoDB aggregation with `$sample` for efficient random sampling
2. **Configurable Sample Size**: Query parameter controls number of products per group
3. **Nested Value Extraction**: Supports dot-notation for nested fields (`cluster_info.level1_id`)
4. **Flexible Field Filtering**: Configurable via `KEYS_TO_SHOW` environment variable

#### 2. Document Serialization System

The API implements a sophisticated document serialization system:

**Features**:

- **ObjectId Conversion**: Automatically converts MongoDB ObjectIds to strings
- **Recursive Serialization**: Handles nested dictionaries and lists
- **Field Filtering**: Only includes fields specified in `KEYS_TO_SHOW` configuration
- **Nested Key Support**: Supports dot-notation for nested field access (e.g., `cluster_info.level1_id`)

**Implementation**:

```python
def serialize_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert ObjectId to string for JSON serialization and filter by KEYS_TO_SHOW.
    Only includes keys specified in KEYS_TO_SHOW environment variable.
    """
```

**Configuration**:

The `KEYS_TO_SHOW` environment variable accepts comma-separated field paths:

- Top-level: `_id,title_en,price`
- Nested: `cluster_info.level1_id,specifications.cpu_model`

If empty, all fields are returned (backward compatibility).

#### 3. Product Router (`routers/product.py`)

**Endpoint**: `GET /product/{product_id}`

**Design Features**:

- **Flexible ID Handling**: Accepts both ObjectId strings and numeric IDs
- **Error Handling**: Comprehensive error handling with appropriate HTTP status codes
- **Async Operations**: Non-blocking MongoDB queries
- **Full Document Serialization**: Returns complete product document

**Response Format**:

Returns the complete product document with all fields (unless filtered by `KEYS_TO_SHOW`).

#### 4. Authentication Router (`routers/users.py`)

**OAuth2 Password Flow Implementation**:

The authentication system follows OAuth2 standard with JWT tokens:

**Endpoints**:

1. **`POST /auth/register`**: User registration
   - Validates username (3-50 chars) and password (6-128 chars)
   - Hashes passwords using Argon2 (via pwdlib)
   - Prevents duplicate usernames

2. **`POST /auth/login`**: User authentication
   - OAuth2PasswordRequestForm for standard OAuth2 flow
   - Returns JWT access token
   - Validates credentials against hashed passwords

3. **`GET /auth/me`**: Get current user
   - Protected endpoint requiring authentication
   - Returns current user information

**Security Design**:

- **Password Hashing**: Argon2 algorithm (recommended by pwdlib)
- **JWT Tokens**: Signed with configurable secret key and algorithm
- **Token Expiration**: Configurable expiration time (default: 30 minutes)
- **Bearer Token Authentication**: Standard OAuth2 Bearer token flow
- **Dependency Injection**: FastAPI's `Depends()` for automatic token validation

**Pydantic Models**:

- `UserCreate`: Registration input validation
- `UserRead`: Safe user data output (no password)
- `Token`: Standardized token response format

#### 5. MongoDB Integration

**Async Client Architecture**:

Each router module creates its own MongoDB client:

```python
mongo_client = AsyncIOMotorClient(MONGO_URI)
collection = mongo_client[DB_NAME][COLLECTION_NAME]
```

**Design Decisions**:

- **Separate Clients**: Each router maintains its own connection for isolation
- **Async Operations**: All database operations use `async/await`
- **Connection Pooling**: Motor handles connection pooling automatically
- **Error Handling**: Comprehensive exception handling with HTTP status codes

## API Endpoints

### Root Endpoints (Hierarchical Clustering)

#### 1. Sample Products by Level 1

```http
GET /?sample_size=3&level1_id=0
```

**Purpose**: Get random samples from each Level 1 cluster (or specific Level 1 cluster).

**Query Parameters**:

- `sample_size` (int, default: 3): Number of products to sample per group
- `level1_id` (int, optional): Filter by specific Level 1 cluster

**Response Structure**:

```json
{
  "message": "Sampled 3 products from each level1_id group",
  "total_groups": 3,
  "results": {
    "0": {
      "level1_id": 0,
      "sample_size": 3,
      "products": [...]
    },
    "1": {...}
  }
}
```

**Design**: Uses MongoDB aggregation pipeline with `$sample` for efficient random sampling.

#### 2. Sample Products by Level 2

```http
GET /sub/{level1_id}?sample_size=3
```

**Purpose**: Get random samples from each Level 2 cluster within a Level 1 cluster.

**Path Parameters**:

- `level1_id` (int): Level 1 cluster identifier

**Query Parameters**:

- `sample_size` (int, default: 3): Number of products to sample per group

**Response Structure**:

```json
{
  "message": "Sampled 3 products from each level2_id group...",
  "level1_id": 0,
  "total_groups": 4,
  "results": {
    "0": {
      "level1_id": 0,
      "level2_id": 0,
      "sample_size": 3,
      "products": [...]
    }
  }
}
```

#### 3. Sample Products by Level 3

```http
GET /sub/{level1_id}/sub-sub/{level2_id}?sample_size=3
```

**Purpose**: Get random samples from each Level 3 cluster (final clusters).

**Path Parameters**:

- `level1_id` (int): Level 1 cluster identifier
- `level2_id` (int): Level 2 cluster identifier

**Query Parameters**:

- `sample_size` (int, default: 3): Number of products to sample per group

**Response Structure**:

```json
{
  "message": "Sampled 3 products from each level3_id group...",
  "level1_id": 0,
  "level2_id": 2,
  "total_groups": 5,
  "results": {
    "0": {
      "level1_id": 0,
      "level2_id": 2,
      "level3_id": 0,
      "sample_size": 3,
      "products": [...]
    }
  }
}
```

### Product Endpoints

#### Get Product by ID

```http
GET /product/{product_id}
```

**Purpose**: Retrieve a single product by its ID.

**Path Parameters**:

- `product_id` (str): Product identifier (supports numeric or ObjectId format)

**Response**: Complete product document with all fields.

**Error Handling**:

- `404 Not Found`: Product doesn't exist
- `500 Internal Server Error`: Database or processing error

### Authentication Endpoints

#### Register User

```http
POST /auth/register
```

**Request Body**:

```json
{
  "username": "user123",
  "password": "securepassword"
}
```

**Response** (`201 Created`):

```json
{
  "username": "user123"
}
```

**Validation**:

- Username: 3-50 characters
- Password: 6-128 characters
- Prevents duplicate usernames (`409 Conflict`)

#### Login

```http
POST /auth/login
```

**Request**: OAuth2 form data (`application/x-www-form-urlencoded`):

- `username`: User identifier
- `password`: User password

**Response**:

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

**Error Handling**:

- `401 Unauthorized`: Invalid credentials

#### Get Current User

```http
GET /auth/me
```

**Headers**: `Authorization: Bearer {token}`

**Response**:

```json
{
  "username": "user123"
}
```

**Protection**: Requires valid JWT token in Authorization header.

## Configuration

All configuration is managed through environment variables (loaded via `python-decouple`):

### MongoDB Configuration

- `MONGO_URI`: MongoDB connection string
- `DB_NAME`: Database name
- `PRODUCTS_COLLECTION`: Products collection name
- `USERS_COLLECTION`: Users collection name

### Authentication Configuration

- `SECRET_KEY`: JWT signing secret key (keep secure!)
- `ALGORITHM`: JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time (default: 30)

### API Configuration

- `KEYS_TO_SHOW`: Comma-separated list of fields to include in responses (empty = all fields)
  - Example: `_id,title_en,price,cluster_info.level1_id`

## Error Handling

The API implements comprehensive error handling:

### HTTP Status Codes

- `200 OK`: Successful request
- `201 Created`: Resource created (user registration)
- `401 Unauthorized`: Authentication required or failed
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource conflict (duplicate username)
- `500 Internal Server Error`: Server error

### Error Response Format

```json
{
  "detail": "Error message description"
}
```

For authentication errors:

```json
{
  "detail": {
    "message": "Error message"
  }
}
```

## Project Structure

```text
backend/
├── README.md              # This file
├── main.py                # FastAPI app, root endpoints, serialization
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── Dockerfile             # Container configuration
├── routers/               # Router modules
│   ├── product.py        # Product endpoints
│   └── users.py          # Authentication endpoints
└── internal/             # Internal utilities
    └── admin.py          # Admin utilities (TODO)
```

## Design Patterns & Best Practices

### 1. Async/Await Pattern

All database operations use async/await for non-blocking I/O:

```python
async def get_product(product_id: str):
    product = await products_collection.find_one(query)
    return serialize_document(product)
```

### 2. Dependency Injection

FastAPI's dependency injection system is used for:

- **Authentication**: `get_current_user` dependency validates tokens
- **OAuth2 Flow**: `OAuth2PasswordRequestForm` dependency handles login form
- **Database Access**: Router-level MongoDB client instances

### 3. Request/Response Models

Pydantic models ensure type safety and automatic validation:

- Request validation on input
- Response model enforcement
- Automatic OpenAPI schema generation

### 4. Router Prefixes & Tags

Clear organization through prefixes and tags:

```python
router = APIRouter(prefix="/auth", tags=["auth"])
```

Enables:

- Organized URL structure (`/auth/login`, `/auth/register`)
- Grouped OpenAPI documentation
- Easier API navigation

### 5. Aggregation Pipelines

Efficient data retrieval using MongoDB aggregation:

```python
pipeline = [
    {"$match": {"cluster_info.level1_id": level1_id}},
    {"$sample": {"size": sample_size}}
]
```

Benefits:

- Server-side filtering and sampling
- Reduced data transfer
- Better performance for large datasets

## API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: Available at `/docs` endpoint
- **ReDoc**: Available at `/redoc` endpoint
- **OpenAPI Schema**: Available at `/openapi.json` endpoint

The documentation includes:

- All endpoints with descriptions
- Request/response schemas
- Authentication requirements
- Example requests and responses

## Usage Examples

### Hierarchical Product Navigation

```bash
# Get samples from all Level 1 clusters
curl "http://localhost:8000/?sample_size=5"

# Get samples from Level 2 clusters in Level 1 cluster 0
curl "http://localhost:8000/sub/0?sample_size=3"

# Get samples from Level 3 clusters
curl "http://localhost:8000/sub/0/sub-sub/2?sample_size=2"
```

### Product Retrieval

```bash
# Get product by ID
curl "http://localhost:8000/product/8860414"
```

### Authentication Flow

```bash
# Register a new user
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "newuser", "password": "securepass123"}'

# Login and get token
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=newuser&password=securepass123"

# Access protected endpoint
curl "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer {your_token_here}"
```

## Performance Considerations

### MongoDB Indexing

For optimal performance, ensure indexes on:

- `cluster_info.level1_id`
- `cluster_info.level2_id`
- `cluster_info.level3_id`
- `_id` (automatic)

### Async Operations

All database operations are asynchronous, enabling:

- High concurrency
- Non-blocking I/O
- Efficient resource utilization

### Sample Size Limits

Consider implementing maximum sample size limits to prevent:

- Excessive data transfer
- Performance degradation
- Resource exhaustion

## Security Considerations

### Password Security

- **Hashing**: Argon2 algorithm (memory-hard, resistant to GPU attacks)
- **No Plain Text Storage**: Passwords are never stored in plain text
- **Validation**: Minimum length requirements enforced

### JWT Security

- **Secret Key**: Use strong, randomly generated secret keys
- **Algorithm**: Configurable algorithm (default: HS256)
- **Expiration**: Tokens expire after configured time
- **Bearer Token**: Standard OAuth2 Bearer token flow

### Input Validation

- **Pydantic Models**: Automatic validation of request data
- **Path Parameters**: Type validation (int, str)
- **Query Parameters**: Range validation (e.g., `ge=1` for sample_size)

## Deployment

### Docker Deployment

The included `Dockerfile` enables containerized deployment:

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY backend/ ./backend/
RUN pip install -r /app/backend/requirements.txt
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### Environment Variables

Create a `.env` file or set environment variables:

```env
MONGO_URI=mongodb://localhost:27017
DB_NAME=digikala
PRODUCTS_COLLECTION=products
USERS_COLLECTION=users
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
KEYS_TO_SHOW=_id,title_en,price,cluster_info.level1_id
```

### Running the Server

```bash
# Development mode with auto-reload
uvicorn backend.main:app --reload

# Production mode
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

## Dependencies

Key dependencies (see `requirements.txt` for full list):

- `fastapi`: Web framework
- `uvicorn`: ASGI server
- `motor`: Async MongoDB driver
- `pymongo`: MongoDB operations
- `pwdlib`: Password hashing
- `PyJWT`: JWT token handling
- `python-decouple`: Configuration management
- `pydantic`: Data validation

## Future Enhancements

Potential improvements:

- **Pagination**: Implement cursor-based or offset pagination for large result sets
- **Caching**: Redis caching for frequently accessed products
- **Rate Limiting**: Prevent API abuse with rate limiting
- **Filtering & Sorting**: Additional query parameters for filtering and sorting
- **Bulk Operations**: Batch product retrieval endpoints
- **GraphQL Support**: Alternative query interface
- **WebSocket Support**: Real-time product updates
- **Admin Panel**: Internal admin utilities (currently TODO)
- **API Versioning**: Versioned endpoints for backward compatibility
