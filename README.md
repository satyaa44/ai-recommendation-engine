# AI-Powered Recommendation Engine 🤖

A production-ready recommendation system with Collaborative Filtering, User Tracking, and Real-time Analytics.

## Tech Stack

- **Backend:** NestJS + TypeScript
- **Database:** PostgreSQL
- **ML Service:** Python (Scikit-learn)
- **Cache:** Redis
- **Deployment:** Docker

## Features

✅ User Authentication (JWT)
✅ Product Catalog Management
✅ User Interaction Tracking
✅ AI-Powered Recommendations
✅ Real-time Analytics
✅ A/B Testing Ready
✅ Performance Monitoring

## Project Structure

```
src/
├── modules/
│   ├── auth/              # JWT authentication
│   ├── users/             # User management
│   ├── products/          # Product catalog
│   ├── tracking/          # User behavior tracking
│   ├── recommendations/   # ML recommendations
│   └── analytics/         # Analytics dashboard
└── main.ts
```

## Setup & Installation

### Using Docker Compose
```bash
docker-compose up -d
```

### Manual Setup
```bash
# Install dependencies
npm install

# Create .env file
cp .env.example .env

# Run database migrations
npm run migration:run

# Start development server
npm run start:dev
```

## API Endpoints

### Auth
- `POST /auth/register` - Register user
- `POST /auth/login` - Login

### Products
- `GET /products` - List products
- `GET /products/:id` - Get product
- `POST /products` - Create product
- `GET /products/search?q=query` - Search

### Recommendations
- `GET /recommendations/user/:userId` - Get recommendations
- `POST /recommendations/:id/click` - Track click
- `POST /recommendations/:id/purchase` - Track purchase

### Analytics
- `GET /analytics/user-summary?userId=id` - User stats
- `GET /analytics/trending-products` - Trending items
- `GET /analytics/recommendation-performance` - Performance metrics

## Example Usage

### Register User
```bash
curl -X POST http://localhost:3000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "john_doe",
    "password": "SecurePassword123",
    "firstName": "John",
    "lastName": "Doe"
  }'
```

### Get Recommendations
```bash
curl -X GET "http://localhost:3000/recommendations/user/{userId}?limit=10" \
  -H "Authorization: Bearer {accessToken}"
```

## Database Schema

### users
- id, email, username, password, firstName, lastName, preferences, metadata, isActive, createdAt, updatedAt

### products
- id, name, description, price, category, imageUrl, tags, features, rating, reviewCount, viewCount, purchaseCount, isActive, createdAt, updatedAt

### user_interactions
- id, userId, productId, interactionType (view/click/purchase/rating), weight, rating, metadata, isActive, createdAt

### recommendations
- id, userId, productId, score, algorithm, rank, metadata, clicked, purchased, createdAt, updatedAt

## Environment Variables

See `.env.example` for all configuration options.

## Testing

```bash
npm run test           # Unit tests
npm run test:e2e      # E2E tests
npm run test:cov      # With coverage
```

## License

MIT

## Author

Satya - AI/DS Student
