# Implementation status

The project is implemented sequentially according to the phases requested by the
product owner. Phase 5 is complete: a meal described in words is turned into an
estimate the person reviews before anything is stored. The estimator sits behind
a port, so the flow is covered by tests without reaching the provider; running it
against OpenAI requires a key in `.env`. The user profile and photograph upload
remain intentionally deferred.

Run the development application with:

```bash
docker compose up --build
```

See [`README.md`](./README.md) for the complete setup and verification guide.
