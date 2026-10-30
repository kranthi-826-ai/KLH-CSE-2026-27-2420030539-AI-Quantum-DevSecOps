# Auth Service API

The API Gateway exposes the auth service at `http://localhost:8080/api/v1/auth`.

## Register

`POST /register`

```json
{
  "username": "testuser",
  "password": "Test@1234"
}
```

Successful response: `201 Created`.

## Login

`POST /login`

```json
{
  "username": "testuser",
  "password": "Test@1234"
}
```

Successful response: `200 OK`. The response contains a signed JWT in the `token` field.

## Current authenticated user

`GET /me`

Include the token returned by login:

```text
Authorization: Bearer <token>
```

Successful response: `200 OK`.

```json
{
  "username": "testuser",
  "role": "ROLE_USER"
}
```

Missing, expired, incorrectly signed, or malformed tokens receive `401 Unauthorized`.
