# Shared Recipe Application

- Recipe platform for multiple users. Create, browse, rate, and copy recipes.
- Build a shopping list from a recipe's ingredients

Built on a Django + PostgreSQL backend, React + Typescript frontend

---

## Table of Contents

- [Quick Start](#quick-start)
- [Seeding Data](#seeding-data)
- [API Reference](#api-reference)
- [Design Decisions](#design-decisions)
- [Project Structure](#project-structure)
- [Scope](#scope)
- [Future Considerations](#future-considerations)

## Quick Start

Requires Docker and Docker Compose

```
cp .env.example .env
docker compose up --build
docker compose exec backend python manage.py migrate
```

Should start containers for:
- database: PostgreSQL
- backend: Django
- frontend: Vite

## Seeding Data

```
docker compose exec backend python manage.py seed_data
```

- Default of 15 users, 40 recipes
- `--users=N` / `--recipes=N` to generate larger (or smaller) data sets. `--recipes` alone (with `--users=0`) adds recipes against the existing seeded users rather than requiring new ones.
- `--clear` deletes existing seed data (non-staff users and everything of theirs) and unreferenced catalog rows before reseeding — staff/superuser accounts, and anything they own, are preserved
- All seeded users share one password, `seedpass123`, printed on completion

## API Reference

Use self-documenting API via DRF
Additional details in this README.md

### Error Codes

The following error codes are returned in the API response body and will grow as later sub-projects add their own (e.g., `stale_write`, `duplicate_review`, `tag_limit_exceeded`, etc.):

| Code | HTTP Status | Meaning |
|---|---|---|
| `not_authenticated` | 401 | No valid session. Call `/api/auth/login/` first |
| `authentication_failed` | 401 | Login credentials were wrong (doesn't say which field) |
| `permission_denied` | 403 | Authenticated, but not the owner/staff |
| `not_found` | 404 | Resource doesn't exist (or exists but isn't yours) |
| `validation_error` | 400 | Field-level validation failed — see the `errors` object in the response body |

## Design Decisions

### Django layering vs Repository Pattern

Django ORM with models that maintain their own validation (`clean()` on the model) and a thin `services.py` per app for operations that involve more than one model gives clear separation of concerns.
An interface on top of the ORM is unnecessary, and PostgreSQL is not something that would be swapped out for any future work.

### Business Rules

The following are the rules of the system as per the provided document
- One review per user per recipe
- Max of five tags per recipe

Rules will be enforced at the model or serializer layer, while the view only needs to parse, delegate, and map results. 
Database constraints like `unique_together` for one review per user along with serializer-layer checks also ensures the user can see clean error messages.
Each rule should have only one place to change and one place to test, to ensure no drifts can happen from multiple implementations.

### Concurrency

Optimistic locking is used instead of database-level row locking. Recipe edits are not a high contention path, so this avoids making every request pay for a lock that's almost never contended.

Uses `django-concurrency`'s `IntegerVersionField` and the version check is enforced inside `Model.save()` so it protects every write path uniformly for both REST API and Django Admin.

### Authentication

Django's built-in session authentication with CSRF rather than JWT is chosen here. The reasoning is as follows:
- Trivial revocation to invalidate a session
- Lower XSS exposure with `httponly` for a session cookie. JS cannot read it even under an XSS vulnerability

The tradeoffs for using session authentication are as follows:
- Statelessness that JWT provides across multiple backend instances. Revisit if the app needs to serve a mobile client, 3rd party API consumer, or a use case that doesn't extend cleanly for cookie-based auth

### Frontend Rendering Strategy

Considering this is a recipe-discovery site, it could be argued that server-side rendering is a great choice for the faster first paint and SEO benefits.
However, I chose a client-side rendered React SPA for the following reasons:
- Take-home challenge scope: Easy to containerize, lightweight, thin client
- Discoverability is not a part of the evaluation, but if this was to go into production, SSR would need a revisit

### Performance at Scale

Some notes that consider how the system handles a larger data set. This can be checked against real numbers via the seeding parameters
- Recipe grid endpoint returns a lighter payload
- Avoid N+1 query patterns as dataset grows using `select_related` or `prefetch_related`
- Indexing on filterable and sorted columns

#### Review and Rating Count
- The average rating and review count are currently computed at read time. Every list request joins Recipe to all Review and does a GROUP BY which scales with total review count. 
  - EXPLAIN ANALYZE measured that the dominant cost of the RecipeViewSet query path is the GroupAggregate that computes the average rating
- Performance here can be improved by computing at write time, storing avg_rating and review_count as real columns on Recipe. We choose this tradeoff as the list of recipes is heavier on reads, while reviews are written less

## Project Structure

Below is the planned project structure
```
backend/
  accounts/       # auth (login/logout/register), shared permissions
  recipes/        # Recipe, Ingredient, Tag, Review models + API + seed command
  shopping_list/  # ShoppingList, ShoppingListItem models + API
frontend/
  src/api/        # single typed API client
  src/hooks/      # TanStack Query hooks, one per resource
  src/components/ # presentational components
  src/pages/      # composition roots
```

## Scope

Below is the scope of the project, as well as what would fall out of scope for the first implementation

### In Scope
- Full Recipe CRUD with ownership enforcement
- Structured ingredients and tags
- Reviewing recipes
- Recipe copying with tracking of origin
- Personal shopping list with recipe-import and manual ingredient entry
- Django Admin for staff management

### Out of Scope
- Unit Conversion Aware for merging shopping list items
- Catalog deduplication
- Real Image processing
- SSR
- Media Storage
- Live Deployment

### Future Considerations

Related to the above Out of Scope items:
- Image processing for this implementation stores and serves images as-is. Production version should move storage to an S3 compatible object store. Additionally, uplaods would be processed asynchronously via a task queue (eg. Celery) to avoid blocking the request/response.
- Unit conversion aware for shopping list merging of items. Per ingredient density data would be necessary (a cup of flour's weight vs a cup of sugar) to tackle this feature
- Fuzzy catalog deduplication would be beneficial for any duplicate tags or ingredients
- SSR as mentioned would be useful if discoverability is needed by the application
- Login and register are not rate-limited. A production deployment would add DRF throttling (`AnonRateThrottle`) to both endpoints to handle any brute-force/credential-stuffing attempts
- `get_or_create_ci` (tag/ingredient resolution on recipe create/update) issues one SELECT, plus a possible INSERT, per submitted name. Fine for a single recipe's ingredient list typed by hand through the API, but could be a concern for recipes with a lot of ingredients. The fix is the standard bulk get-or-create/upsert pattern: one query to fetch existing matches (`annotate(Lower("name"))` + `filter(__in=...)`), then `bulk_create(..., ignore_conflicts=True)` for whatever's missing to reduce to 2-3 queries total regardless of row count, instead of up to 2N. A true single-query Postgres upsert (`INSERT ... ON CONFLICT ... RETURNING`) is also possible via the third-party `django-postgres-extra` package's `on_conflict()`, but Django core's `bulk_create` + a follow-up lookup covers this without adding a dependency.
- Editing or removing individual shopping-list items, and checking items off (`ShoppingListItem.is_checked` exists on the model but isn't exposed via the API). Editing, removing, and checking off were deferred to get full coverage of the stated requirements first
