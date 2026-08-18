# Implementation status

The project is implemented sequentially according to the phases requested by the
product owner. Phase 9 is complete: the profile holds height, target weight and
the figures a metabolic estimate needs, and weight is tracked day by day with an
exponentially smoothed trend, charted against the target. Running the food
estimator against OpenAI requires a key in `.env`. Baseline expenditure, which
would turn the daily net into a real balance, remains intentionally deferred
even though the profile now carries what it needs.

Run the development application with:

```bash
docker compose up --build
```

See [`README.md`](./README.md) for the complete setup and verification guide.
