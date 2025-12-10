# Data Pipeline - Async Web Scraping & ETL System

This directory contains a high-performance asynchronous data pipeline for scraping product data and comments from web APIs, with automated ETL processes that load data into MongoDB. The system is built with Python's `asyncio` for concurrent operations and uses Prefect for workflow orchestration and scheduling.

## Overview

The pipeline follows an Extract, Transform, Load (ETL) architecture with three main stages:

1. **Extract**: Async web scraping to fetch brand and product data
2. **Transform**: Data normalization and schema validation
3. **Load**: Async batch loading into MongoDB (Parallel)

The entire pipeline is designed around asynchronous operations to maximize throughput and efficiency.

## Key Features

### 🚀 Async Web Scraping Capabilities

The scraping layer leverages Python's `asyncio` library to perform concurrent HTTP requests, significantly reducing the time needed to fetch large datasets.

#### Brand Extraction (`brand_ex.py`)

- **Concurrent Brand Processing**: Uses `asyncio.Semaphore(5)` to limit concurrent brand requests while processing multiple brands simultaneously
- **Pagination Handling**: Concurrently fetches all product pages for each brand using `asyncio.wait()` and `asyncio.create_task()`
- **Async HTTP Client**: Uses `httpx.AsyncClient` for non-blocking HTTP requests
- **Key Methods**:
  - `get_all_brands()`: Fetches all available brands asynchronously
  - `get_product_ids_of_each_brand()`: Concurrently processes all pages for a brand using semaphores
  - `get_all_ids_by_brand()`: Orchestrates concurrent brand processing with task management

#### Product Extraction (`product_ex.py`)

- **Concurrent Product Fetching**: Uses semaphores (`asyncio.Semaphore(5)`) to control concurrency when fetching individual products
- **Brand-Level Parallelism**: Processes multiple brands concurrently using `asyncio.create_task()`
- **Product-Level Parallelism**: For each brand, fetches all products concurrently
- **Comments Pagination**: Handles paginated comments by first fetching page 1 to determine total pages, then concurrently fetching all remaining pages
- **Dual Mode Operation**: Supports both product data extraction and comments extraction based on `state` parameter
- **Key Methods**:
  - `fetch_product()`: Async fetch with semaphore-controlled concurrency
  - `fetch_brand_products()`: Concurrently fetches all products for a brand
  - `fetch_product_comments()`: Handles paginated comments with concurrent page fetching
  - `run()`: Orchestrates concurrent processing across all brands

**Performance Benefits**:

- Semaphores prevent overwhelming target servers while maintaining high throughput
- Concurrent task execution reduces total scraping time from hours to minutes
- Timeout management ensures failed requests don't block the entire pipeline

### 🗄️ Async MongoDB Loading

The ETL layer uses Motor (async MongoDB driver) combined with process pools to optimize both I/O-bound and CPU-bound operations.

#### Architecture (`etl.py`)

- **Async File I/O**: Uses `aiofiles` for non-blocking file reading in chunks
- **Async MongoDB Operations**: Uses `motor.motor_asyncio.AsyncIOMotorClient` for non-blocking database operations
- **Hybrid Processing Model**: Combines async I/O with process pools for CPU-intensive transformations
- **Chunked Processing**: Processes data in configurable chunks (`CHUNK_SIZE`) to manage memory efficiently

#### Key Components

1. **Chunked Data Extraction**:
   - `extract_product_in_chunks()`: Async generator that yields data chunks from JSON files
   - `extract_comments_in_chunks()`: Similar async generator for comment data
   - Uses `aiofiles.open()` for non-blocking file I/O

2. **Concurrent Chunk Processing**:
   - `_process_chunk_async()`: Worker function that:
     - Transforms chunks in a separate process (CPU-bound) using `ProcessPoolExecutor`
     - Loads transformed data asynchronously (I/O-bound) using `AsyncIOMotorCollection.bulk_write()`
   - `run_chunked_pipeline_concurrently()`: Orchestrates concurrent processing of all chunks
     - Creates async tasks for each chunk as it's generated
     - Uses `asyncio.gather()` to wait for all tasks

3. **Async Database Operations**:
   - `load_products()`: Uses `bulk_write()` with `UpdateOne` operations for upsert logic
   - `load_comments()`: Uses `delete_many()` followed by `insert_many()` for comment replacement
   - Both operations are fully async and non-blocking

**Performance Benefits**:

- Async MongoDB operations allow multiple chunks to be loaded concurrently
- Process pools enable parallel CPU-intensive transformations
- Chunked processing prevents memory overflow with large datasets
- Producer-consumer pattern ensures I/O and CPU work happen simultaneously

### 🤖 Prefect Automation

The pipeline uses Prefect 3.x for workflow orchestration, scheduling, and monitoring.

#### Pipeline Flow (`pipeline.py`)

The Prefect flow orchestrates the entire ETL process:

```python
@flow(log_prints=True)
async def products_pipeline_flow():
    # 1. Extract brands
    brands_info = await extract_brands_task()
    
    # 2. Extract products
    products = await extract_products_task(brands_info)
    
    # 3. Transform and Load
    await run_etl_task(...)
```

#### Prefect Tasks

- `@task extract_brands_task()`: Async task for brand extraction
- `@task extract_products_task()`: Async task for product extraction  
- `@task save_json_task()`: Task for saving intermediate JSON files
- `@task run_etl_task()`: Task for ETL operations

#### Scheduling & Automation

The pipeline can be run in three modes:

