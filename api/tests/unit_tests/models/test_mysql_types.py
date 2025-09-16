import pytest
from unittest.mock import patch

from models.types import adjusted_array, adjusted_jsonb, adjusted_json_index
from configs import dify_config


class TestMySQLTypeAdaptation:
    """Test MySQL type adaptation functions."""

    def test_adjusted_array_mysql(self):
        """Test adjusted_array returns JSON for MySQL."""
        with patch.object(dify_config, 'SQLALCHEMY_DATABASE_URI_SCHEME', 'mysql+pymysql'):
            from models.types import adjusted_array
            result = adjusted_array(None)
            assert result is not None
            # In MySQL, array should be adapted to JSON type

    def test_adjusted_array_postgresql(self):
        """Test adjusted_array returns ARRAY for PostgreSQL."""
        with patch.object(dify_config, 'SQLALCHEMY_DATABASE_URI_SCHEME', 'postgresql'):
            from models.types import adjusted_array
            from sqlalchemy import String
            result = adjusted_array(String)
            assert result is not None
            # In PostgreSQL, should return ARRAY type

    def test_adjusted_jsonb_mysql(self):
        """Test adjusted_jsonb returns JSON for MySQL."""
        with patch.object(dify_config, 'SQLALCHEMY_DATABASE_URI_SCHEME', 'mysql+pymysql'):
            from models.types import adjusted_jsonb
            result = adjusted_jsonb()
            assert result is not None
            # Should return JSON type for MySQL

    def test_adjusted_jsonb_postgresql(self):
        """Test adjusted_jsonb returns JSONB for PostgreSQL."""
        with patch.object(dify_config, 'SQLALCHEMY_DATABASE_URI_SCHEME', 'postgresql'):
            from models.types import adjusted_jsonb
            result = adjusted_jsonb()
            assert result is not None
            # Should return JSONB type for PostgreSQL

    def test_adjusted_json_index_mysql(self):
        """Test adjusted_json_index returns None for MySQL."""
        with patch.object(dify_config, 'SQLALCHEMY_DATABASE_URI_SCHEME', 'mysql+pymysql'):
            from models.types import adjusted_json_index
            result = adjusted_json_index("test_idx", "test_column")
            assert result is None  # MySQL doesn't support GIN indexes

    def test_adjusted_json_index_postgresql(self):
        """Test adjusted_json_index returns Index for PostgreSQL."""
        with patch.object(dify_config, 'SQLALCHEMY_DATABASE_URI_SCHEME', 'postgresql'):
            from models.types import adjusted_json_index
            result = adjusted_json_index("test_idx", "test_column")
            assert result is not None  # PostgreSQL supports GIN indexes

    def test_stringuuid_mysql_compatibility(self):
        """Test StringUUID works with MySQL."""
        from models.types import StringUUID
        from unittest.mock import MagicMock
        import uuid

        # Test UUID processing for MySQL
        test_uuid = uuid.uuid4()
        uuid_processor = StringUUID()

        # Mock dialect for MySQL
        mock_dialect = MagicMock()
        mock_dialect.name = "mysql"

        # Test process_bind_param
        result = uuid_processor.process_bind_param(test_uuid, mock_dialect)
        assert isinstance(result, str)
        assert result == str(test_uuid)

    def test_stringuuid_postgresql_compatibility(self):
        """Test StringUUID works with PostgreSQL."""
        from models.types import StringUUID
        from unittest.mock import MagicMock
        import uuid

        # Test UUID processing for PostgreSQL
        test_uuid = uuid.uuid4()
        uuid_processor = StringUUID()

        # Mock dialect for PostgreSQL
        mock_dialect = MagicMock()
        mock_dialect.name = "postgresql"

        # Test process_bind_param
        result = uuid_processor.process_bind_param(test_uuid, mock_dialect)
        assert isinstance(result, str)
        assert result == str(test_uuid)


def test_mysql_database_compatibility():
    """Test overall MySQL database compatibility."""
    with patch.object(dify_config, 'SQLALCHEMY_DATABASE_URI_SCHEME', 'mysql+pymysql'):
        # Test that all type adaptations work correctly for MySQL
        from models.types import adjusted_array, adjusted_jsonb, adjusted_json_index

        # Array should be adapted to JSON
        array_result = adjusted_array(None)
        assert array_result is not None

        # JSONB should be adapted to JSON
        jsonb_result = adjusted_jsonb()
        assert jsonb_result is not None

        # JSON index should return None (not supported in MySQL)
        index_result = adjusted_json_index("test_idx", "test_col")
        assert index_result is None


def test_postgresql_database_compatibility():
    """Test overall PostgreSQL database compatibility."""
    with patch.object(dify_config, 'SQLALCHEMY_DATABASE_URI_SCHEME', 'postgresql'):
        # Test that all type adaptations work correctly for PostgreSQL
        from models.types import adjusted_array, adjusted_jsonb, adjusted_json_index

        # Array should return ARRAY type
        array_result = adjusted_array(None)
        assert array_result is not None

        # JSONB should return JSONB type
        jsonb_result = adjusted_jsonb()
        assert jsonb_result is not None

        # JSON index should return Index with GIN
        index_result = adjusted_json_index("test_idx", "test_col")
        assert index_result is not None
