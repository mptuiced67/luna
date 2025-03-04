import fire
import numpy as np
from loguru import logger

from luna.radiology.mirp.imagePerturbations import randomise_roi_contours
from luna.radiology.mirp.imageProcess import (
    combine_all_rois,
    combine_pertubation_rois,
    crop_image,
    interpolate_image,
    interpolate_roi,
)
from luna.radiology.mirp.imageReaders import read_itk_image, read_itk_segmentation
from luna.radiology.mirp.importSettings import Settings


def randomize_contours(
    input_itk_volume: str,
    input_itk_labels: str,
    resample_pixel_spacing: float,
    resample_smoothing_beta: float,
    output_dir: str,
):
    """Generate randomize contours given and image, label after resampling using MIRP processing library

    First, we interpolate the inputs to a isotropic spacing, then get the supervoxel pertubations using the MIRP methods,
    as defined in:

    Zwanenburg, A., Leger, S., Agolli, L. et al. Assessing robustness of radiomic features by image perturbation. Sci Rep 9, 614 (2019). https://doi.org/10.1038/s41598-018-36938-4

    Args:
        input_itk_volume (str): path to itk compatible image volume (.mhd, .nrrd, .nii, etc.)
        input_itk_labels (str): path to itk compatible label volume (.mha)
        output_dir (str): output/working directory
        resample_pixel_spacing (float): voxel size in mm
        resample_smoothing_beta (float): smoothing beta of gaussian filter

    Returns:
        dict: metadata about function call
    """
    logger.info("Hello, processing %s, %s", input_itk_volume, input_itk_labels)
    settings = Settings()

    print(settings)

    resample_pixel_spacing = np.full((3), resample_pixel_spacing)

    settings.img_interpolate.new_spacing = resample_pixel_spacing
    settings.roi_interpolate.new_spacing = resample_pixel_spacing
    settings.img_interpolate.smoothing_beta = resample_smoothing_beta

    # Read
    image_class_object = read_itk_image(input_itk_volume, "CT")
    roi_class_object_list = read_itk_segmentation(input_itk_labels)

    # Crop for faster interpolation
    image_class_object, roi_class_object_list = crop_image(
        img_obj=image_class_object,
        roi_list=roi_class_object_list,
        boundary=50.0,
        z_only=True,
    )

    # Interpolation
    image_class_object = interpolate_image(
        img_obj=image_class_object, settings=settings
    )
    roi_class_object_list = interpolate_roi(
        img_obj=image_class_object, roi_list=roi_class_object_list, settings=settings
    )

    # Export
    image_file = image_class_object.export(file_path=f"{output_dir}/main_image")

    # ROI processing
    roi_class_object = combine_all_rois(
        roi_list=roi_class_object_list, settings=settings
    )
    label_file = roi_class_object.export(
        img_obj=image_class_object, file_path=f"{output_dir}/main_label"
    )

    roi_class_object_list, svx_class_object_list = randomise_roi_contours(
        img_obj=image_class_object, roi_list=roi_class_object_list, settings=settings
    )

    roi_supervoxels = combine_all_rois(
        roi_list=svx_class_object_list, settings=settings
    )
    voxels_file = roi_supervoxels.export(
        img_obj=image_class_object, file_path=f"{output_dir}/supervoxels"
    )

    for roi in combine_pertubation_rois(
        roi_list=roi_class_object_list, settings=settings
    ):
        if "COMBINED" in roi.name:
            roi.export(
                img_obj=image_class_object, file_path=f"{output_dir}/pertubations"
            )

    print(image_file, label_file)

    # Construct return dicts
    properties = {
        "itk_volume": image_file,
        "itk_labels": label_file,
        "mirp_pertubations": f"{output_dir}/pertubations",
        "mirp_supervoxels": voxels_file,
    }

    return properties


def fire_cli():
    fire.Fire(randomize_contours)


if __name__ == "__main__":
    fire_cli()
