# Copyright (c) 2025-2026 ADBC Drivers Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Minimal driver quirks for the CI smoke tests.

These quirks are intentionally small: they define only what is needed to
run the statement-level validation tests against real, released drivers.
They are not shipped as part of the package.
"""

import os
import re
from pathlib import Path

from adbc_drivers_validation import model

_QUERIES_PATH = Path(__file__).parent.parent / "queries"


class SQLiteQuirks(model.DriverQuirks):
    name = "sqlite"
    driver = "adbc_driver_sqlite"
    driver_name = "ADBC SQLite Driver"
    vendor_name = "SQLite"
    vendor_version = "3"
    short_version = "3"
    features = model.DriverFeatures(
        connection_transactions=True,
        statement_bind=True,
        # The released driver raises NOT_IMPLEMENTED for execute_schema.
        statement_execute_schema=False,
        statement_get_parameter_schema=True,
        statement_prepare=True,
        statement_rows_affected=True,
        statement_rows_affected_ddl=True,
    )
    setup = model.DriverSetup(
        database={"uri": model.FromEnv("ADBC_SQLITE_TEST_URI")},
        connection={},
        statement={},
    )

    @property
    def queries_paths(self) -> tuple[Path]:
        return (_QUERIES_PATH,)

    def is_table_not_found(self, table_name: str | None, error: Exception) -> bool:
        return "no such table" in str(error).lower()


class PostgreSQLQuirks(model.DriverQuirks):
    name = "postgresql"
    driver = "adbc_driver_postgresql"
    driver_name = "ADBC PostgreSQL Driver"
    vendor_name = "PostgreSQL"
    vendor_version = re.compile(r"18[0-9]{4}")
    short_version = "18"
    features = model.DriverFeatures(
        connection_transactions=True,
        statement_bind=True,
        statement_execute_schema=True,
        statement_get_parameter_schema=True,
        statement_prepare=True,
        statement_rows_affected=True,
        statement_rows_affected_ddl=False,
    )
    setup = model.DriverSetup(
        database={"uri": model.FromEnv("ADBC_POSTGRESQL_TEST_URI")},
        connection={},
        statement={},
    )

    @property
    def queries_paths(self) -> tuple[Path]:
        return (_QUERIES_PATH,)

    def bind_parameter(self, index: int) -> str:
        """PostgreSQL uses $1, $2, $3, etc. for parameter placeholders."""
        return f"${index}"

    def is_table_not_found(self, table_name: str | None, error: Exception) -> bool:
        message = str(error).lower()
        if table_name is not None and table_name.lower() not in message:
            return False
        return "does not exist" in message or "undefined_table" in message


def selected_quirks() -> model.DriverQuirks:
    """Return the quirks selected by the SMOKE_DRIVER environment variable."""
    name = os.environ.get("SMOKE_DRIVER", "sqlite")
    if name == "sqlite":
        return SQLiteQuirks()
    elif name == "postgresql":
        return PostgreSQLQuirks()
    raise ValueError(f"Unknown SMOKE_DRIVER: {name!r}")
