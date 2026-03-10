# Dossier Facile Integration

This app contains the Dossier Facile integration used to:

- connect a student account to Dossier Facile with OAuth2 Authorization Code
- store the linked Dossier Facile tenant in the local database
- expose the tenant dossier metadata to the rest of the backend

This app is the only public API surface for Dossier Facile and is exposed under `/api/dossier-facile/`.

## What Exists In This App

- `DossierFacileTenant`: the business model linked to `Student`
- `DossierFacileOAuthState`: short-lived OAuth state used for the connect flow
- `DossierFacileClient`: wrapper around Dossier Facile HTTP calls
- `DossierFacileConnectUrlView`: returns the external authorize URL
- `DossierFacileCallbackView`: consumes `code` + `state`, syncs the tenant, then redirects to the frontend
- `DossierFacileSyncView`: syncs a tenant for an authenticated student with a fresh authorization code
- `DossierFacileWebhookView`: receives Dossier Facile webhook events

No Django session is used for the OAuth flow.

## Data Model

### `DossierFacileTenant`

This is the persisted business record for a student's linked Dossier Facile account.

Important fields:

- `student`: local student account
- `tenant_id`: Dossier Facile tenant identifier
- `name`: display name resolved from the Dossier Facile profile
- `status`: normalized Dossier Facile status when it matches allowed values
- `url`: Dossier Facile dossier URL
- `pdf_url`: Dossier Facile dossier PDF URL
- `last_synced_at`: last successful sync time

The callback and resync flow use `update_or_create(student=..., tenant_id=...)` to avoid duplicates.

There is also a DB uniqueness constraint on `(student, tenant_id)`.

### `DossierFacileOAuthState`

This model exists only to secure the OAuth redirect round-trip.

- `state` is generated with `secrets.token_urlsafe(32)`
- it is stored server-side in DB
- it is linked to the authenticated user
- it has an `expires_at`
- it is deleted after successful use
- it is also deleted when expired

This avoids storing the JWT in the `state` parameter.

## OAuth Flow

### 1. Frontend asks for a connect URL

Request:

```http
GET /api/dossier-facile/connect-url/
Authorization: Bearer <jwt>
```

Backend behavior:

- checks that the authenticated user is a `Student`
- creates a secure random `state`
- deletes any previous pending state for the same user
- stores the new `DossierFacileOAuthState`
- builds the Dossier Facile authorize URL
- returns the URL and the expiration timestamp

Response shape:

```json
{
  "authorization_url": "https://.../oauth/authorize?...",
  "expires_at": "2026-03-02T12:34:56Z"
}
```

### 2. Frontend redirects the browser

The frontend must redirect the browser to `authorization_url`.

This is a browser redirect, not a backend-to-backend call.

### 3. Dossier Facile redirects back to the frontend

Callback URL:

```http
GET <DOSSIERFACILE_REDIRECT_URI>?code=<code>&state=<state>
```

Frontend behavior:

- reads `code` and `state` from the callback URL
- calls the authenticated `POST /api/dossier-facile/sync/` endpoint with both values

Backend behavior during `sync`:

- validates presence of `code` and `state`
- loads the stored `DossierFacileOAuthState`
- rejects invalid or expired states
- ensures the `state` belongs to the authenticated user
- deletes the state before calling external APIs (one-time use)
- exchanges the `code` for an access token
- fetches the user dossier/profile from Dossier Facile
- extracts `tenant_id`, status, URLs, and display name
- upserts `DossierFacileTenant`
- returns JSON to the frontend

## Frontend Integration Guide

The frontend does not need to generate any OAuth parameters itself.

Recommended flow:

1. User clicks "Connect Dossier Facile".
2. Frontend calls `GET /api/dossier-facile/connect-url/` with the current JWT.
3. Frontend reads `authorization_url`.
4. Frontend redirects `window.location` to that URL.
5. Dossier Facile redirects to the frontend callback URL configured in `DOSSIERFACILE_REDIRECT_URI`.
6. Frontend reads `code` and `state` from the callback URL.
7. Frontend calls `POST /api/dossier-facile/sync/` with the current JWT and the callback payload.
8. Frontend handles success or error locally.

### Important frontend note

The callback endpoint is now a frontend route. Dossier Facile redirects the browser there directly.

That means:

- the frontend must keep the user authenticated until it calls `sync`
- the backend still validates the server-side `state` before exchanging the code

### Callback UX

The frontend owns the callback route and the success/error UX.

