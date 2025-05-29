# Foundation API Documentation

## Base URL

The API base URL is `https://foundation-api.example.com/api/`.

## Authentication

Most endpoints require authentication using JWT tokens.

### Request Authentication

Include the JWT token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

## API Endpoints

### News API

#### Get All News Articles

```
GET /api/news/
```

Query Parameters:
- `cursor`: Pagination cursor (ID of the last item)
- `limit`: Number of items to return (default: 20, max: 100)
- `order`: Sort order, either "asc" or "desc" (default: "desc")
- `category_id`: Filter by category ID
- `featured`: Filter by featured status
- `search`: Search in title or content

Response:
```json
{
  "items": [
    {
      "id": 1,
      "title": "News Title",
      "slug": "news-title",
      "excerpt": "Short excerpt",
      "image_url": "https://example.com/image.jpg",
      "author_id": 1,
      "published_at": "2023-01-15T15:30:00Z",
      "published": true,
      "featured": true,
      "categories": [
        {
          "id": 1,
          "name": "Category Name",
          "slug": "category-name"
        }
      ]
    }
  ],
  "next_cursor": "1",
  "has_more": true
}
```

#### Get a Single News Article

```
GET /api/news/{slug}
```

Response:
```json
{
  "id": 1,
  "title": "News Title",
  "slug": "news-title",
  "content": "Full content",
  "excerpt": "Short excerpt",
  "image_url": "https://example.com/image.jpg",
  "author_id": 1,
  "published_at": "2023-01-15T15:30:00Z",
  "created_at": "2023-01-15T15:20:00Z",
  "updated_at": "2023-01-15T15:25:00Z",
  "published": true,
  "featured": true,
  "categories": [
    {
      "id": 1,
      "name": "Category Name",
      "slug": "category-name"
    }
  ]
}
```

#### Create a News Article

```
POST /api/news/
```

Request Body:
```json
{
  "title": "News Title",
  "content": "Full content",
  "excerpt": "Short excerpt",
  "image_url": "https://example.com/image.jpg",
  "published": true,
  "featured": false,
  "category_ids": [1, 2]
}
```

#### Update a News Article

```
PUT /api/news/{article_id}
```

Request Body (all fields optional):
```json
{
  "title": "Updated Title",
  "content": "Updated content",
  "excerpt": "Updated excerpt",
  "image_url": "https://example.com/new-image.jpg",
  "published": true,
  "featured": true,
  "category_ids": [1, 3]
}
```

#### Delete a News Article

```
DELETE /api/news/{article_id}
```

#### Get News Categories

```
GET /api/news/categories/
```

Response:
```json
[
  {
    "id": 1,
    "name": "Category Name",
    "slug": "category-name"
  }
]
```

#### Create a News Category

```
POST /api/news/categories/
```

Request Body:
```json
{
  "name": "Category Name",
  "slug": "category-name"
}
```

### Events API

#### Get All Events

```
GET /api/events/
```

Query Parameters:
- `cursor`: Pagination cursor (ID of the last item)
- `limit`: Number of items to return (default: 20, max: 100)
- `order`: Sort order, either "asc" or "desc" (default: "desc")
- `upcoming`: Filter for upcoming events only
- `featured`: Filter by featured status
- `search`: Search in title or description

Response:
```json
{
  "items": [
    {
      "id": 1,
      "title": "Event Title",
      "slug": "event-title",
      "location": "Event Location",
      "start_date": "2023-02-15T18:00:00Z",
      "end_date": "2023-02-15T20:00:00Z",
      "image_url": "https://example.com/event.jpg",
      "organizer_id": 1,
      "published": true,
      "featured": true
    }
  ],
  "next_cursor": "1",
  "has_more": true
}
```

#### Get a Single Event

```
GET /api/events/{slug}
```

Response:
```json
{
  "id": 1,
  "title": "Event Title",
  "slug": "event-title",
  "description": "Full description",
  "location": "Event Location",
  "start_date": "2023-02-15T18:00:00Z",
  "end_date": "2023-02-15T20:00:00Z",
  "image_url": "https://example.com/event.jpg",
  "organizer_id": 1,
  "created_at": "2023-02-10T15:20:00Z",
  "updated_at": "2023-02-10T15:25:00Z",
  "published": true,
  "featured": true
}
```

#### Create an Event

```
POST /api/events/
```

Request Body:
```json
{
  "title": "Event Title",
  "description": "Full description",
  "location": "Event Location",
  "start_date": "2023-02-15T18:00:00Z",
  "end_date": "2023-02-15T20:00:00Z",
  "image_url": "https://example.com/event.jpg",
  "published": true,
  "featured": false
}
```

#### Update an Event

```
PUT /api/events/{event_id}
```

Request Body (all fields optional):
```json
{
  "title": "Updated Title",
  "description": "Updated description",
  "location": "Updated Location",
  "start_date": "2023-02-16T18:00:00Z",
  "end_date": "2023-02-16T20:00:00Z",
  "image_url": "https://example.com/new-event.jpg",
  "published": true,
  "featured": true
}
```

#### Delete an Event

```
DELETE /api/events/{event_id}
```

#### Register for an Event

```
POST /api/events/{event_id}/register
```

Request Body:
```json
{
  "name": "Attendee Name",
  "email": "attendee@example.com",
  "phone": "+1234567890"
}
```

Response:
```json
{
  "id": 1,
  "event_id": 1,
  "name": "Attendee Name",
  "email": "attendee@example.com",
  "phone": "+1234567890",
  "created_at": "2023-02-12T14:30:00Z"
}
```

#### Get Event Registrations

```
GET /api/events/{event_id}/registrations
```

Response:
```json
[
  {
    "id": 1,
    "event_id": 1,
    "name": "Attendee Name",
    "email": "attendee@example.com",
    "phone": "+1234567890",
    "created_at": "2023-02-12T14:30:00Z"
  }
]
```

### Contacts API

*Documentation for the contacts API endpoints will be added once the implementation is complete.*

## Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `204 No Content`: Request successful, no content to return
- `400 Bad Request`: Invalid request
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Authenticated but not authorized
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error
