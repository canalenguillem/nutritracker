# Implementation status

The project is implemented sequentially according to the phases requested by the
product owner. Phase 6 is complete: a meal can be described in words and backed
by a photograph of its nutrition label, which the estimator reads and then drops
without storing it. Running the estimator against OpenAI requires a key in
`.env`. The user profile and keeping photographs alongside a meal remain
intentionally deferred.

Run the development application with:

```bash
docker compose up --build
```

See [`README.md`](./README.md) for the complete setup and verification guide.
