# Engineering conventions

NutriTrack AI follows the architecture and implementation sequence in
[`project-spec.md`](./project-spec.md). The following rules apply to every phase:

- Keep source code, identifiers and filenames in English.
- Keep the initial user interface in Spanish.
- Place business logic in services and persistence logic in repositories.
- Validate API data with Pydantic and browser form data with Zod.
- Keep internal timestamps in UTC and convert them only for display.
- Read configuration and secrets from environment variables.
- Complete and verify one phase before starting the next one.
