# E-commerce Store API

A complete Flask-based REST API for an e-commerce store with cart functionality, checkout process, and discount code management.

## Features

- **Cart Management**: Add items to cart, view cart contents
- **Checkout Process**: Place orders with optional discount codes
- **Discount System**: Automatic discount code generation every nth order (configurable)
- **Admin Panel**: Generate discount codes manually and view store statistics
- **In-Memory Storage**: Fast, lightweight data persistence (easily replaceable with database)
- **Comprehensive Testing**: Full test coverage with unit tests
- **Production Ready**: Proper error handling, logging, and configuration

## API Endpoints

### Customer Endpoints

#### Add Item to Cart
```http
POST /cart/{user_id}/items
Content-Type: application/json

{
    "item_id": "string",
    "name": "string",
    "price": number,
    "quantity": integer
}
```

#### Get Cart
```http
GET /cart/{user_id}
```

#### Checkout
```http
POST /cart/{user_id}/checkout
Content-Type: application/json

{
    "discount_code": "string" (optional)
}
```

### Admin Endpoints

#### Generate Discount Code
```http
POST /admin/discount-codes
```

#### Get Store Statistics
```http
GET /admin/stats
```

#### List Discount Codes
```http
GET /admin/discount-codes
```

### Utility Endpoints

#### Health Check
```http
GET /health
```

## Quick Start

### Prerequisites
- Python 3.8+
- pip

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd ecommerce-store-api
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run the application**
```bash
python app.py
```

The API will be available at `http://localhost:5000`

### Using Docker

1. **Build the image**
```bash
docker build -t ecommerce-api .
```

2. **Run the container**
```bash
docker run -p 5000:5000 ecommerce-api
```

## Configuration

The application can be configured using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_ENV` | `development` | Application environment |
| `SECRET_KEY` | `dev-secret-key-change-in-production` | Flask secret key |
| `DISCOUNT_ORDER_FREQUENCY` | `3` | Every nth order gets discount code |
| `DISCOUNT_PERCENTAGE` | `10.0` | Discount percentage |
| `DISCOUNT_CODE_EXPIRY_DAYS` | `30` | Days until discount code expires |
| `LOG_LEVEL` | `INFO` | Logging level |

## Testing

### Run all tests
```bash
python -m pytest test_app.py -v
```

### Run with coverage
```bash
python -m pytest test_app.py --cov=. --cov-report=html
```

### Run specific test class
```bash
python -m pytest test_app.py::EcommerceAPITestCase -v
```

## API Usage Examples

### Example 1: Basic Shopping Flow

1. **Add items to cart**
```bash
curl -X POST http://localhost:5000/cart/user123/items \
  -H "Content-Type: application/json" \
  -d '{
    "item_id": "laptop001",
    "name": "Gaming Laptop",
    "price": 999.99,
    "quantity": 1
  }'
```

2. **View cart**
```bash
curl http://localhost:5000/cart/user123
```

3. **Checkout**
```bash
curl -X POST http://localhost:5000/cart/user123/checkout \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Example 2: Using Discount Code

1. **Checkout with discount code**
```bash
curl -X POST http://localhost:5000/cart/user123/checkout \
  -H "Content-Type: application/json" \
  -d '{
    "discount_code": "DISCOUNT12345678"
  }'
```

### Example 3: Admin Operations

1. **Generate discount code**
```bash
curl -X POST http://localhost:5000/admin/discount-codes
```

2. **Get store statistics**
```bash
curl http://localhost:5000/admin/stats
```

## Business Logic

### Discount Code System

- **Automatic Generation**: Every nth order (default: 3rd) automatically generates a new discount code
- **Single Use**: Each discount code can only be used once
- **Expiration**: Discount codes expire after 30 days (configurable)
- **Validation**: Codes are validated before applying discount during checkout

### Cart Management

- **User-specific**: Each user has their own cart
- **Item Consolidation**: Adding same item multiple times increases quantity
- **Persistent**: Carts persist until checkout or manual clearing
- **Validation**: All items are validated before adding to cart

### Order Processing

- **Atomic**: Orders are created atomically with all validations
- **Discount Application**: Discounts are applied to entire order, not individual items
- **Cart Clearing**: Cart is automatically cleared after successful checkout
- **Order History**: All orders are stored for admin reporting

## Error Handling

The API provides comprehensive error handling with appropriate HTTP status codes:

- `400 Bad Request`: Invalid request data or business logic violations
- `404 Not Found`: Resource not found
- `405 Method Not Allowed`: HTTP method not supported for endpoint
- `500 Internal Server Error`: Unexpected server errors

All errors return JSON responses with descriptive error messages:

```json
{
  "error": "Description of what went wrong"
}
```

## Data Models

### Item
```json
{
  "item_id": "string",
  "name": "string",
  "price": number,
  "quantity": integer,
  "subtotal": number
}
```

### Cart
```json
{
  "user_id": "string",
  "items": [Item],
  "total_items": integer,
  "total_amount": number,
  "created_at": "ISO datetime",
  "updated_at": "ISO datetime"
}
```

### Order
```json
{
  "order_id": "string",
  "user_id": "string",
  "items": [Item],
  "subtotal": number,
  "discount_code": "string | null",
  "discount_amount": number,
  "total_amount": number,
  "created_at": "ISO datetime"
}
```

### Discount Code
```json
{
  "code": "string",
  "discount_percentage": number,
  "is_used": boolean,
  "created_at": "ISO datetime",
  "used_at": "ISO datetime | null",
  "expires_at": "ISO datetime",
  "is_valid": boolean
}
```

## Architecture

The application follows a clean architecture pattern:

```
app.py              # Flask application and routes
├── models.py       # Data models and in-memory store
├── services.py     # Business logic layer
├── validators.py   # Request validation
├── config.py       # Configuration management
└── test_app.py     # Comprehensive test suite
```

### Key Components

- **Models**: Data structures and storage interface
- **Services**: Business logic separated from HTTP concerns  
- **Validators**: Input validation and sanitization
- **Configuration**: Environment-based configuration management

## Production Considerations

### Security
- Use strong `SECRET_KEY` in production
- Implement authentication/authorization as needed
- Add rate limiting for API endpoints
- Use HTTPS in production

### Scalability
- Replace in-memory store with database (PostgreSQL, MongoDB)
- Add caching layer (Redis) for better performance
- Implement proper session management
- Add connection pooling for database

### Monitoring
- Add application metrics (Prometheus)
- Implement structured logging
- Add health checks and readiness probes
- Set up error tracking (Sentry)

### Deployment
- Use container orchestration (Kubernetes)
- Set up CI/CD pipeline
- Configure load balancing
- Add environment-specific configurations

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## Testing Strategy

The test suite covers:

- **API Endpoints**: All HTTP endpoints with various scenarios
- **Business Logic**: Core functionality in service layer
- **Data Models**: Model validation and behavior
- **Error Handling**: Error conditions and edge cases
- **Integration**: End-to-end workflows

### Test Coverage Areas

- ✅ Cart operations (add, view, clear)
- ✅ Checkout process (with/without discounts)
- ✅ Discount code generation and validation
- ✅ Admin statistics and management
- ✅ Error scenarios and edge cases
- ✅ Data model validation
- ✅ Service layer business logic

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions or issues, please:
1. Check existing issues on GitHub
2. Create a new issue with detailed description
3. Include steps to reproduce for bugs
4. Provide environment information for deployment issues