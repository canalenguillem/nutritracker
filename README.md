# NutriTrack AI

Base funcional y dockerizada de una aplicación web para el seguimiento de
alimentación, actividad y objetivos nutricionales. La implementación sigue
[`project-spec.md`](./project-spec.md) y avanza estrictamente por fases.

## Estado actual

La Fase 8 incluye, además de todo lo anterior:

- Registro de ejercicio con actividad, duración, intensidad, notas y hora.
- El gasto se estima a partir de la actividad, la intensidad, el tiempo y el
  peso corporal, y se guarda también la cifra que aporte la persona, que es la
  que cuenta para el día.
- Sin peso no se estima nada: el gasto depende del cuerpo que se mueve. El peso
  que se indique en una sesión se recuerda para las siguientes.
- El resumen del día muestra el ejercicio y la comida menos el ejercicio. No es
  un déficit: falta conocer el gasto en reposo, que llegará con el perfil.

La Fase 7 aportó los platos compuestos:

- Las estimaciones se acumulan: se describe un alimento tras otro y todos se
  suman al mismo plato, en vez de sustituirse.
- Buscador de comidas anteriores en la pantalla de alta, para repetir un plato
  habitual sin volver a describirlo ni pagar otra estimación.
- La búsqueda ofrece cada combinación de alimentos una sola vez, aunque se haya
  comido muchas veces.

La Fase 6 aportó la lectura de etiquetas:

- Junto a la descripción se puede adjuntar una foto de la tabla nutricional,
  que el modelo lee para afinar la estimación.
- Desde el móvil se puede hacer la foto en el momento o elegir una imagen ya
  guardada, con vista previa antes de enviarla.
- La foto se reduce en el navegador antes de subirla, de modo que una
  fotografía de móvil no choque con el límite de subida.
- Lo que se está escribiendo se conserva fuera de la página durante dos horas,
  porque el navegador del móvil suele descartarla mientras se usa la cámara.
  Se borra al guardar la comida y al cerrar sesión.
- La foto no se guarda: se envía al proveedor para leerla y se descarta.
- Se aceptan JPEG, PNG y WebP hasta `MAX_UPLOAD_MB`, comprobando el contenido
  del archivo y no su nombre ni el tipo declarado.
- Una estimación con foto no reutiliza la que se hizo solo con palabras.

La Fase 5 aportó la estimación escrita:

- Estimación de una comida a partir de una descripción escrita: «un café con
  nata» devuelve alimentos, cantidades y macronutrientes.
- Cada alimento llega con su nivel de confianza y con los supuestos que se han
  hecho, además de preguntas para afinar la estimación.
- Nada se guarda hasta que la persona revisa y confirma los valores.
- Los totales se suman en el servidor a partir de los alimentos, nunca se toman
  del modelo.

Para usar la estimación hay que definir `OPENAI_API_KEY` y `OPENAI_MODEL` en
`.env`. Sin esos valores el resto de la aplicación funciona con normalidad y el
formulario indica que el estimador no está disponible.

La Fase 4 aportó el registro de comidas:

- Registro manual de comidas con tantos alimentos como haga falta.
- Diario diario con el desglose de cada comida y los totales del día.
- Los totales se calculan siempre a partir de los alimentos; nunca se
  aceptan desde la petición.
- Cada comida se archiva en el día natural de la zona horaria de la cuenta,
  de forma que una cena pasada la medianoche no cae en la víspera.
- Consultas siempre limitadas a la persona propietaria: la comida de otra
  cuenta es indistinguible de una que no existe.

La Fase 3 aportó la autenticación:

- Registro e inicio de sesión con correo electrónico y contraseña.
- Contraseñas protegidas con Argon2 y tokens de acceso JWT de vida corta.
- Tokens de refresco opacos guardados como hash, rotados en cada uso y con
  detección de reutilización que revoca todas las sesiones del usuario.
- Inicio de sesión con Google mediante OAuth 2.0 y estado de un solo uso en
  Redis.
- Formularios de registro e inicio de sesión validados con Zod, y un panel
  privado accesible solo con sesión iniciada.

La Fase 2 aportó la base sobre la que se apoya:

