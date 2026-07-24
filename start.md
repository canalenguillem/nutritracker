# Implementation status

The project is implemented sequentially according to the phases requested by the
product owner. Phase 2 is complete: the containerised foundation, persistence
layer, Alembic migration, user domain models and role foundation have been
compiled, started and health-checked successfully. Authentication and later
product features remain intentionally deferred.

Run the development application with:

```bash
docker compose up --build
```

See [`README.md`](./README.md) for the complete setup and verification guide.
