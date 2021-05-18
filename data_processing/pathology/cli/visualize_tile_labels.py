'''
Created: February 2021
@author: aukermaa@mskcc.org

Given a slide (container) ID
1. resolve the path to the WSI image
2. perform various scoring and labeling to tiles
3. save tiles as a csv with schema [address, coordinates, *scores, *labels ]

Example:
python3 -m data_processing.pathology.cli.visualize_tile_labels \
    -c TCGA-BRCA \
    -s tcga-gm-a2db-01z-00-dx1.9ee36aa6-2594-44c7-b05c-91a0aec7e511 \
    -m data_processing/pathology/cli/example_visualize_tile_labels.json

Example with annotation:
python3 -m data_processing.pathology.cli.visualize_tile_labels \
        -c ov-path-druv  \
        -s 226871 \
        -m data_processing/pathology/cli/example_visualize_tile_labels.json 
'''

# General imports
import os, json, logging
import click
import tempfile
import subprocess

# From common
from data_processing.common.custom_logger   import init_logger
from data_processing.common.DataStore       import DataStore
from data_processing.common.Node            import Node
from data_processing.common.config          import ConfigSet

from data_processing.pathology.common.preprocess   import create_tile_thumbnail_image


@click.command()
@click.option('-a', '--app_config', required=True,
              help="application configuration yaml file. See config.yaml.template for details.")
@click.option('-c', '--cohort_id', required=True,
              help="cohort name")
@click.option('-s', '--datastore_id', required=True,
              help='datastore name. usually a slide id.')
@click.option('-m', '--method_param_path', required=True,
              help='json file with parameters for creating a heatmap and optionally pushing the annotation to DSA.')
def cli(app_config, cohort_id, datastore_id, method_param_path):
    init_logger()

    with open(method_param_path) as json_file:
        method_data = json.load(json_file)
    visualize_tile_labels_with_datastore(app_config, cohort_id, datastore_id, method_data)

def visualize_tile_labels_with_datastore(app_config: str, cohort_id: str, container_id: str, method_data: dict):
    """
    Using the container API interface, visualize tile-wise scores
    """
    logger = logging.getLogger(f"[datastore={container_id}]")

    # Do some setup
    cfg = ConfigSet("APP_CFG",  config_file=app_config)
    datastore   = DataStore( cfg ).setNamespace(cohort_id).setDatastore(container_id)
    method_id   = method_data.get("job_tag", "none")
    
    image_node  = datastore.get("WholeSlideImage", method_data['input_wsi_tag'])
    label_node  = datastore.get("TileScores",      method_data['input_label_tag'])

    method_data.update(label_node.properties)

    try:
        if image_node is None:
            raise ValueError("Image node not found")

        # Data just goes under namespace/name
        # TODO: This path is really not great, but works for now
        output_dir = os.path.join(os.environ['MIND_GPFS_DIR'], cfg.get_value(path="APP_CFG::ENV"),
                                  datastore._namespace_id, datastore._name, method_id)
        if not os.path.exists(output_dir): os.makedirs(output_dir)

        properties = create_tile_thumbnail_image(image_node.data, label_node.data, output_dir, method_data)

        # push results to DSA
        if method_data.get("dsa_config", None):
            properties = label_node.properties

            properties["column"]   = "tumor_score"
            properties["input"]    = label_node.properties["data"]
            properties["annotation_name"]   = method_id
            properties["tile_size"]   = method_data["tile_size"]
            properties["scale_factor"]   = method_data["scale_factor"]
            properties["magnification"]   = method_data["magnification"]
            properties["output_folder"]   = method_data["output_folder"]
            properties["image_filename"] = container_id + ".svs"            
            with tempfile.TemporaryDirectory() as tmpdir:
                print (tmpdir)
                with open(f"{tmpdir}/model_inference_config.json", "w") as f:
                    json.dump(properties, f)
                with open(f"{tmpdir}/dsa_config.json", "w") as f:
                    json.dump(method_data["dsa_config"], f)

                # build viz
                result = subprocess.run(["python3","-m","data_processing.pathology.cli.dsa.dsa_viz",
                                         "-s", "heatmap",
                                         "-d", f"{tmpdir}/model_inference_config.json"],
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                print(result.returncode, result.stdout, result.stderr)

                # push results to DSA
                result_path = result.stdout.split(" ")[-1].strip()
                properties["annotation_filepath"] = result_path
                properties["collection_name"] = method_data["collection_name"]
                with open(f"{tmpdir}/model_inference_config.json", "w") as f:
                    json.dump(properties, f)

                subprocess.run(["python3","-m","data_processing.pathology.cli.dsa.dsa_upload",
                                 "-c", f"{tmpdir}/dsa_config.json", "-d", f"{tmpdir}/model_inference_config.json"])

    except Exception as e:
        logger.exception (f"{e}, stopping job execution...")
        raise e

    # Put results in the data store
    output_node = Node("TileScores", method_id, properties)
    datastore.put(output_node)
        


if __name__ == "__main__":
    cli()
