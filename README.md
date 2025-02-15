# Personalized Shopping Assistant API Documentation

**Version:** 1.0  
**Base URL:** `http://127.0.0.1:5000/api`

**Overview:**  
This API enables a personalized shopping experience by managing users, their preferences, and shopping sessions. It leverages OpenAI’s Assistants API to power real-time chat interactions and generate tailored product descriptions based on user conversation history and product page details. Data is stored in CSV files (for demo purposes) located in the `DemoDatabase` folder.

---

## Table of Contents

1. [User Management](#user-management)
   - [Create User](#create-user)
   - [Login](#login)
2. [User Preferences](#user-preferences)
   - [Update Preferences](#update-preferences)
   - [Get Preferences](#get-preferences)
3. [Shopping Sessions](#shopping-sessions)
   - [Create Shopping Session](#create-shopping-session)
   - [Get Shopping Session](#get-shopping-session)
   - [Get All Sessions for a User](#get-all-sessions-for-a-user)
   - [Add Chat Message to Session](#add-chat-message-to-session)
   - [Generate Product Description](#generate-product-description)
4. [Testing the API](#testing-the-api)
5. [Additional Notes](#additional-notes)

---

## 1. User Management

### Create User

**Endpoint:**  
`POST /api/users`

**Description:**  
Creates a new user with the provided name, email, and password.

**Request Body Example:**

```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "securepassword"
}
```

**Response Example:**

```json
{
  "user_id": "1",
  "name": "John Doe",
  "email": "john@example.com",
  "created_at": "2025-02-06T12:00:00"
}
```

**cURL Example:**

```bash
curl -X POST http://127.0.0.1:5000/api/users 
  -H "Content-Type: application/json" 
  -d '{"name": "John Doe", "email": "john@example.com", "password": "securepassword"}'
```

---

### Login

**Endpoint:**  
`POST /api/login`

**Description:**  
Authenticates a user using email and password. Returns the user info if the credentials are correct.

**Request Body Example:**

```json
{
  "email": "john@example.com",
  "password": "securepassword"
}
```

**Response Example (Success):**

```json
{
  "user_id": "1",
  "name": "John Doe",
  "email": "john@example.com"
}
```

**cURL Example:**

```bash
curl -X POST http://127.0.0.1:5000/api/login 
  -H "Content-Type: application/json" 
  -d '{"email": "john@example.com", "password": "securepassword"}'
```

---

## 2. User Preferences

### Update Preferences

**Endpoint:**  
`POST /api/users/<user_id>/preferences`

**Description:**  
Creates or updates user preferences.

**Request Body Example:**

```json
{
  "preferences": [
    { "key": "budget", "value": "$100-$200" },
    { "key": "color", "value": "red" }
  ]
}
```

**Response Example:**

```json
{
  "message": "Preferences updated",
  "updated_preferences": [
    {
      "preference_id": "1",
      "user_id": "1",
      "preference_key": "budget",
      "preference_value": "$100-$200"
    },
    {
      "preference_id": "2",
      "user_id": "1",
      "preference_key": "color",
      "preference_value": "red"
    }
  ]
}
```

**cURL Example:**

```bash
curl -X POST http://127.0.0.1:5000/api/users/1/preferences 
  -H "Content-Type: application/json" 
  -d '{"preferences": [{"key": "budget", "value": "$100-$200"}, {"key": "color", "value": "red"}]}'
```

---

### Get Preferences

**Endpoint:**  
`GET /api/users/<user_id>/preferences`

**Description:**  
Returns the preferences for the specified user.

**Response Example:**

```json
{
  "user_id": "1",
  "preferences": [
    {
      "preference_id": "1",
      "user_id": "1",
      "preference_key": "budget",
      "preference_value": "$100-$200"
    },
    {
      "preference_id": "2",
      "user_id": "1",
      "preference_key": "color",
      "preference_value": "red"
    }
  ]
}
```

**cURL Example:**

```bash
curl http://127.0.0.1:5000/api/users/1/preferences
```

---

## 3. Shopping Sessions

### Create Shopping Session

**Endpoint:**  
`POST /api/users/<user_id>/shopping_sessions`

**Description:**  
Creates a new shopping session for the user with the specified intent. This endpoint automatically creates a chat thread (using the OpenAI Assistants API) and stores the associated `thread_id` with the session.

**Request Body Example:**

```json
{
  "intent": "Looking for a new pair of running shoes"
}
```

**Response Example:**

```json
{
  "session_id": "1",
  "user_id": "1",
  "thread_id": "thread_xyz",
  "intent": "Looking for a new pair of running shoes",
  "created_at": "2025-02-06T12:05:00",
  "updated_at": "2025-02-06T12:05:00"
}
```

**cURL Example:**

```bash
curl -X POST http://127.0.0.1:5000/api/users/1/shopping_sessions 
  -H "Content-Type: application/json" 
  -d '{"intent": "Looking for a new pair of running shoes"}'
```

---

### Get Shopping Session

**Endpoint:**  
`GET /api/shopping_sessions/<session_id>`

**Description:**  
Retrieves the shopping session details using the session ID.

**Response Example:**

```json
{
  "session_id": "1",
  "user_id": "1",
  "thread_id": "thread_xyz",
  "intent": "Looking for a new pair of running shoes",
  "created_at": "2025-02-06T12:05:00",
  "updated_at": "2025-02-06T12:05:00"
}
```

**cURL Example:**

```bash
curl http://127.0.0.1:5000/api/shopping_sessions/1
```

---

### Get All Sessions for a User

**Endpoint:**  
`GET /api/users/<user_id>/sessions`

**Description:**  
Returns all shopping sessions for the specified user.

**Response Example:**

```json
[
  {
    "session_id": "1",
    "user_id": "1",
    "thread_id": "thread_xyz",
    "intent": "Looking for a new pair of running shoes",
    "created_at": "2025-02-06T12:05:00",
    "updated_at": "2025-02-06T12:05:00"
  },
  {
    "session_id": "2",
    "user_id": "1",
    "thread_id": "thread_abc",
    "intent": "Searching for a smartwatch",
    "created_at": "2025-02-06T13:00:00",
    "updated_at": "2025-02-06T13:00:00"
  }
]
```

**cURL Example:**

```bash
curl http://127.0.0.1:5000/api/users/1/sessions
```

---

### Add Chat Message to Session

**Endpoint:**  
`POST /api/shopping_sessions/<session_id>/messages`

**Description:**  
Adds a new chat message to the conversation thread associated with the shopping session. The endpoint returns the updated list of messages.

**Request Body Example:**

```json
{
  "message": "Can you recommend a good brand for running shoes?"
}
```

**Response Example:**

```json
[
  {
    "id": "msg_123",
    "role": "assistant",
    "created_at": 1699016383,
    "content": "Based on your preferences, I recommend..."
  },
  {
    "id": "msg_124",
    "role": "user",
    "created_at": 1699016400,
    "content": "Can you recommend a good brand for running shoes?"
  }
]
```

**cURL Example:**

```bash
curl -X POST http://127.0.0.1:5000/api/shopping_sessions/1/messages 
  -H "Content-Type: application/json" 
  -d '{"message": "Can you recommend a good brand for running shoes?"}'
```

---

### Generate Product Description

**Endpoint:**  
`POST /api/shopping_sessions/<session_id>/product_description`

**Description:**  
Generates a personalized product description using the product description assistant. This endpoint accepts a product page string and uses the conversation history from the session’s chat thread to generate the description.

**Request Body Example:**

```json
{
  "product_page": "Detailed product page information, in string format."
}
```

**Response Example:**

```json
[
  {
    "id": "msg_200",
    "role": "assistant",
    "created_at": 1699016500,
    "content": "Based on your conversation and the product details, we recommend..."
  }
]
```

**cURL Example:**

```bash
curl -X POST http://127.0.0.1:5000/api/shopping_sessions/1/product_description 
  -H "Content-Type: application/json" 
  -d '{"product_page": "Detailed product page information, including specifications, reviews, and images."}'
```

---

## 4. Testing the API

You can test the API using the provided interactive test client (`test_api_cli.py`). This script presents a menu with the following options:

1. **Create User**  
2. **Get User by ID**  
3. **Update User Preferences**  
4. **Get User Preferences**  
5. **Create Shopping Session**  
6. **Get Shopping Session**  
7. **Add Chat Message to Session**  
8. **Generate Product Description**  
9. **Login**  
10. **Get All Sessions for a User**  
0. **Exit**

### How to Run the Server and Test Client

1. **Start the Server:**  
   Run the Flask server using:

```bash
python app.py
```

   Ensure the server is running on `http://127.0.0.1:5000`.

2. **Run the Test Client:**  
   In another terminal, run:

```bash
python test_api_cli.py
```

   Follow the on-screen prompts to interact with the API.

---
