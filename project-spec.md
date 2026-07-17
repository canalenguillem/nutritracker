# Project Briefing — AI Food & Calorie Tracker

## 1. Project name

**NutriTrack AI**  
Nombre provisional. Debe poder cambiarse mediante variables de entorno y configuración del frontend.

---

## 2. Project objective

Crear una aplicación web responsive para registrar diariamente:

- Comidas mediante fotografía.
- Alimentos introducidos manualmente.
- Bebidas.
- Entrenamientos y actividad física.
- Peso corporal.
- Objetivo de peso.
- Calorías consumidas.
- Calorías gastadas estimadas.
- Balance y déficit calórico diario.
- Evolución semanal y mensual.

La aplicación utilizará visión artificial mediante la API de OpenAI para reconocer los alimentos presentes en una fotografía y devolver una estimación editable de:

- Nombre del alimento.
- Cantidad aproximada.
- Unidad.
- Calorías.
- Proteínas.
- Grasas.
- Carbohidratos.
- Nivel de confianza.
- Preguntas necesarias para mejorar la estimación.

La IA nunca debe guardar automáticamente una estimación como definitiva. El usuario debe poder revisarla, corregir cantidades y confirmar el registro.

---

## 3. Target users

### Initial version

Uso personal y pequeños grupos de usuarios.

### Future version

Aplicación SaaS para:

- Personas que quieren perder peso.
- Personas que siguen dietas bajas en carbohidratos o keto.
- Deportistas.
- Nutricionistas que supervisan clientes.
- Entrenadores personales.

---

## 4. Technology stack

Todo el proyecto debe ejecutarse mediante Docker Compose.

### Backend

- Python 3.12
- FastAPI
- SQLAlchemy 2
- Alembic
- Pydantic
- JWT access tokens
- Refresh tokens seguros
- Authlib o librería equivalente para Google OAuth
- OpenAI Python SDK
- Pillow para validación y procesamiento básico de imágenes

### Frontend

- TypeScript
- React
- Vite
- React Router
- TanStack Query
- React Hook Form
- Zod
- Axios o cliente HTTP centralizado
- Diseño responsive mobile-first

### Databases and services

- MariaDB
- Redis
- MongoDB opcional para almacenar respuestas completas de IA y trazas
- n8n para automatizaciones futuras
- Nginx como reverse proxy
- phpMyAdmin
- Mongo Express si se activa MongoDB

### Infrastructure

- Docker Compose
- Volúmenes persistentes dentro de `./volumes`
- Variables centralizadas en `.env`
- Nombres de contenedores prefijados mediante `PROJECT_PREFIX`
- Entornos: development y production

---

## 5. Authentication

La aplicación debe permitir dos métodos de acceso.

### 5.1 Email and password

Funciones necesarias:

- Registro con nombre, correo electrónico y contraseña.
- Validación del formato del correo.
- Contraseña mínima de 8 caracteres.
- Hash de contraseña con Argon2id o bcrypt.
- Inicio de sesión.
- Cierre de sesión.
- Refresh token.
- Recuperación de contraseña.
- Confirmación del correo electrónico.
- Cambio de contraseña.
- Bloqueo temporal tras varios intentos fallidos.
- Opción para mantener la sesión iniciada.

Nunca se debe almacenar una contraseña en texto plano.

### 5.2 Google login

El botón debe mostrar:

**Continuar con Google**

Utilizar Google OAuth 2.0 / OpenID Connect.

Flujo:

1. El usuario pulsa “Continuar con Google”.
2. El frontend redirige al endpoint OAuth del backend.
3. Google autentica al usuario.
4. El backend recibe el callback.
5. Se valida el identificador y el correo verificado.
6. Si el usuario no existe, se crea.
7. Si ya existe con el mismo correo, se vincula la identidad de Google.
8. El backend genera la sesión de la aplicación.
9. El usuario es redirigido al panel.

No se debe solicitar ni almacenar la contraseña de Gmail.

### 5.3 Account linking

Un mismo usuario puede disponer de:

- Acceso mediante contraseña.
- Acceso mediante Google.
- Ambos métodos vinculados a la misma cuenta.

