# Variables
COMPOSE=docker-compose

.PHONY: build up down logs restart migrate seed init-db shell clean run api

build:
	$(COMPOSE) build

# Levanta todo (DB + API) en segundo plano
up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

# Ver logs de la API
logs:
	$(COMPOSE) logs -f app

# Reiniciar solo el servicio de la API
restart:
	$(COMPOSE) restart app

# Ejecuta migraciones de Alembic
migrate:
	$(COMPOSE) exec app alembic upgrade head

# Inicializa base de datos y carga datos iniciales
init-db:
	$(COMPOSE) exec app python init_db.py
	$(COMPOSE) exec app python seed_initial_data.py

# Ejecutar el pipeline manual (Script original)
# Nota: --rm elimina el contenedor temporal al terminar
run:
	$(COMPOSE) run --rm app python src/main.py

# Levanta la API viendo los logs directamente en la terminal
api:
	$(COMPOSE) up app

# Limpiar archivos temporales y reportes
clean:
	rm -rf artifacts/*.pdf
	find . -type d -name "__pycache__" -exec rm -rf {} +

# Entrar al shell del contenedor para debuggear
shell:
	$(COMPOSE) exec app /bin/bash