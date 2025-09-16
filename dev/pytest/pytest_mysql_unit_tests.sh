#!/bin/bash
set -x

SCRIPT_DIR="$(dirname "$(realpath "$0")")"
cd "$SCRIPT_DIR/../.."

# Run MySQL-specific unit tests
echo "Running MySQL configuration tests..."
pytest api/tests/unit_tests/configs/test_dify_config.py::test_mysql_config -v
pytest api/tests/unit_tests/configs/test_dify_config.py::test_mysql_engine_options -v
pytest api/tests/unit_tests/configs/test_dify_config.py::test_mysql_flask_config -v
pytest api/tests/unit_tests/configs/test_dify_config.py::test_mysql_db_extras_options -v
pytest api/tests/unit_tests/configs/test_dify_config.py::test_mysql_oceanbase_config -v

echo "Running MySQL type adaptation tests..."
pytest api/tests/unit_tests/models/test_mysql_types.py -v

echo "Running MySQL migration tests..."
pytest api/tests/unit_tests/test_mysql_migration.py -v