La vinculación debe realizarse por correo verificado y requerir confirmación cuando exista riesgo de conflicto.

---

## 6. User roles

### User

Puede:

- Gestionar su perfil.
- Registrar comidas, bebidas, peso y entrenamientos.
- Consultar sus estadísticas.
- Modificar y eliminar sus registros.
- Exportar sus datos.

### Admin

Puede:

- Consultar usuarios.
- Activar o desactivar cuentas.
- Revisar errores de análisis de IA.
- Consultar consumo estimado de la API.
- Gestionar configuraciones generales.
- Consultar auditoría sin acceder innecesariamente a información privada.

### Future role: nutritionist

Podrá acceder únicamente a usuarios que le hayan concedido permiso explícito.

---

## 7. Main screens

### Public screens

- Landing page.
- Login.
- Register.
- Password recovery.
- Reset password.
- Email verification.
- Privacy policy.
- Terms of service.

### Private screens

- Dashboard.
- Add food photo.
- Review AI analysis.
- Manual food entry.
- Daily diary.
- Exercise entry.
- Weight entry.
- Statistics.
- History.
- User profile.
- Goals and preferences.
- Account and security.
- Data export.
- Admin panel.

---

## 8. Main user flow

### 8.1 First login

1. User creates an account.
2. User completes onboarding.
3. User enters:
   - Date of birth or age range.
   - Sex used for metabolic estimation, optionally.
   - Height.
   - Current weight.
   - Target weight.
   - Typical activity level.
   - Main goal.
4. The application calculates an initial estimated daily calorie target.
5. The user accepts or edits the target.

All calculations must be labelled as estimates and not medical advice.

### 8.2 Add meal using a photo

1. User chooses meal type:
   - Breakfast.
   - Lunch.
   - Dinner.
   - Snack.
   - Drink.
2. User takes or uploads a photograph.
3. Frontend compresses the image.
4. Backend validates:
   - MIME type.
   - Maximum size.
   - Dimensions.
5. Image is stored privately.
6. Backend sends the image to OpenAI.
7. OpenAI returns structured JSON.
8. Application presents detected items.
9. User edits quantities or names.
10. Application asks clarification questions when required.
11. User confirms.
12. Final nutritional values are stored in MariaDB.

### 8.3 Manual entry

The user can add:

- Food name.
- Quantity.
- Unit.
- Calories.
- Macronutrients.
- Notes.
- Time.
- Meal type.

### 8.4 Exercise entry

The user can enter:

- Activity type.
- Duration.
- Intensity.
- Calories manually.
- Estimated calories.
- Notes.
- Date and start time.

Example:

- Activity: Brooklyn Fitboxing.
- Duration: 47 minutes.
- Intensity: high.
- Estimated expenditure: editable.

### 8.5 Daily balance

The dashboard displays:

- Calories consumed.
- Exercise calories.
- Estimated baseline expenditure.
- Estimated total expenditure.
- Daily calorie balance.
- Estimated deficit or surplus.
- Protein, fat and carbohydrates.
- Current weight.
- Progress toward goal.

---

## 9. AI food analysis

### 9.1 Required behaviour

The AI should:

- Detect visible foods and drinks.
- Avoid inventing ingredients that cannot be observed.
- Estimate portions conservatively.
- Distinguish visible facts from assumptions.
- Ask questions about:
  - Oil.
  - Sauces.
  - Sugar.
  - Type of milk or cream.
  - Cooking method.
  - Approximate plate size.
  - Whether the full portion was eaten.
- Return a confidence value for every item.
- Return warnings when the image is unclear.
- Allow multiple photographs for the same meal in a future version.

### 9.2 Expected structured output

