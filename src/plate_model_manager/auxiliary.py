import logging
import os
import re
from typing import Union

from .exceptions import ServerUnavailable
from .plate_model import PlateModel
from .plate_model_manager import PlateModelManager
from .zenodo import ZenodoRecord

logger = logging.getLogger("pmm")


def get_plate_model(
    model_name: str, data_dir: Union[str, os.PathLike]
) -> Union[PlateModel, None]:
    """Return a plate model instance using online lookup with local fallback.

    This helper first attempts to resolve ``model_name`` through
    :class:`PlateModelManager`. If the PMM servers are unavailable, it falls back
    to creating a local, read-only :class:`PlateModel` from files already present
    in ``data_dir``.

    :param model_name: Name of the plate model to resolve.
    :param data_dir: Directory containing downloaded plate model data.
    :returns: A :class:`PlateModel` instance, or ``None`` if the model name cannot
        be resolved.

    Example usage:

    .. code-block:: python

        from plate_model_manager import get_plate_model

        model = get_plate_model("Muller2025", data_dir="plate-models-data-dir")
        if model is not None:
            print(model.get_rotation_model())
        else:
            print("Model not found.")
    """
    try:
        model = PlateModelManager().get_model(model_name, data_dir=data_dir)
    except ServerUnavailable:
        # if unable to connect to the servers, try to use the local files
        model = PlateModel(model_name=model_name, data_dir=data_dir, readonly=True)
        logger.warning(
            "Unable to connect to the servers. Using local files in readonly mode."
        )
    return model


def check_update():
    """Check whether configured models have newer versions on Zenodo.

    For each model that includes both ``URL`` and ``Version`` metadata, this
    function compares the stored Zenodo version identifier against the latest
    available record version. It logs update status for each model and logs a
    summary when everything is up-to-date.

    This function is intended for PMM server maintenance workflows.
    """
    need_update = False
    models = PlateModelManager().models
    for model_name in models:
        logger.info(f"Checking update for model -- {model_name} ...")
        model = models[model_name]
        if isinstance(model, dict) and "URL" in model and "Version" in model:
            record_id = re.findall(r"zenodo.(\d+)", model["URL"])
            version_id = re.findall(r"zenodo.(\d+)", model["Version"])
            if len(record_id) == 1 and len(version_id) == 1:
                # logger.info(record_id[0])
                latest_id = str(ZenodoRecord(record_id[0]).get_latest_version_id())
                if version_id[0] != latest_id:
                    need_update = True
                    logger.info(
                        f"Model ({model_name}) needs update. The latest version ID is: {latest_id}. Your current version ID is : {version_id[0]}."
                    )
    if not need_update:
        logger.info("All models are up-to-date.")