## Authenticated Resync

Endpoint:

```http
POST /api/dossier-facile/sync/
Authorization: Bearer <jwt>
Content-Type: application/json
```

Payload:

```json
{
  "code": "<fresh_authorization_code>",
  "state": "<state_from_connect_url>"
}
```

Use this when the frontend receives the Dossier Facile callback and needs the API to complete the OAuth exchange for the authenticated student.

Success response:

```json
{
  "tenant_id": "tenant-123",
  "name": "Jane Doe",
  "status": "verified",
  "url": "https://...",
  "pdf_url": "https://...",
  "last_synced_at": "2026-03-02T12:35:02Z"
}
```

## Error Cases

Common error `type` values returned by the API:

- `not_student`: authenticated user is not a student
- `dossier_facile_not_configured`: required settings are missing
- `missing_oauth_parameters`: `code` or `state` missing on the legacy backend callback
- `invalid_state`: unknown or already-used state
- `expired_state`: state expired
- `invalid_profile`: Dossier Facile response did not contain a usable tenant identifier
- `dossier_facile_token_endpoint_unreachable`
- `dossier_facile_token_exchange_failed`
- `dossier_facile_invalid_token_response`
- `dossier_facile_profile_endpoint_unreachable`
- `dossier_facile_profile_fetch_failed`
- `dossier_facile_invalid_profile_response`

## Settings Required

The integration depends on these Django settings:

- `DOSSIERFACILE_CLIENT_ID`
- `DOSSIERFACILE_CLIENT_SECRET`
- `DOSSIERFACILE_AUTHORIZE_URL`
- `DOSSIERFACILE_TOKEN_URL`
- `DOSSIERFACILE_TENANT_PROFILE_URL`
- `DOSSIERFACILE_REDIRECT_URI`
- `DOSSIERFACILE_SCOPE`
- `DOSSIERFACILE_TIMEOUT_SECONDS`
- `DOSSIERFACILE_STATE_TTL_SECONDS`
- `DOSSIERFACILE_WEBHOOK_API_KEY`
- `DOSSIERFACILE_FRONTEND_SUCCESS_URL` (optional, legacy backend callback only)
- `DOSSIERFACILE_FRONTEND_ERROR_URL` (optional, legacy backend callback only)

Recommended defaults already used in code:

- `DOSSIERFACILE_TIMEOUT_SECONDS=10`
- `DOSSIERFACILE_STATE_TTL_SECONDS=600`

## Webhook

Endpoint:

```http
POST /api/dossier-facile/webhook/
X-Api-Key: <DOSSIERFACILE_WEBHOOK_API_KEY>
```

The webhook is independent from the OAuth callback and from the authenticated `sync` endpoint.

It is used by Dossier Facile to push later updates. The current processing logic is implemented in:

- `dossier_facile/event_processor.py`

Supported event types currently handled by rules:

- `VERIFIED_ACCOUNT`
- `ACCESS_REVOKED`
- `DENIED_ACCOUNT`
- `DELETED_ACCOUNT`

Webhook behavior summary:

- validates `X-Api-Key`
- dispatches the event through `event_processor.py`
- updates or deletes local data depending on the event type
- returns `200` when an event is handled
- returns `400` when no rule matches
- returns `401` when the API key is invalid

## Notes For Backend Developers

- This app is now the only public API surface for Dossier Facile.
- `Student` exposes compatibility properties like `student.dossierfacile_status`, but the source of truth is `DossierFacileTenant`.
- If you need to check whether a student has a valid dossier, read the latest `DossierFacileTenant` for that student.
- The authenticated `sync` flow intentionally does not trust client state beyond the opaque `state` token stored in DB.
- External calls use `requests` with a timeout through `DossierFacileClient`.
- The canonical "validated dossier" status stored in DB is `verified`.
- The legacy Dossier Facile routes in `account` have been removed.

## Maintenance

Cleanup expired OAuth states periodically:

```bash
python manage.py cleanup_dossier_facile_oauth_states
```

## Files To Read First

- [models.py](/Users/pierrechene/Documents/dev/mle-back/dossier_facile/models.py)
- [services.py](/Users/pierrechene/Documents/dev/mle-back/dossier_facile/services.py)
- [views.py](/Users/pierrechene/Documents/dev/mle-back/dossier_facile/views.py)
- [urls.py](/Users/pierrechene/Documents/dev/mle-back/dossier_facile/urls.py)
