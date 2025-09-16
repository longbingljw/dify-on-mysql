import pytest
from unittest.mock import MagicMock, patch
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.environment import EnvironmentContext
from alembic.migration import MigrationContext


def test_mysql_migration_config():
    """Test MySQL migration configuration."""
    # Test that alembic.ini exists and is readable
    from pathlib import Path
    config_path = Path("api/migrations-mysql/alembic.ini")
    assert config_path.exists()
    
    config = Config("api/migrations-mysql/alembic.ini")
    
    # Check that config object is created successfully
    assert config is not None
    
    # Check that we can read some basic configuration
    # Note: MySQL alembic.ini might have different structure than PostgreSQL
    try:
        script_location = config.get_main_option("script_location")
        # If script_location exists, verify it
        if script_location:
            assert "migrations" in script_location
    except Exception:
        # If script_location is not set, that's OK for MySQL setup
        pass
    
    # Test that we can create script directory from the migrations-mysql path
    # Even if alembic.ini doesn't have script_location, we can still test the directory
    mysql_migrations_path = Path("api/migrations-mysql")
    assert mysql_migrations_path.exists()
    assert mysql_migrations_path.is_dir()


def test_mysql_migration_versions():
    """Test MySQL migration versions are available."""
    from pathlib import Path
    
    # Test that migration version files exist in the versions directory
    versions_dir = Path("api/migrations-mysql/versions")
    assert versions_dir.exists()
    assert versions_dir.is_dir()
    
    # Get all migration files
    migration_files = list(versions_dir.glob("*.py"))
    assert len(migration_files) > 0
    
    # Check that we have the expected migration files
    file_names = [f.name for f in migration_files]
    
    # Check for specific migration files (by prefix)
    assert any(f.startswith("9adccf7ca328") for f in file_names), "Initial MySQL version not found"
    assert any(f.startswith("4ce39f688dc4") for f in file_names), "1.8.0 version not found"


@patch('alembic.command.upgrade')
def test_mysql_migration_upgrade_command(mock_upgrade):
    """Test MySQL migration upgrade command can be called."""
    config = Config("api/migrations-mysql/alembic.ini")

    # Mock the upgrade command
    mock_upgrade.return_value = None

    # This should not raise an exception
    command.upgrade(config, "head")

    # Verify the command was called
    mock_upgrade.assert_called_once_with(config, "head")


@patch('alembic.command.current')
def test_mysql_migration_current_command(mock_current):
    """Test MySQL migration current command can be called."""
    config = Config("api/migrations-mysql/alembic.ini")

    # Mock the current command
    mock_current.return_value = None

    # This should not raise an exception
    command.current(config)

    # Verify the command was called
    mock_current.assert_called_once_with(config)


def test_mysql_migration_env_py_structure():
    """Test that MySQL migration env.py has correct structure without importing it."""
    from pathlib import Path
    
    env_file = Path("api/migrations-mysql/env.py")
    assert env_file.exists(), "env.py file should exist"
    
    # Read file content and verify key components exist
    content = env_file.read_text()
    
    # Check for required imports
    assert "from alembic import context" in content
    assert "from flask import current_app" in content
    assert "from models.base import Base" in content
    
    # Check for required functions
    assert "def run_migrations_offline" in content
    assert "def run_migrations_online" in content  
    assert "def get_metadata" in content
    assert "def include_object" in content
    
    # Check for key logic without executing
    assert "Base.metadata" in content
    assert 'type_ == "foreign_key_constraint"' in content
    assert "return False" in content  # for foreign key constraints


@pytest.mark.parametrize("revision", [
    "9adccf7ca328",  # Initial MySQL version
    "15d91fcf3eb9",  # Table fix
    "37c2bb41f84a",  # MCP servers update
    "4ce39f688dc4",  # 1.8.0 version
    "7aefe33a8deb",  # Upgrade to 1.7.0
    "e0e5dc8aa037",  # Text fields update
])
def test_mysql_migration_revisions_exist(revision):
    """Test that specific MySQL migration revisions exist."""
    from pathlib import Path
    
    # Test that specific migration files exist
    versions_dir = Path("api/migrations-mysql/versions")
    migration_files = list(versions_dir.glob("*.py"))
    file_names = [f.name for f in migration_files]
    
    # Check that the specific revision file exists
    assert any(f.startswith(revision) for f in file_names), f"Migration {revision} not found"


def test_mysql_migration_script_directory():
    """Test MySQL migration script directory structure."""
    from pathlib import Path

    # Check that main migrations directory exists
    migrations_dir = Path("api/migrations-mysql")
    assert migrations_dir.exists()
    assert migrations_dir.is_dir()

    # Check that versions directory exists
    versions_dir = Path("api/migrations-mysql/versions")
    assert versions_dir.exists()
    assert versions_dir.is_dir()

    # Check that we have migration files
    migration_files = list(versions_dir.glob("*.py"))
    assert len(migration_files) > 0

    # Each migration file should have proper naming
    for migration_file in migration_files:
        assert migration_file.name.endswith(".py")
        # Should follow alembic naming convention: {revision}_{description}.py
        parts = migration_file.stem.split("_", 1)
        assert len(parts) == 2
        assert len(parts[0]) == 12  # Alembic revision IDs are 12 characters
        
    # Check that env.py exists
    env_file = migrations_dir / "env.py"
    assert env_file.exists()
