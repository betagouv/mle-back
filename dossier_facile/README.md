# Dossier Facile Integration

This app contains the Dossier Facile integration used to:

- connect a student account to Dossier Facile with OAuth2 Authorization Code
- store the linked Dossier Facile tenant in the local database
- expose the tenant dossier metadata to the rest of the backend

The preferred API entrypoint for this flow is under `/api/dossier-facile/`.

## What Exists In This App

- `DossierFacileTenant`: the business model linked to `Student`
- `DossierFacileOAuthState`: short-lived OAuth state used for the connect flow
- `DossierFacileClient`: wrapper around Dossier Facile HTTP calls
- `DossierFacileConnectUrlView`: returns the external authorize URL
- `DossierFacileCallbackView`: consumes `code` + `state`, then syncs the tenant
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

The callback uses `update_or_create(student=..., tenant_id=...)` to avoid duplicates.

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

### 3. Dossier Facile redirects back to the backend

Callback URL:

```http
GET /api/dossier-facile/callback/?code=<code>&state=<state>
```

Backend behavior:

- validates presence of `code` and `state`
- loads the stored `DossierFacileOAuthState`
- rejects invalid or expired states
- deletes the state before calling external APIs (one-time use)
- exchanges the `code` for an access token
- fetches the user dossier/profile from Dossier Facile
- extracts `tenant_id`, status, URLs, and display name
- upserts `DossierFacileTenant`

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

## Frontend Integration Guide

The frontend does not need to generate any OAuth parameters itself.

Recommended flow:

1. User clicks "Connect Dossier Facile".
2. Frontend calls `GET /api/dossier-facile/connect-url/` with the current JWT.
3. Frontend reads `authorization_url`.
4. Frontend redirects `window.location` to that URL.
5. Dossier Facile redirects to the backend callback URL configured in settings.
6. The backend completes the link and returns JSON.

### Important frontend note

The callback endpoint is a backend endpoint. Dossier Facile calls it directly in the browser redirect.

That means:

- the frontend does not send the JWT on the callback
- the callback works because the backend resolves the user from the stored server-side `state`

### How the frontend should handle callback UX

Because the callback currently returns JSON, the browser will land on a JSON response after Dossier Facile redirects back.

For a smoother UX, a common next step is to change the callback so it redirects to a frontend route such as:

- `/profile/dossier-facile/success`
- `/profile/dossier-facile/error`

That is not implemented in the current V1. The current V1 is API-first and returns JSON.

## Error Cases

Common error `type` values returned by the API:

- `not_student`: authenticated user is not a student
- `dossier_facile_not_configured`: required settings are missing
- `missing_oauth_parameters`: `code` or `state` missing on callback
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

Recommended defaults already used in code:

- `DOSSIERFACILE_TIMEOUT_SECONDS=10`
- `DOSSIERFACILE_STATE_TTL_SECONDS=600`

## Webhook

Endpoint:

```http
POST /api/dossier-facile/webhook/
X-Api-Key: <DOSSIERFACILE_WEBHOOK_API_KEY>
```

The webhook is independent from the OAuth callback.

It is used by Dossier Facile to push later updates. The current processing logic is implemented in:

- `dossier_facile/event_processor.py`

## Notes For Backend Developers

- `account` still contains older Dossier Facile endpoints for backward compatibility, but new integration work should prefer the endpoints in this app.
- `Student` exposes compatibility properties like `student.dossierfacile_status`, but the source of truth is `DossierFacileTenant`.
- If you need to check whether a student has a valid dossier, read the latest `DossierFacileTenant` for that student.
- The callback intentionally does not trust client state beyond the opaque `state` token stored in DB.
- External calls use `requests` with a timeout through `DossierFacileClient`.

## Files To Read First

- [models.py](/Users/pierrechene/Documents/dev/mle-back/dossier_facile/models.py)
- [services.py](/Users/pierrechene/Documents/dev/mle-back/dossier_facile/services.py)
- [views.py](/Users/pierrechene/Documents/dev/mle-back/dossier_facile/views.py)
- [urls.py](/Users/pierrechene/Documents/dev/mle-back/dossier_facile/urls.py)