- FastAPI con endpoints de vida y disponibilidad.
- React, TypeScript y Vite con una interfaz inicial en español.
- MariaDB y Redis con almacenamiento persistente local.
- Nginx como punto de entrada y reverse proxy.
- n8n preparado para automatizaciones futuras.
- phpMyAdmin para administrar MariaDB en desarrollo.
- Configuración centralizada mediante `.env` y health checks de los servicios.
- Persistencia asíncrona con SQLAlchemy 2 y MariaDB.
- Alembic con la migración inicial de usuarios, perfiles, identidades y tokens.
- Roles `user` y `admin`, repositorio y capa de servicio de usuarios.

El perfil de usuario y el archivo de fotografías junto a la comida
pertenecen a fases posteriores.

Para habilitar el acceso con Google se deben definir `GOOGLE_CLIENT_ID`,
`GOOGLE_CLIENT_SECRET` y `GOOGLE_REDIRECT_URI` en `.env`. Sin esos valores el
resto de la autenticación funciona con normalidad y el proveedor responde que
no está disponible.

## Requisitos

- Docker Engine con Docker Compose v2 o posterior.
- `curl` para ejecutar el script de comprobación desde el host.
- Puertos libres `80`, `3000`, `8000`, `5679` y `8081`, o valores alternativos
  configurados en `.env`.

No se necesita instalar Python, Node.js, MariaDB ni Redis en el host.

## Puesta en marcha

1. Crea la configuración local:

   ```bash
   cp .env.example .env
   ```

2. Sustituye en `.env` las contraseñas y claves marcadas como valores de
   reemplazo. En esta fase, OpenAI y Google OAuth pueden quedar vacíos.

3. Construye e inicia la aplicación:

   ```bash
   docker compose up --build -d
   ```

4. Comprueba el estado de los contenedores y los endpoints:

   ```bash
   docker compose ps
   ./scripts/check-health.sh
   ```

La primera construcción descarga las imágenes y dependencias, por lo que puede
tardar varios minutos.

## URLs de desarrollo

| Servicio | URL predeterminada |
| --- | --- |
| Aplicación mediante Nginx | <http://localhost> |
| Frontend Vite directo | <http://localhost:3000> |
| API y documentación | <http://localhost:8000/api/v1/docs> |
| Disponibilidad de la API | <http://localhost/api/v1/health/ready> |
| n8n | <http://localhost:5679> |
| phpMyAdmin | <http://localhost:8081> |

Para acceder a phpMyAdmin se utilizan `MARIADB_USER` y `MARIADB_PASSWORD`; el
servidor es `mariadb`.

## Comandos habituales

Ver logs agregados:

```bash
docker compose logs -f
```

Ver los logs de un único servicio:

```bash
docker compose logs -f backend
```

Ejecutar las comprobaciones del backend:

```bash
docker compose exec backend pytest
docker compose exec backend ruff check app tests alembic
docker compose exec backend mypy app
docker compose exec backend alembic current
docker compose exec backend alembic check
```

Comprobar y compilar el frontend:

```bash
docker compose exec frontend npm run typecheck
docker compose exec frontend npm run build
```

Detener los contenedores sin borrar los datos:

```bash
docker compose down
```

## Configuración

`.env.example` documenta todas las variables disponibles. `.env` contiene la
configuración local y está excluido de Git. Los nombres de contenedor y red usan
`PROJECT_PREFIX`; los puertos públicos, URLs, credenciales, proveedores externos
y límites también se configuran sin modificar código.

Los datos persistentes se guardan bajo `./volumes`:

```text
volumes/
├── mariadb/
├── n8n/
├── redis/
└── uploads/
```

MongoDB permanece desactivado porque la especificación lo define como opcional.

## Configuración de producción preliminar

El override construye imágenes sin montar el código fuente:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
```

Antes de utilizarlo fuera de un entorno local se deben definir secretos reales,
URLs públicas y políticas de despliegue. El endurecimiento completo de producción
forma parte de la Fase 10.

## Arquitectura de la Fase 1

```text
Browser
  └── Nginx (:80)
      ├── React/Vite (:5173 interno)
      └── FastAPI (:8000 interno)
          ├── MariaDB (:3306 interno)
          └── Redis (:6379 interno)

n8n (:5679) y phpMyAdmin (:8081) se publican como herramientas independientes.
```

El backend mantiene las rutas HTTP, servicios y repositorios separados. El
frontend centraliza el cliente HTTP, valida las respuestas externas y gestiona el
estado remoto con TanStack Query.

## Aviso

Los valores nutricionales, el gasto calórico y el balance de calorías son
estimaciones. Esta aplicación no sustituye el consejo de un médico o dietista-
nutricionista colegiado.
