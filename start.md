# Implementation status

The project is implemented sequentially according to the phases requested by the
product owner. Phase 8 is complete: exercise is recorded and counted against the
day, with the expenditure estimated from the activity, the intensity, the time
and body weight, and the person's own figure taking precedence. Running the food
estimator against OpenAI requires a key in `.env`. The user profile, and with it
the baseline expenditure that turns the daily net into a real balance, remains
intentionally deferred.

Run the development application with:

```bash
docker compose up --build
```

See [`README.md`](./README.md) for the complete setup and verification guide.
