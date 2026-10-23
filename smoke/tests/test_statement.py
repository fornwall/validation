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

"""Run the statement-level validation tests against a real driver."""

import pytest

import adbc_drivers_validation.tests.statement
from adbc_drivers_validation.tests.statement import (
    TestStatement,  # noqa: F401
)

from . import quirks


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    adbc_drivers_validation.tests.statement.generate_tests(
        [quirks.selected_quirks()], metafunc
    )
