from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
import os
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool
import sqlalchemy as sa
from alembic import context
load_dotenv()
db_url = os.getenv("DATABASE_URL")

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = None

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Modo Online: Inyecta la URL del .env dinámicamente."""
    
    # 2. Obtenemos la sección de configuración del .ini
    configuration = config.get_section(config.config_ini_section)
    
    # 3. SOBRESCRIBIMOS la URL con la del .env (esto elimina el error de 'driver')
    if not db_url:
        raise ValueError("❌ No se encontró DATABASE_URL en el archivo .env")
    
    configuration["sqlalchemy.url"] = db_url

    # 4. Creamos el motor con la configuración inyectada
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # Forzamos el search_path para ver todos los esquemas
        connection.execute(sa.text("set search_path to public, operational, raw_vision, raw_voice, audit, cleansed, artifacts, logs"))
        connection.commit()

        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            include_schemas=True,
            version_table_schema='public',
            include_object=include_object
        )

        with context.begin_transaction():
            # Crear esquemas si no existen antes de aplicar tablas
            schemas = ['operational', 'raw_vision', 'raw_voice', 'audit', 'cleansed', 'artifacts', 'logs']
            for schema in schemas:
                connection.execute(sa.text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
            
            context.run_migrations()