import os
import shutil
from datetime import datetime

import click
from flask import current_app
from werkzeug.security import generate_password_hash

from models import User, db


@click.command("create-admin")
@click.option("--email", default=None, help="Email address for the new admin account")
def create_admin(email):
    """Create a new admin user interactively."""
    if email is None:
        email = click.prompt("Admin email", type=str)

    email = email.strip()
    if not email:
        raise click.ClickException("Email cannot be empty.")

    password = click.prompt("Password", hide_input=True, confirmation_prompt=False)
    if not password:
        raise click.ClickException("Password cannot be empty.")

    confirm_password = click.prompt("Confirm password", hide_input=True, confirmation_prompt=False)
    if password != confirm_password:
        raise click.ClickException("Passwords do not match.")

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        click.echo(f"A user with the email {email} already exists. No changes were made.")
        return

    new_user = User(
        email=email,
        password=generate_password_hash(password),
        role="admin",
        is_approved=True,
    )
    db.session.add(new_user)
    db.session.commit()
    click.echo(f"Admin account created successfully for {email}.")


@click.command("backup-db")
def backup_db():
    """Create a timestamped backup of the active SQLite database file."""
    source_path = os.path.join(current_app.instance_path, 'database.db')
    if not os.path.exists(source_path):
        raise click.ClickException(f"Database file not found: {source_path}")

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = os.path.join(current_app.instance_path, 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    backup_path = os.path.join(backup_dir, f'database_{timestamp}.db')
    shutil.copy2(source_path, backup_path)
    click.echo(f"Database backup created at {backup_path}")


def register_commands(app):
    app.cli.add_command(create_admin)
    app.cli.add_command(backup_db)
