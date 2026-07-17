# NutriTrack AI

Base funcional y dockerizada de una aplicación web para el seguimiento de
alimentación, actividad y objetivos nutricionales. La implementación sigue
[`project-spec.md`](./project-spec.md) y avanza estrictamente por fases.

## Estado actual

La Fase 1 incluye:

- FastAPI con endpoints de vida y disponibilidad.
- React, TypeScript y Vite con una interfaz inicial en español.
- MariaDB y Redis con almacenamiento persistente local.
- Nginx como punto de entrada y reverse proxy.
- n8n preparado para automatizaciones futuras.
- phpMyAdmin para administrar MariaDB en desarrollo.
- Configuración centralizada mediante `.env` y health checks de los servicios.

Los modelos de datos, migraciones y usuarios pertenecen a la Fase 2 y no se han
adelantado en esta fase.

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
docker compose exec backend ruff check app tests
docker compose exec backend mypy app
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
