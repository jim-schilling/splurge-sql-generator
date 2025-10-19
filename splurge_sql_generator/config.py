"""
Configuration management for splurge_sql_generator.

This module provides structured configuration with environment variable support.

Copyright (c) 2025, Jim Schilling

This module is licensed under the MIT License.
"""

import os
from dataclasses import dataclass

DOMAINS = ["config"]

# Environment variable prefix
_ENV_PREFIX = "SPLURGE_"


@dataclass
class GeneratorConfig:
    """Configuration for SQL code generator."""

    max_file_size_mb: int = 512
    """Maximum SQL file size in MB before chunked processing"""

    default_encoding: str = "utf-8"
    """Default text encoding for file operations"""

    sql_type_mapping_file: str = "types.yaml"
    """Path to SQL type mapping YAML file"""

    validate_parameters: bool = False
    """Whether to validate SQL parameters against schema"""

    strict_mode: bool = False
    """Whether to enforce strict validation on input"""

    @classmethod
    def from_env(cls) -> "GeneratorConfig":
        """
        Load configuration from environment variables.

        Environment variables (prefixed with SPLURGE_):
        - SPLURGE_MAX_FILE_SIZE_MB: Maximum file size in MB
        - SPLURGE_DEFAULT_ENCODING: Default text encoding
        - SPLURGE_SQL_TYPE_MAPPING_FILE: Path to types.yaml
        - SPLURGE_VALIDATE_PARAMETERS: Enable parameter validation (true/false)
        - SPLURGE_STRICT_MODE: Enable strict validation (true/false)

        Returns:
            GeneratorConfig instance with environment overrides applied
        """
        max_file_size_mb = int(os.getenv(f"{_ENV_PREFIX}MAX_FILE_SIZE_MB", "512"))
        default_encoding = os.getenv(f"{_ENV_PREFIX}DEFAULT_ENCODING", "utf-8")
        sql_type_mapping_file = os.getenv(f"{_ENV_PREFIX}SQL_TYPE_MAPPING_FILE", "types.yaml")
        validate_parameters = os.getenv(f"{_ENV_PREFIX}VALIDATE_PARAMETERS", "false").lower() == "true"
        strict_mode = os.getenv(f"{_ENV_PREFIX}STRICT_MODE", "false").lower() == "true"

        return cls(
            max_file_size_mb=max_file_size_mb,
            default_encoding=default_encoding,
            sql_type_mapping_file=sql_type_mapping_file,
            validate_parameters=validate_parameters,
            strict_mode=strict_mode,
        )

    def to_dict(self) -> dict[str, object]:
        """
        Convert configuration to dictionary.

        Returns:
            Dictionary representation of configuration
        """
        return {
            "max_file_size_mb": self.max_file_size_mb,
            "default_encoding": self.default_encoding,
            "sql_type_mapping_file": self.sql_type_mapping_file,
            "validate_parameters": self.validate_parameters,
            "strict_mode": self.strict_mode,
        }


# Global default configuration instance
DEFAULT_CONFIG = GeneratorConfig()
