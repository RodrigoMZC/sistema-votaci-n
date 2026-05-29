# Sistema de Votación para Equipos

Aplicación web desarrollada con Django 5 que permite a equipos crear y gestionar votaciones de tipo simple o ponderada.

---

## Requisitos previos

Antes de clonar el proyecto asegúrate de tener instalado:

- Python 3.12
- PostgreSQL
- Git

---

## Instalación

### 1. Crear y activar el entorno virtual

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Sabrás que está activo porque el prompt cambia a `(.venv)`.

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto (el compañero que hizo el setup te lo comparte por WhatsApp/Discord):

```
SECRET_KEY=django-insecure-cambia-esto
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

DB_NAME=voting_db
DB_USER=tu_usuario_postgres
DB_PASSWORD=tu_password_postgres
DB_HOST=localhost
DB_PORT=5432

EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_HOST_USER=correo@ejemplo.com
EMAIL_HOST_PASSWORD=api_key_de_brevo
```

### 4. Crear la base de datos en PostgreSQL

```bash
psql -U postgres
```

```sql
CREATE DATABASE voting_db;
\q
```

### 5. Aplicar migraciones

```bash
python manage.py migrate
```

### 6. Crear superusuario (opcional, para acceder al admin)

```bash
python manage.py createsuperuser
```

### 7. Levantar el servidor

```bash
python manage.py runserver
```

Abre tu navegador en [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## Estructura del proyecto

```
votaciones/
├── manage.py
├── .env                  ← NO está en Git, pedírselo al equipo
├── .gitignore
├── requirements.txt
├── voting_project/       ← configuración Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── accounts/             ← CustomUser + autenticación completa
├── teams/                ← CRUD de equipos y membresía
├── polls/                ← encuestas, votos y resultados
├── core/                 ← base.html, home, utilidades
├── static/               ← CSS y JS propios
├── media/                ← imágenes subidas (NO está en Git)
└── templates/
    ├── base.html
    ├── accounts/
    ├── teams/
    └── polls/
```

---

## Stack

| Tecnología | Versión | Uso |
|---|---|---|
| Django | 5.2.1 | Framework principal |
| PostgreSQL | — | Base de datos |
| Bootstrap | 5 | Estilos y componentes UI |
| Pillow | ≥10.0 | Manejo de imágenes |
| python-dotenv | ≥1.0 | Variables de entorno |
| psycopg2-binary | ≥2.9 | Adaptador PostgreSQL |

---

## Convenciones de Git

Trabajamos con una rama por persona. Nunca commitear directo a `main`.

```bash
# Al inicio del día, siempre actualizar main
git pull origin main

# Trabajar en tu rama
git checkout rama-persona-a   # o rama-persona-b / rama-persona-c
```

Formato de commits:

```
feat: agregar vista de votación
fix: validar votos duplicados
refactor: extraer lógica ponderada a services.py
test: prueba de cierre automático de encuesta
chore: actualizar requirements.txt
```

---

## Comandos útiles

```bash
# Verificar que el proyecto no tiene errores de configuración
python manage.py check

# Crear migraciones después de modificar un modelo
python manage.py makemigrations

# Aplicar migraciones pendientes
python manage.py migrate

# Correr las pruebas unitarias
python manage.py test

# Abrir la shell de Django
python manage.py shell
```

---
