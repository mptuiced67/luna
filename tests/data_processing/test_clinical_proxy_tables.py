'''
Created on September 11, 2020

@author: pashaa@mskcc.org
'''
import os, shutil, sys
import pytest
from click.testing import CliRunner

from data_processing.common.config import ConfigSet

sys.path.insert(0, os.path.abspath( os.path.join(os.path.dirname(__file__), '../src/') ))

from data_processing.clinical_proxy_tables import generate_proxy_table, cli
from data_processing.common.sparksession import SparkConfig

source_file = 'tests/data_processing/testdata/data/test_clinical_patients.tsv'
source_file_err = 'tests/data_processing/testdata/data/test_clinical_patients_error.tsv'
destination_dir = 'tests/data_processing/testdata/data/tables/test-patients'


@pytest.fixture(autouse=True)
def spark():
    print('------setup------')
    APP_CFG = 'APP_CFG'
    ConfigSet(name=APP_CFG, config_file='tests/test_config.yaml')
    spark = SparkConfig().spark_session(config_name=APP_CFG, app_name='test-clinical-proxy-preprocessing')

    yield spark

    print('------teardown------')
    clinical_proxy_table = os.path.join(destination_dir)
    if os.path.exists(clinical_proxy_table):
        shutil.rmtree(clinical_proxy_table)


def test_generate_proxy_table(spark):
    generate_proxy_table(source_file, destination_dir, spark)

    df = spark.read.format('delta').load(destination_dir)
    assert df.count() == 3
    df.unpersist()

def test_generate_proxy_table_error(spark):
    with pytest.raises(Exception, match=r'Make sure input file is a valid tab delimited csv file'):
        generate_proxy_table(source_file_err, destination_dir, spark)


def test_cli(spark):
    runner = CliRunner()
    result = runner.invoke(cli, [
        '-m', 'local[2]',
        '-s', source_file,
        '-d', destination_dir,
        '-f', 'tests/test_config.yaml'])
    assert result.exit_code == 0

    df = spark.read.format('delta').load(destination_dir)
    assert df.count() == 3
    df.unpersist()