```json
{
  "meal_summary": "Grilled chicken with salad",
  "items": [
    {
      "name": "grilled chicken breast",
      "estimated_quantity": 180,
      "unit": "g",
      "estimated_kcal": 297,
      "protein_g": 55.8,
      "fat_g": 6.5,
      "carbohydrates_g": 0,
      "confidence": 0.82,
      "assumptions": [
        "Chicken appears grilled",
        "No visible sauce included"
      ]
    },
    {
      "name": "mixed salad",
      "estimated_quantity": 150,
      "unit": "g",
      "estimated_kcal": 45,
      "protein_g": 2,
      "fat_g": 0.5,
      "carbohydrates_g": 8,
      "confidence": 0.68,
      "assumptions": [
        "Oil is not included"
      ]
    }
  ],
  "clarification_questions": [
    {
      "key": "olive_oil",
      "question": "Did the salad contain olive oil?",
      "type": "single_choice",
      "options": [
        "No",
        "1 teaspoon",
        "1 tablespoon",
        "More than 1 tablespoon",
        "I do not know"
      ]
    }
  ],
  "estimated_total_kcal": 342,
  "analysis_confidence": 0.73,
  "warning": "Calories are an estimate and should be reviewed."
}
```

### 9.3 Prompt rules

The system prompt must instruct the model to:

- Return only valid structured data.
- Never diagnose health conditions.
- Never present calorie values as exact.
- Avoid identifying people in images.
- Ignore irrelevant background elements.
- Flag poor-quality or unrelated images.
- Use the language selected by the user.
- Separate visible evidence from assumptions.

### 9.4 AI processing states

- `pending`
- `processing`
- `needs_review`
- `confirmed`
- `failed`
- `cancelled`

---

## 10. Calorie calculations

### 10.1 Core values

- `food_calories`
- `drink_calories`
- `exercise_calories`
- `estimated_bmr`
- `estimated_tdee`
- `daily_target`
- `daily_balance`

Suggested formula:

```text
daily_balance = consumed_calories - estimated_total_expenditure
```

Interpretation:

- Negative value: estimated deficit.
- Positive value: estimated surplus.

The user interface should display:

```text
Estimated deficit: 640 kcal
```

Never display it as an exact medical measurement.

### 10.2 Exercise calories

Exercise expenditure must be editable because:

- Watches may overestimate.
- Machines may provide different values.
- Duration and intensity affect expenditure.
- Body weight affects expenditure.

Store both:

- `estimated_calories`
- `confirmed_calories`

---

## 11. Database model

### users

- id
- email
- password_hash nullable
- display_name
- avatar_url nullable
- role
- status
- email_verified_at nullable
- locale
- timezone
- created_at
- updated_at
- last_login_at nullable

### auth_identities

- id
- user_id
- provider
- provider_user_id
- provider_email
- created_at
- updated_at

Providers:

- `local`
- `google`

### refresh_tokens

- id
- user_id
- token_hash
- expires_at
- revoked_at nullable
- user_agent nullable
- ip_hash nullable
- created_at

### user_profiles

- id
- user_id
- height_cm nullable
- current_weight_kg nullable
- target_weight_kg nullable
- birth_date nullable
- biological_sex nullable
- activity_level
- primary_goal
- daily_calorie_target nullable
- protein_target_g nullable
- carbohydrate_target_g nullable
- fat_target_g nullable
- created_at
- updated_at

### daily_logs

- id
- user_id
- log_date
- notes nullable
- created_at
- updated_at

Unique index:

- user_id + log_date

### meals

- id
- daily_log_id
- user_id
- meal_type
- eaten_at
- source
- notes nullable
- total_kcal
- protein_g
- fat_g
- carbohydrates_g
- status
- created_at
- updated_at

Sources:

- `photo_ai`
- `manual`
- `imported`

### meal_items

- id
- meal_id
- name
- quantity
- unit
- kcal
- protein_g
- fat_g
- carbohydrates_g
- confidence nullable
- assumptions_json nullable
- user_confirmed
- created_at
- updated_at

### meal_images

- id
- meal_id
- storage_key
- original_filename
- mime_type
- size_bytes
- width
- height
- sha256
- created_at

### ai_analyses

- id
- user_id
- meal_id
- provider
- model
- prompt_version
- status
- raw_response_location nullable
- parsed_response_json nullable
- input_tokens nullable
- output_tokens nullable
- estimated_cost nullable
- error_code nullable
- error_message nullable
- created_at
- completed_at nullable

### exercises

- id
- daily_log_id
- user_id
- activity_name
- duration_minutes
- intensity
- estimated_calories nullable
- confirmed_calories nullable
- source
- performed_at
- notes nullable
- created_at
- updated_at

### weight_entries

