from __future__ import with_statement
import os, sys
from alembic import context
from sqlalchemy import engine_from_config, pool
from logging.config import fileConfig

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import create_app, db
from app import models  # noqa

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

app = create_app()
target_metadata = db.metadata

def get_url():
    return app.config["SQLALCHEMY_DATABASE_URI"]

def run_migrations_offline():
    context.configure(url=get_url(), target_metadata=target_metadata, literal_binds=True, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config({"sqlalchemy.url": get_url()}, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
