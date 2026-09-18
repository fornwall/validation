# Copyright (c) 2026 ADBC Drivers Contributors
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

import typing
from unittest.mock import MagicMock

import adbc_driver_manager
import pyarrow
import pytest

from adbc_drivers_validation import model
from adbc_drivers_validation.tests import query as query_tests


@pytest.fixture
def driver() -> MagicMock:
    driver = MagicMock(spec=model.DriverQuirks)
    driver.name = "test"
    driver.short_version = "1"
    driver.features = model.DriverFeatures(statement_bind=True)
    driver.query_set = model.base_query_set()
    driver.bind_parameter.return_value = "?"
    return driver


@pytest.mark.parametrize(
    "test_name,option,defaults",
    [
        (
            "test_query_bind_stream",
            "bind_stream_queries",
            {"type/bind/string", "type/bind/large_string"},
        ),
        (
            "test_query_bind_dictionary",
            "bind_dictionary_queries",
            {"type/bind/string", "type/bind/large_string"},
        ),
    ],
)
@pytest.mark.parametrize("custom_queries", [False, True])
@pytest.mark.parametrize("bind_supported", [False, True])
def test_generate_bind_variants(
    driver: MagicMock,
    test_name: str,
    option: str,
    defaults: set[str],
    custom_queries: bool,
    bind_supported: bool,
) -> None:
    driver.features.statement_bind = bind_supported
    metafunc = MagicMock(spec=pytest.Metafunc)
    metafunc.definition = MagicMock()
    metafunc.definition.name = test_name
    metafunc.definition.iter_markers.return_value = []
    options = {}
    expected = defaults
    if custom_queries:
        # Even an explicit selection must exclude ingest and unbound queries.
        options[option] = {"type/bind/int32", "type/select/string", "ingest/string"}
        expected = {"type/bind/int32"}

    query_tests.generate_tests([driver], metafunc, **options)

    metafunc.parametrize.assert_called_once()
    args, kwargs = metafunc.parametrize.call_args
    assert args[0] == "driver,query"
    assert kwargs == {"scope": "module", "indirect": ["driver"]}
    params = args[1]
    assert {param.values[1].name for param in params} == expected
    for param in params:
        assert param.id == f"test:1:{param.values[1].name}"
        skip_reasons = [mark.kwargs["reason"] for mark in param.marks]
        assert skip_reasons == ([] if bind_supported else ["bind not supported"])


@pytest.mark.parametrize("mode", ["insert", "select"])
@pytest.mark.parametrize("fixture_setup", [False, True])
@pytest.mark.parametrize(
    "batch_size,empty_batches,batch_lengths",
    [
        (None, False, [5]),
        (1, False, [1, 1, 1, 1, 1]),
        (1, True, [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0]),
        (2, False, [2, 2, 1]),
        (2, True, [0, 2, 0, 2, 0, 1, 0]),
    ],
)
def test_bind_stream(
    driver: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    mode: typing.Literal["insert", "select"],
    fixture_setup: bool,
    batch_size: int | None,
    empty_batches: bool,
    batch_lengths: list[int],
) -> None:
    driver.features.statement_bind_test_mode = mode
    driver.features.select_fixture_setup = fixture_setup
    query = driver.query_set.queries["type/bind/string"]
    conn = MagicMock()
    statement = conn.cursor.return_value.__enter__.return_value.adbc_statement
    setup = MagicMock()
    monkeypatch.setattr(query_tests, "_setup_query", setup)
    bound = []

    def bind_stream(stream: pyarrow.RecordBatchReader) -> None:
        batches = list(stream)
        assert [batch.num_rows for batch in batches] == batch_lengths
        bound.append(pyarrow.Table.from_batches(batches, schema=stream.schema))

    def execute_query() -> tuple[adbc_driver_manager.ArrowArrayStreamHandle, int]:
        handle = adbc_driver_manager.ArrowArrayStreamHandle()
        bound[-1].to_reader()._export_to_c(handle.address)
        return handle, -1

    statement.bind_stream.side_effect = bind_stream
    statement.execute_query.side_effect = execute_query

    # Repeated runs must reset insert fixtures instead of relying on test order.
    for _ in range(2):
        query_tests.TestQuery().test_query_bind_stream(
            driver, conn, query, batch_size, empty_batches
        )

    assert statement.bind_stream.call_count == 2
    statement.bind.assert_not_called()
    assert statement.execute_query.call_count == 2
    assert statement.execute_update.call_count == (2 if mode == "insert" else 0)
    assert setup.call_count == (2 if mode == "insert" and fixture_setup else 0)
