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

"""Pytest configuration for the driver smoke tests."""

import importlib

import pytest

from adbc_drivers_validation import model
from adbc_drivers_validation.tests.conftest import (  # noqa: F401
    conn,
    conn_factory,
    db_kwargs,
    manual_test,
    noci,
    pytest_addoption,
    pytest_collection_modifyitems,
)

from . import quirks


@pytest.fixture(scope="session")
def driver(request: pytest.FixtureRequest) -> model.DriverQuirks:
    selected = quirks.selected_quirks()
    assert request.param == f"{selected.name}:{selected.short_version}"
    return selected


@pytest.fixture(scope="session")
def driver_path(driver: model.DriverQuirks) -> str:
    return importlib.import_module(driver.driver)._driver_path()
