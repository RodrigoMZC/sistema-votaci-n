# 🗳️ Sistema de Votación para Equipos

Aplicación web desarrollada con **Django 5** que permite a equipos crear y gestionar votaciones de tipo simple o ponderada, con fecha límite y número de votos requeridos para cierre automático.

---

## 📋 Tabla de contenidos

- [Stack y tecnologías](#stack-y-tecnologías)
- [Configuración del entorno](#configuración-del-entorno)
- [Modelos de base de datos](#modelos-de-base-de-datos)
- [Vistas, URLs y plantillas](#vistas-urls-y-plantillas)
- [Autenticación](#autenticación)
- [CRUD del recurso principal](#crud-del-recurso-principal)
- [Funcionalidad extra](#funcionalidad-extra)
- [Pruebas unitarias](#pruebas-unitarias)
- [Docker](#docker)
- [Despliegue en OCI](#despliegue-en-oci)
- [Credenciales de prueba](#credenciales-de-prueba)
- [Variables de entorno](#variables-de-entorno)
- [Capturas de pantalla](#capturas-de-pantalla)

---

## Stack y tecnologías

| Tecnología | Versión | Uso |
|---|---|---|
| Python | 3.12 | Lenguaje principal |
| Django | 5.2.1 | Framework web |
| PostgreSQL | 16 | Base de datos |
| Bootstrap | 5.3 | Estilos y UI |
| Gunicorn | 23.0.0 | Servidor WSGI en producción |
| Nginx | alpine | Reverse proxy |
| Docker | — | Contenedores |
| Brevo | — | SMTP para correos transaccionales |

---

## Configuración del entorno

### Requisitos previos

- Python 3.12+
- PostgreSQL
- Git

### Instalación local

```bash
# 1. Clonar el repositorio
git clone https://github.com/RodrigoMZC/sistema-votaci-n.git
cd sistema-votaci-n

# 2. Crear y activar el entorno virtual
python3 -m venv .venv
source .venv/bin/activate        # Linux/Mac
# .venv\Scripts\activate         # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Crear el archivo .env (ver sección Variables de entorno)
cp .env.example .env
# Editar .env con los valores reales

# 5. Crear la base de datos en PostgreSQL
psql -U postgres -c "CREATE DATABASE voting_db;"

# 6. Aplicar migraciones
python manage.py migrate

# 7. Cargar usuarios de prueba
python manage.py seed

# 8. Levantar el servidor
python manage.py runserver
```

Abrir [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## Modelos de base de datos

### CustomUser — `accounts/models.py`

Extiende `AbstractUser` con campos adicionales. Configurado con `AUTH_USER_MODEL = 'accounts.CustomUser'` en `settings.py`.

```python
class CustomUser(AbstractUser):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    avatar     = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio        = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username

    def get_absolute_url(self):
        return reverse('accounts:profile')
```

### Team y TeamMember — `teams/models.py`

```python
class Team(models.Model):
    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name            = models.CharField(max_length=100, unique=True)
    slug            = models.SlugField(unique=True, blank=True)
    logo            = models.ImageField(upload_to='logos/', blank=True, null=True)
    description     = models.TextField(blank=True)
    primary_color   = models.CharField(max_length=7, default='#E8192C')
    secondary_color = models.CharField(max_length=7, default='#1a1a2e')
    created_by      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at      = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('teams:detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class TeamMember(models.Model):
    ROLE_CHOICES = [('admin', 'Administrador'), ('member', 'Miembro')]
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team       = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='members')
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role       = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    joined_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('team', 'user')

    def __str__(self):
        return f"{self.user} - {self.team} ({self.role})"
```

### Poll, Option y Vote — `polls/models.py` (recurso principal)

```python
class Poll(models.Model):
    TYPE_CHOICES    = [('simple', 'Simple'), ('weighted', 'Ponderada')]
    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title           = models.CharField(max_length=200)
    description     = models.TextField(blank=True)
    type            = models.CharField(max_length=10, choices=TYPE_CHOICES, default='simple')
    required_votes  = models.PositiveIntegerField(default=0, help_text="0 = sin mínimo")
    deadline        = models.DateTimeField(null=True, blank=True)
    team            = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='polls')
    created_by      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    is_active       = models.BooleanField(default=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('polls:detail', kwargs={
            'team_slug': self.team.slug,
            'poll_id': self.id,
        })

    def check_and_close(self):
        total = Vote.objects.filter(option__poll=self).count()
        if (self.required_votes and total >= self.required_votes) or \
           (self.deadline and timezone.now() >= self.deadline):
            self.is_active = False
            self.save()


class Option(models.Model):
    id     = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    poll   = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='options')
    text   = models.CharField(max_length=200)
    image  = models.ImageField(upload_to='options/', blank=True, null=True)
    weight = models.FloatField(default=1.0, help_text="Solo aplica en votación ponderada")

    def __str__(self):
        return f"{self.poll} — {self.text}"


class Vote(models.Model):
    id       = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    option   = models.ForeignKey(Option, on_delete=models.CASCADE, related_name='votes')
    voted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('user', 'option')]

    def __str__(self):
        return f"{self.user} → {self.option}"
```

### Diagrama de relaciones

```
CustomUser
    │
    ├──< TeamMember >── Team ──< Poll ──< Option ──< Vote
    │                                                  │
    └──────────────────────────────────────────────────┘
```

Todos los modelos usan **UUID** como clave primaria.

---

## Vistas, URLs y plantillas

### Patrón de vistas

Se usan **Class-Based Views (CBV)** de forma consistente:

- `LoginRequiredMixin` — protege todas las vistas que requieren sesión
- `UserPassesTestMixin` — restringe edición/eliminación a admins del equipo
- `TemplateView`, `ListView`, `DetailView`, `CreateView`, `UpdateView`, `DeleteView`

### URLs principales — `votaciones/urls.py`

```python
urlpatterns = [
    path('admin/',    admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('teams/',    include('teams.urls')),
    path('polls/',    include('polls.urls')),
    path('',          include('core.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### URLs por app

**accounts** (`/accounts/`)

| URL | Vista |
|---|---|
| `login/` | `LoginView` |
| `logout/` | `LogoutView` |
| `register/` | `RegisterView` |
| `profile/` | `ProfileView` |
| `password-change/` | `PasswordChangeView` |
| `password-reset/` | `PasswordResetView` |
| `password-reset/done/` | `PasswordResetDoneView` |
| `password-reset/<uid>/<token>/` | `PasswordResetConfirmView` |
| `password-reset/complete/` | `PasswordResetCompleteView` |

**teams** (`/teams/`)

| URL | Vista |
|---|---|
| `` | `TeamListView` |
| `create/` | `TeamCreateView` |
| `<slug>/` | `TeamDetailView` |
| `<slug>/edit/` | `TeamUpdateView` |
| `<slug>/delete/` | `TeamDeleteView` |
| `<slug>/members/add/` | `AddMemberView` |
| `members/<uuid>/remove/` | `RemoveMemberView` |

**polls** (`/polls/`)

| URL | Vista |
|---|---|
| `` | `MyPollsView` — todas las votaciones del usuario agrupadas por equipo |
| `mis-votos/` | `MyVotesView` — historial de votos emitidos |
| `team/<slug>/` | `PollListView` — votaciones de un equipo específico |
| `team/<slug>/create/` | `PollCreateView` |
| `team/<slug>/<uuid>/` | `PollDetailView` |
| `team/<slug>/<uuid>/vote/` | `PollVoteView` |
| `team/<slug>/<uuid>/results/` | `PollResultsView` |

### Herencia de plantillas

```
templates/
├── base.html                        ← navbar, Bootstrap 5, mensajes flash, footer
├── core/
│   └── home.html
├── accounts/
│   ├── login.html
│   ├── register.html
│   ├── profile.html
│   ├── password_change.html
│   ├── password_change_done.html
│   ├── password_reset.html
│   ├── password_reset_done.html
│   ├── password_reset_confirm.html
│   ├── password_reset_complete.html
│   └── emails/
│       └── password_reset_email.html
├── teams/
│   ├── team_list.html
│   ├── team_detail.html
│   ├── team_form.html               ← crear y editar
│   ├── team_confirm_delete.html
│   ├── add_member.html
│   └── remove_member.html
└── polls/
    ├── my_polls.html                ← vista global de todas las votaciones
    ├── my_votes.html                ← historial de votos del usuario
    ├── poll_list.html               ← votaciones de un equipo
    ├── poll_detail.html             ← detalle + formulario de voto
    ├── poll_create.html             ← formulario de creación
    └── poll_results.html            ← resultados con barras de progreso
```

`base.html` define los bloques: `title`, `content`, `extra_css`, `extra_js`. Bootstrap 5 se carga vía CDN.

---

## Autenticación

Implementada en la app `accounts` usando las vistas integradas de Django con plantillas personalizadas:

| Funcionalidad | URL | Vista |
|---|---|---|
| Registro | `/accounts/register/` | `RegisterView` (CBV) |
| Inicio de sesión | `/accounts/login/` | `LoginView` (Django) |
| Cierre de sesión | `/accounts/logout/` | `LogoutView` (Django) |
| Perfil y edición | `/accounts/profile/` | `ProfileView` (CBV) |
| Cambio de contraseña | `/accounts/password-change/` | `PasswordChangeView` (Django) |
| Reset por correo | `/accounts/password-reset/` | `PasswordResetView` (Django) |

El correo de restablecimiento se envía vía **Brevo SMTP** con plantilla personalizada en `accounts/emails/password_reset_email.html`.

Configuración en `settings.py`:

```python
LOGIN_URL             = '/accounts/login/'
LOGIN_REDIRECT_URL    = '/'
LOGOUT_REDIRECT_URL   = '/accounts/login/'
AUTH_USER_MODEL       = 'accounts.CustomUser'
DEFAULT_FROM_EMAIL    = os.getenv('DEFAULT_FROM_EMAIL')
```

---

## CRUD del recurso principal

### Encuestas (Poll)

Las votaciones son el recurso principal del proyecto. El CRUD está implementado con CBV y permisos por rol:

| Operación | URL | Permiso requerido |
|---|---|---|
| **Listar** (global) | `/polls/` | Sesión iniciada |
| **Listar** (por equipo) | `/polls/team/<slug>/` | Miembro del equipo |
| **Crear** | `/polls/team/<slug>/create/` | Admin del equipo |
| **Detalle + votar** | `/polls/team/<slug>/<uuid>/` | Miembro del equipo |
| **Resultados** | `/polls/team/<slug>/<uuid>/results/` | Miembro del equipo |

La **creación** incluye:
- Título y descripción
- Tipo: simple o ponderada (con pesos por opción)
- Fecha límite (`deadline`) opcional
- Número de votos para cierre automático (`required_votes`) opcional
- Mínimo 2 opciones, con imagen opcional por opción

El **voto** aplica las siguientes validaciones antes de registrar:
- La encuesta debe estar activa (`is_active=True`)
- El usuario no debe haber votado ya en esa encuesta
- La fecha límite no debe haber vencido

Después de cada voto se invoca `poll.check_and_close()` que cierra la encuesta automáticamente si se cumplen las condiciones.

---

## Funcionalidad extra

### 1. Votación simple vs ponderada

- **Simple:** cada voto vale 1. Gana la opción con más votos directos.
- **Ponderada:** cada opción tiene un `weight` configurable. El resultado refleja la suma ponderada de votos.

### 2. Cierre automático de encuesta

`check_and_close()` se ejecuta tras cada voto y cierra la encuesta si:
- Se alcanzó el número de `required_votes`, **o**
- Se venció la `deadline`

### 3. Restricción de voto único

`unique_together = ('user', 'option')` en el modelo `Vote` + validación en la vista garantizan que ningún usuario vote dos veces en la misma encuesta.

### 4. Colores personalizados por equipo

Cada equipo elige un color primario y secundario mediante `<input type="color">`. Estos colores se aplican dinámicamente en los gradientes de los headers, botones y barras de resultados de todas las vistas de ese equipo.

### 5. Vista global de votaciones

`/polls/` agrega todas las votaciones de todos los equipos del usuario con filtros **Todas / Activas / Cerradas** y muestra si el usuario ya votó o tiene voto pendiente.

### 6. Historial de votos

`/polls/mis-votos/` muestra todas las opciones elegidas por el usuario con fecha, equipo y acceso directo a resultados.

---

## Pruebas unitarias

```bash
python manage.py test
```

Las pruebas cubren los flujos más críticos del sistema:

| App | Archivo | Qué prueba |
|---|---|---|
| `accounts` | `accounts/tests.py` | Registro, login, reset de contraseña |
| `teams` | `teams/tests.py` | Creación de equipo, permisos de rol |
| `polls` | `polls/tests.py` | Creación de votación, voto, cierre automático |

> Las pruebas de correo usan `django.core.mail.backends.locmem.EmailBackend` — ningún correo real se envía.

---

## Docker

El proyecto corre completamente en Docker con tres contenedores orquestados por `docker-compose.yml`.

### Contenedores

| Contenedor | Imagen | Puerto externo |
|---|---|---|
| `nginx` | nginx:alpine | 80 |
| `web` | python:3.12-slim | interno (8000) |
| `db` | postgres:16-alpine | interno (5432) |

### Archivos

```
votaciones/
├── dockerfile
├── docker-compose.yml
└── nginx/
    └── nginx.conf
```

### Levantar con Docker

```bash
# 1. Crear el .env de producción
cp .env.example .env
# Editar con los valores reales (DEBUG=False, DB_HOST=db)

# 2. Construir e iniciar
docker compose up --build -d

# 3. Verificar que los 3 contenedores estén activos
docker compose ps

# 4. Cargar usuarios de prueba
docker compose exec web python manage.py seed

# 5. Ver logs
docker compose logs -f web
```

### Detener

```bash
docker compose down
```

> Los datos de PostgreSQL persisten en el volumen `postgres_data`.

---

## Despliegue en OCI

### Arquitectura

```
Internet → Puerto 80 → Nginx → Gunicorn/Django
                             ↘ PostgreSQL
```

### Pasos resumidos

```bash
# 1. Conectarse a la instancia OCI
ssh ubuntu@<IP_PUBLICA>

# 2. Instalar Docker
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-plugin
sudo usermod -aG docker $USER && newgrp docker

# 3. Clonar el repositorio
git clone https://github.com/RodrigoMZC/sistema-votaci-n.git
cd sistema-votaci-n

# 4. Crear el .env de producción
cp .env.example .env
nano .env
# Ajustar: DEBUG=False, ALLOWED_HOSTS=<IP_PUBLICA>, DB_HOST=db

# 5. Levantar los contenedores
docker compose up --build -d

# 6. Cargar datos de prueba
docker compose exec web python manage.py seed
```

### Requisitos en OCI

- Puerto **80** abierto en el Security Group (Ingress → TCP → 0.0.0.0/0)
- `DEBUG=False` en el `.env` del servidor
- `ALLOWED_HOSTS` con la IP pública de OCI
- `DB_HOST=db` (nombre del servicio en docker-compose, no `localhost`)

### URL pública

```
http://<IP_PUBLICA>
```

> Completar con la IP asignada tras el despliegue.

---

## Credenciales de prueba

Generadas con `python manage.py seed` (o `docker compose exec web python manage.py seed`):

| Rol | Usuario | Contraseña |
|---|---|---|
| Superusuario | `admin` | `Admin1234!` |
| Usuario normal | `usuario` | `Usuario1234!` |

Panel de administración: `http://<IP>/admin/`

---

## Variables de entorno

Crear `.env` a partir de `.env.example`:

```bash
cp .env.example .env
```

Contenido de `.env.example`:

```bash
# Django
SECRET_KEY=coloca-aqui-una-clave-secreta-larga-y-aleatoria
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# Base de datos PostgreSQL
DB_NAME=voting_db
DB_USER=tu_usuario_postgres
DB_PASSWORD=tu_password_postgres
DB_HOST=localhost
DB_PORT=5432

# Correo SMTP (Brevo)
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_HOST_USER=tu_correo@ejemplo.com
EMAIL_HOST_PASSWORD=tu_api_key_brevo
DEFAULT_FROM_EMAIL=tu_correo@ejemplo.com
```

> **En producción:** `DEBUG=False`, `DB_HOST=db`, IP pública en `ALLOWED_HOSTS`.

---

## Equipo de desarrollo

| Persona | GitHub |
|---|---|
| Rodrigo Mazuca | [@RodrigoMZC](https://github.com/RodrigoMZC) |
| Paloma Fernandez | [@Pal0mafdz](https://github.com/Pal0mafdz) |
| Xavier Sotomayor | [@XavierSs21](https://github.com/XavierSs21) |

---