- id
- user_id
- measured_at
- weight_kg
- notes nullable
- created_at
- updated_at

### daily_summaries

- id
- user_id
- log_date
- consumed_kcal
- exercise_kcal
- estimated_bmr
- estimated_tdee
- estimated_expenditure
- balance_kcal
- protein_g
- fat_g
- carbohydrates_g
- calculated_at

### audit_logs

- id
- user_id nullable
- action
- entity_type
- entity_id nullable
- metadata_json nullable
- created_at

---

## 12. Backend API

Base path:

```text
/api/v1
```

### Authentication

```text
POST   /auth/register
POST   /auth/login
POST   /auth/refresh
POST   /auth/logout
POST   /auth/forgot-password
POST   /auth/reset-password
GET    /auth/verify-email
GET    /auth/google/login
GET    /auth/google/callback
GET    /auth/me
POST   /auth/link/google
DELETE /auth/link/google
```

### Profile

```text
GET    /profile
PATCH  /profile
PATCH  /profile/goals
PATCH  /profile/password
DELETE /profile/account
```

### Meals

```text
GET    /meals
POST   /meals
GET    /meals/{meal_id}
PATCH  /meals/{meal_id}
DELETE /meals/{meal_id}
POST   /meals/{meal_id}/images
POST   /meals/{meal_id}/analyze
POST   /meals/{meal_id}/confirm
POST   /meals/{meal_id}/reanalyze
```

### Daily diary

```text
GET    /diary/{date}
GET    /diary/{date}/summary
PATCH  /diary/{date}
```

### Exercise

```text
GET    /exercises
POST   /exercises
GET    /exercises/{exercise_id}
PATCH  /exercises/{exercise_id}
DELETE /exercises/{exercise_id}
```

### Weight

```text
GET    /weights
POST   /weights
PATCH  /weights/{weight_id}
DELETE /weights/{weight_id}
```

### Statistics

```text
GET    /statistics/daily
GET    /statistics/weekly
GET    /statistics/monthly
GET    /statistics/weight
GET    /statistics/macros
```

### Administration

```text
GET    /admin/users
GET    /admin/users/{user_id}
PATCH  /admin/users/{user_id}/status
GET    /admin/ai-usage
GET    /admin/errors
GET    /admin/audit
```

---

## 13. Image storage

Development:

```text
./volumes/uploads
```

Production:

- Private S3-compatible storage.
- MinIO is acceptable for self-hosting.
- Signed URLs with expiration.
- Images must not be publicly accessible.
- Remove EXIF metadata where appropriate.
- Generate a smaller analysis copy.
- Preserve the original only if the user consents.

Suggested limits:

- Maximum upload: 10 MB.
- Accepted formats: JPEG, PNG and WebP.
- Reject executables or mismatched MIME types.
- Generate file names with UUID.
- Verify content hash.

---

## 14. Security requirements

- Password hashing with Argon2id preferred.
- Short-lived access tokens.
- Refresh tokens stored hashed.
- Secure, HttpOnly and SameSite cookies in production.
- CSRF protection when cookies are used.
- Rate limiting for login and AI analysis.
- Email verification.
- Password reset tokens with expiration and one-time use.
- Google OAuth `state` validation.
- Strict redirect URI allowlist.
- CORS restricted by environment.
- Input validation with Pydantic and Zod.
- File MIME validation.
- Maximum request size.
- SQL injection protection through ORM.
- Security headers in Nginx.
- Secret keys only in environment variables.
- Logs must not include passwords, tokens or image contents.
- Ownership checks on every private resource.
- Users must never access another user's meals or images.
- Admin actions must be audited.

---

## 15. Privacy

The application handles potentially sensitive lifestyle information.

Required features:

- Explicit consent for AI image analysis.
- Clear notice that images are sent to an external AI provider.
- Ability to delete individual images.
- Ability to delete all account data.
- Export in JSON and CSV.
- Configurable image retention.
- Data minimisation.
- No use of uploaded images for advertising.
- Privacy policy and terms.
- Separate acceptance timestamp for privacy conditions.

Possible retention policy:

- Original image: configurable, default 30 days.
- Derived nutritional record: retained until user deletion.
- AI raw response: 30 days for debugging.
- Audit data: according to legal and operational requirements.