1. **Manual Execution**: Run specific stages directly

   ```bash
   python -m data.pipeline --stage Products
   python -m data.pipeline --stage Comments
   ```

2. **Prefect Serve Mode**: Automated scheduling with Prefect server

   ```bash
   python -m data.pipeline --stage serve
   ```

   This mode:
   - Starts a Prefect server (via `start.sh` script)
   - Schedules the `products_pipeline_flow` to run daily at 2:00 AM UTC (`cron="0 2 * * *"`)
   - Provides web UI for monitoring runs, logs, and flow execution history
   - Automatically retries failed tasks with configurable retry logic
   - Tags flows for organization (`tags=["etl", "daily"]`)

#### Prefect Server Setup (`start.sh`)

The startup script:

- Initializes Prefect server on configurable host/port (default: `0.0.0.0:4200`)
- Waits for API health check before starting pipeline
- Handles graceful shutdown with cleanup

**Benefits of Prefect**:

- **Observability**: Track flow runs, task durations, and failures in web UI
- **Scheduling**: Cron-based automation without external schedulers
- **Error Handling**: Built-in retry mechanisms and error tracking
- **Dependencies**: Clear task dependency management
- **State Management**: Automatic state tracking and recovery

## Project Structure

```text
data/
├── README.md                 # This file
├── pipeline.py              # Prefect flow orchestration
├── brand_ex.py              # Async brand extraction
├── product_ex.py            # Async product/comment extraction
├── etl.py                   # Async ETL with MongoDB loading
├── config.py                # Configuration management
├── start.sh                 # Prefect server startup script
├── Dockerfile               # Container configuration
├── requirements.txt         # Python dependencies
├── .env_data               # Environment variables
├── util/                    # Utility modules
│   ├── logger.py           # Logging setup
│   └── async_timer.py      # Async timing decorators
├── original_data/          # Scraped JSON files
├── logs/                   # Application logs
└── tests/                  # Test suite
```

## Configuration

All configuration is managed through environment variables (loaded via `python-decouple`):

- **Scraping Configuration**:
  - `URL`: Base URL for brand search API
  - `PRODUCT_BASE_URL`: Base URL for product details API
  - `COMMENTS_BASE_URL`: Base URL for comments API
  - `TIMEOUT`: Request timeout in seconds
  - `ENABLE_LOGGING`: Enable/disable file logging

- **Database Configuration**:
  - `MONGO_URI`: MongoDB connection string
  - `DB_NAME`: Database name
  - `PRODUCTS_COLLECTION`: Products collection name
  - `COMMENTS_COLLECTION`: Comments collection name
  - `CHUNK_SIZE`: Number of items per processing chunk

- **Prefect Configuration**:
  - `PREFECT_HOST`: Prefect server host (default: `0.0.0.0`)
  - `PREFECT_PORT`: Prefect server port (default: `4200`)

See `.env_data` for example configuration values.

## Usage

### Manual Execution

```bash
# Extract and load products
python -m data.pipeline --stage Products

# Extract and load comments
python -m data.pipeline --stage Comments
```

### Automated Execution with Prefect

```bash
# Start Prefect server and schedule pipeline
./start.sh

# Or run serve mode directly
python -m data.pipeline --stage serve
```

Access Prefect UI at `http://localhost:4200` to monitor flow runs.

### Docker Deployment

The project includes a `Dockerfile` for containerized deployment. See the Dockerfile for build instructions.

## Async Performance Characteristics

### Scraping Layer

- **Concurrency Level**: Up to 5 concurrent requests per semaphore (configurable)
- **Brand Processing**: All brands processed concurrently with semaphore limits
- **Product Processing**: All products per brand processed concurrently
- **Comments**: All pages per product fetched concurrently after initial page discovery

### ETL Layer

- **File Reading**: Async chunked file I/O prevents blocking
- **Transformation**: CPU-bound work distributed across process pool (one per CPU core)
- **Database Loading**: Multiple chunks loaded concurrently using async MongoDB operations
- **Memory Efficiency**: Chunked processing handles datasets of any size

## Database Schema

The pipeline enforces JSON Schema validation on MongoDB collections:

- **Products Collection**: Validates required fields (`_id`, `title_en`, `brand`, `category`, `specifications`) and data types
- **Comments Collection**: Validates required fields (`product_id`, `body`) and comment structure

See `etl.py::setup_database_schemas()` for full schema definitions.

## Logging

The pipeline uses structured logging with:

- Timestamped log files in `logs/` directory
- Module-specific loggers for different components
- Configurable logging levels and file output
- Automatic log file rotation based on execution timestamp

## Error Handling

- **Scraping Errors**: Individual request failures don't stop the pipeline; errors are logged and processing continues
- **ETL Errors**: Chunk-level error handling ensures partial failures don't affect entire dataset
- **Database Errors**: Bulk operations handle duplicate keys and validation errors gracefully
- **Prefect Retries**: Automatic task retry on failure with exponential backoff

## Dependencies

Key dependencies (see `requirements.txt` for full list):

- `asyncio`: Async runtime
- `httpx`: Async HTTP client
- `motor`: Async MongoDB driver
- `prefect`: Workflow orchestration
- `aiofiles`: Async file I/O
- `pymongo`: MongoDB operations
- `python-decouple`: Configuration management

## Future Enhancements

Potential improvements:

- Rate limiting strategies for API respect
- Distributed task execution with Prefect Cloud
- Real-time streaming data processing
- Incremental data updates instead of full replacement
- Monitoring dashboards for pipeline metrics
