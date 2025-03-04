from pathlib import Path

import fire
import numpy as np
import pandas as pd
import scipy.ndimage
from loguru import logger

from luna.radiology.mirp.imageReaders import read_itk_image


def coregister_volumes(
    input_itk_volume: str,
    input_itk_geometry: str,
    resample_pixel_spacing: float,
    output_dir: str,
    order: int,
    save_npy: bool,
):
    """Resamples and co-registeres all volumes to occupy the same physical coordinates of a reference geometry (given as a itk_volume) and desired voxel size

    Args:
        input_itk_volume (str): path to itk compatible image volume (.mhd, .nrrd, .nii, etc.)
        input_itk_geometry (str): path to itk compatible image volume (.mhd, .nrrd, .nii, etc.) to use as a reference geometry
        output_dir (str): output/working directory
        resample_pixel_spacing (float): voxel size in mm
        order (int): interpolation order [0-5]
        save_npy(bool): whether to also save a numpy file representing the volume

    Returns:
        dict: metadata about function call
    """
    d_properties = {}

    resample_pixel_spacing = np.full((3), resample_pixel_spacing)

    image_class_object_volume = read_itk_image(
        input_itk_volume, modality=str(Path(input_itk_volume).stem)
    )
    image_class_object_geometry = read_itk_image(
        input_itk_geometry, modality=str(Path(input_itk_geometry).stem)
    )

    _ = interpolate(
        image_class_object_volume,
        resample_pixel_spacing,
        reference_geometry=image_class_object_geometry,
        order=order,
    )

    image_file = image_class_object_volume.export(file_path=output_dir)
    d_properties["itk_volume"] = image_file

    if save_npy:
        np.save(image_file + ".npy", image_class_object_volume.get_voxel_grid())
        d_properties["npy_volume"] = image_file + ".npy"

    # d_properties['volume_size']    = list (image_class_object_volume.size.flatten())
    # d_properties['volume_spacing'] = list (image_class_object_volume.spacing.flatten())
    # d_properties['volume_percentiles'] = list (np.percentile(image_class_object_volume.get_voxel_grid(), np.linspace(0, 100, 11)).flatten())

    output_file = f"{output_dir}/volume_registered_features.parquet"
    pd.DataFrame([d_properties]).to_parquet(output_file)

    d_properties["feature_data"] = output_file

    return d_properties


def interpolate(image, resample_spacing, reference_geometry, order=3):
    """Run interplation

    Args:
        image (imageClass): mirp image class object
        resample_spacing (np.ndarray): spacing of resample as a 1D vector
        reference_geometry (imageClass): output/working directory
        order (int): interpolation order [0-5]

    Returns:
        imageClass: mirp image class object after resample
    """

    image_size = image.size
    image_spacing = image.spacing
    image_voxels = image.voxel_grid
    image_origin = image.origin
    logger.info("Image size=%s, spacing=%s" % (image_size, image_spacing))

    reference_origin = reference_geometry.origin

    reference_offset = (reference_origin - image_origin) / image_spacing
    logger.info("Reference offset=%s" % (reference_offset))

    grid_spacing = resample_spacing / image_spacing

    grid_size = np.ceil(
        np.multiply(
            reference_geometry.size, reference_geometry.spacing / resample_spacing
        )
    )

    logger.info("Grid spacing=%s, size=%s" % (grid_spacing, grid_size))

    map_z, map_y, map_x = np.mgrid[: grid_size[0], : grid_size[1], : grid_size[2]]

    map_z = map_z * grid_spacing[0] + reference_offset[0]
    map_y = map_y * grid_spacing[1] + reference_offset[1]
    map_x = map_x * grid_spacing[2] + reference_offset[2]

    logger.info("Z=%s, Y=%s, Z=%s" % (map_z.shape, map_y.shape, map_x.shape))

    resampled_image = scipy.ndimage.map_coordinates(
        input=image_voxels.astype(np.float32),
        coordinates=np.array([map_z, map_y, map_x], dtype=np.float32),
        order=order,
        mode="nearest",
    )

    print(resampled_image.shape)
    logger.info("Resampled size=%s" % (list(resampled_image.shape)))

    image.set_spacing(resample_spacing)
    image.set_origin(image_origin + (reference_origin - image_origin))
    image.set_voxel_grid(voxel_grid=resampled_image)

    logger.info("New origin=%s" % (image.origin))

    return resampled_image


def fire_cli():
    fire.Fire(coregister_volumes)


if __name__ == "__main__":
    fire_cli()