---

## 16. Dashboard requirements

The dashboard should show the current day by default.

Cards:

- Calories consumed.
- Target calories.
- Estimated expenditure.
- Estimated deficit or surplus.
- Protein progress.
- Carbohydrate progress.
- Fat progress.
- Water consumed.
- Latest weight.
- Exercise completed.

Main action:

```text
Add meal photo
```

Secondary actions:

```text
Add food manually
Add drink
Add exercise
Add weight
```

---

## 17. Statistics

### Weekly

- Daily calories consumed.
- Estimated daily deficit or surplus.
- Exercise minutes.
- Weight evolution.
- Average protein.
- Days with complete data.

### Monthly

- Weight change.
- Average calorie balance.
- Training sessions.
- Most frequently logged foods.
- Adherence to target.

Charts must not imply false precision.

---

## 18. Notifications and automations

Future n8n workflows:

- Daily reminder to complete the diary.
- Weekly report by email.
- Alert after several days without weight entry.
- Monthly CSV export.
- Notification when AI analysis fails.
- Admin report of API consumption.
- Optional Telegram bot for adding text records and photographs.

---

## 19. Project structure

```text
nutritrack-ai/
├── .env.example
├── .gitignore
├── docker-compose.yml
├── docker-compose.prod.yml
├── README.md
├── project-spec.md
├── skills.md
├── start.md
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   ├── tests/
│   └── app/
│       ├── main.py
│       ├── api/
│       │   └── v1/
│       ├── core/
│       ├── db/
│       ├── models/
│       ├── schemas/
│       ├── services/
│       ├── repositories/
│       ├── security/
│       └── workers/
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── features/
│   │   ├── hooks/
│   │   ├── layouts/
│   │   ├── pages/
│   │   ├── routes/
│   │   ├── schemas/
│   │   └── types/
├── nginx/
│   ├── nginx.conf
│   └── conf.d/
├── n8n/
├── scripts/
└── volumes/
    ├── mariadb/
    ├── redis/
    ├── mongodb/
    ├── n8n/
    └── uploads/
```

---

## 20. Docker services

Suggested services:

```text
frontend
backend
mariadb
redis
mongodb
n8n
phpmyadmin
mongo-express
nginx
```

All container names must use:

```text
${PROJECT_PREFIX}_backend
${PROJECT_PREFIX}_frontend
${PROJECT_PREFIX}_mariadb
```

---

## 21. Environment variables

```dotenv
PROJECT_PREFIX=nutritrack
APP_NAME=NutriTrack AI
APP_ENV=development
APP_URL=http://localhost
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000

JWT_SECRET_KEY=change_me
JWT_ACCESS_TOKEN_MINUTES=15
JWT_REFRESH_TOKEN_DAYS=30

MARIADB_HOST=mariadb
MARIADB_PORT=3306
MARIADB_DATABASE=nutritrack
MARIADB_USER=nutritrack
MARIADB_PASSWORD=change_me
MARIADB_ROOT_PASSWORD=change_me

REDIS_URL=redis://redis:6379/0

MONGODB_URL=mongodb://mongodb:27017
MONGODB_DATABASE=nutritrack_ai_logs

OPENAI_API_KEY=
OPENAI_MODEL=
OPENAI_PROMPT_VERSION=v1

GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback

SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=
SMTP_FROM_NAME=NutriTrack AI

UPLOAD_DIR=/app/uploads
MAX_UPLOAD_MB=10

N8N_PORT=5679
PHPMYADMIN_PORT=8081
MONGO_EXPRESS_PORT=8082
```

Do not commit the real `.env`.

---

## 22. Testing requirements

### Backend tests

- Registration.
- Login.
- Refresh token.
- Google account linking.
- Password reset.
- Resource ownership.
- Image validation.
- AI response parsing.
- Meal confirmation.
- Daily summary calculation.
- Exercise calculation.
- Account deletion.

### Frontend tests

- Authentication forms.
- Photo upload.
- AI review screen.
- Editing detected food.
- Daily diary.
- Error states.
- Loading states.
- Mobile layout.

### Integration tests

