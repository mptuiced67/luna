import os

import pytest
from click.testing import CliRunner

from luna.common.Neo4jConnection import Neo4jConnection
from luna.services.graph_service import update_graph


@pytest.fixture(autouse=True)
def spark(monkeypatch):
    print("------setup------")
    # setup env
    stream = os.popen("which python")
    pypath = stream.read().rstrip()
    monkeypatch.setenv("PYSPARK_PYTHON", pypath)

    yield

    print("------teardown------")


def test_cli_dicom_table(mocker):

    # mock graph connection
    mocker.patch.object(Neo4jConnection, "query")

    runner = CliRunner()
    result = runner.invoke(
        update_graph,
        [
            "-d",
            "tests/testdata/services/dicom-config.yaml",
            "-a",
            "tests/test_config.yml",
        ],
    )

    assert result.exit_code == 0


def test_cli_mha_table(mocker):

    # mock graph connection
    mocker.patch.object(Neo4jConnection, "query")

    runner = CliRunner()
    result = runner.invoke(
        update_graph,
        [
            "-d",
            "tests/testdata/services/mha-config.yaml",
            "-a",
            "tests/test_config.yml",
        ],
    )

    assert result.exit_code == 0


def test_cli_mhd_table(mocker):

    # mock graph connection
    mocker.patch.object(Neo4jConnection, "query")

    runner = CliRunner()
    result = runner.invoke(
        update_graph,
        [
            "-d",
            "tests/testdata/services/mhd-config.yaml",
            "-a",
            "tests/test_config.yml",
        ],
    )

    assert result.exit_code == 0


def test_cli_png_table(mocker):

    # mock graph connection
    mocker.patch.object(Neo4jConnection, "query")

    runner = CliRunner()
    result = runner.invoke(
        update_graph,
        [
            "-d",
            "tests/testdata/services/png-config.yaml",
            "-a",
            "tests/test_config.yml",
        ],
    )

    assert result.exit_code == 0


def test_cli_feature_table(mocker):

    # mock graph connection
    mocker.patch.object(Neo4jConnection, "query")

    runner = CliRunner()
    result = runner.invoke(
        update_graph,
        [
            "-d",
            "tests/testdata/services/feature-config.yaml",
            "-a",
            "tests/test_config.yml",
        ],
    )

    assert result.exit_code == 0


def test_cli_regional_bitmask_table(mocker):

    # mock graph connection
    mocker.patch.object(Neo4jConnection, "query")

    runner = CliRunner()
    result = runner.invoke(
        update_graph,
        [
            "-d",
            "tests/testdata/services/regional_bitmask-config.yaml",
            "-a",
            "tests/test_config.yml",
        ],
    )

    assert result.exit_code == 0


def test_cli_regional_geojson_table(mocker):

    # mock graph connection
    mocker.patch.object(Neo4jConnection, "query")

    runner = CliRunner()
    result = runner.invoke(
        update_graph,
        [
            "-d",
            "tests/testdata/services/regional_geojson-config.yaml",
            "-a",
            "tests/test_config.yml",
        ],
    )

    assert result.exit_code == 0


def test_cli_point_raw_json_table(mocker):

    # mock graph connection
    mocker.patch.object(Neo4jConnection, "query")

    runner = CliRunner()
    result = runner.invoke(
        update_graph,
        [
            "-d",
            "tests/testdata/services/point_json-config.yaml",
            "-a",
            "tests/test_config.yml",
        ],
    )

    assert result.exit_code == 0


def test_cli_point_geojson_table(mocker):

    # mock graph connection
    mocker.patch.object(Neo4jConnection, "query")

    runner = CliRunner()
    result = runner.invoke(
        update_graph,
        [
            "-d",
            "tests/testdata/services/point_geojson-config.yaml",
            "-a",
            "tests/test_config.yml",
        ],
    )

    assert result.exit_code == 0