- Complete registration and login.
- Google OAuth callback using mocks.
- Upload → AI analysis → review → confirmation.
- Add exercise → recalculate daily balance.
- Delete account and associated data.

---

## 23. Error handling

The API should use a consistent error structure:

```json
{
  "error": {
    "code": "AI_ANALYSIS_FAILED",
    "message": "The meal could not be analysed.",
    "details": null,
    "request_id": "uuid"
  }
}
```

Required error codes:

- `INVALID_CREDENTIALS`
- `EMAIL_ALREADY_EXISTS`
- `EMAIL_NOT_VERIFIED`
- `OAUTH_FAILED`
- `INVALID_IMAGE`
- `IMAGE_TOO_LARGE`
- `AI_ANALYSIS_FAILED`
- `AI_RESPONSE_INVALID`
- `RESOURCE_NOT_FOUND`
- `FORBIDDEN`
- `RATE_LIMITED`
- `VALIDATION_ERROR`

---

## 24. Logging and observability

- Structured JSON logs.
- Request ID.
- User ID when available.
- Endpoint latency.
- AI request latency.
- AI model used.
- Token usage.
- Estimated API cost.
- Error code.
- Never log credentials, JWTs or private image data.

Optional:

- Sentry.
- Prometheus.
- Grafana.

---

## 25. Minimum viable product

### Phase 1

- Docker Compose base.
- Email/password authentication.
- Google login.
- User profile and goals.
- Manual meal registration.
- Photo upload.
- OpenAI food detection.
- Review and confirmation.
- Exercise registration.
- Weight registration.
- Daily calorie balance.
- Basic weekly statistics.

### Phase 2

- Email verification.
- Password recovery.
- Improved nutritional database.
- Clarification questions.
- Image retention settings.
- CSV and JSON export.
- n8n weekly summaries.
- Admin usage dashboard.

### Phase 3

- Nutritionist role.
- Mobile PWA.
- Telegram integration.
- Barcode scanning.
- Integration with wearable devices.
- Subscription plans.
- Multi-language support.
- Food database integrations.

---

## 26. Definition of done for MVP

The MVP is complete when a user can:

1. Register with email and password.
2. Log in with Google.
3. Complete their profile.
4. Upload a meal photograph.
5. Receive structured AI estimates.
6. Correct the detected foods and quantities.
7. Confirm the meal.
8. Add a manual meal.
9. Add a Brooklyn Fitboxing session or other exercise.
10. Add body weight.
11. View the estimated daily deficit or surplus.
12. View weekly evolution.
13. Log out securely.
14. Delete their account and data.

---

## 27. Development rules

- Code, variables, functions, classes and filenames in English.
- User interface initially in Spanish.
- Avoid business logic inside route handlers.
- Use service and repository layers.
- Use migrations for every database change.
- Never calculate final totals only in the frontend.
- Store decimal nutritional values with suitable precision.
- Use UTC internally.
- Display dates in the user's timezone.
- All AI results must be editable.
- Every AI prompt must have a version.
- Avoid hardcoding models, secrets, ports or domains.
- Create small, reviewable commits.
- Keep README setup instructions updated.
- Add docstrings only where they add value.
- Prefer explicit types.
- Validate all external responses.
- Fail safely when OpenAI is unavailable.

---

## 28. Initial implementation order

1. Create repository and folder structure.
2. Add Docker Compose.
3. Configure MariaDB, Redis, frontend and backend.
4. Add health checks.
5. Create user and authentication models.
6. Implement email/password authentication.
7. Implement Google OAuth.
8. Build onboarding.
9. Create daily logs and meals.
10. Add manual food entry.
11. Add private image upload.
12. Integrate OpenAI image analysis.
13. Build AI review interface.
14. Add exercise and weight records.
15. Calculate daily summaries.
16. Build dashboard and weekly statistics.
17. Add tests.
18. Add privacy and account deletion.
19. Prepare production Nginx configuration.
20. Document deployment.

---

## 29. Important product warning

The application must display a visible disclaimer:

> Nutritional values, calorie expenditure and calorie balance are estimates. This application does not replace advice from a doctor or registered dietitian.

The application must not claim to diagnose, treat or prevent medical conditions.
