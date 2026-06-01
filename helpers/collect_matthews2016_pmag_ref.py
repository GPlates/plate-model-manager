import os
import sys

import utils

model_path = utils.get_model_path(sys.argv, "matthews2016_pmag_ref")

# fetch Rotations
utils.fetch_and_zip_files(
    [
        "https://www.earthbyte.org/webdav/ftp/incoming/mchin/plate-models/MATTHEWS2016_pmag_ref/Matthews_etal_PMAG_PacificCorrected_fixed_crossovers.rot",
    ],
    model_path,
    "Rotations",
)

# fetch ContinentalPolygons
utils.fetch_and_zip_files(
    [
        "https://www.earthbyte.org/webdav/ftp/incoming/mchin/plate-models/MATTHEWS2016_pmag_ref/Matthews_etal_2016_ContinentalPolygons.gpmlz",
    ],
    model_path,
    "ContinentalPolygons",
)

# fetch COBs. this model does not provide COBs, use the continental polygons as COBs
utils.fetch_and_zip_files(
    [
        "https://www.earthbyte.org/webdav/ftp/incoming/mchin/plate-models/MATTHEWS2016_pmag_ref/Matthews_etal_2016_ContinentalPolygons.gpmlz",
    ],
    model_path,
    "COBs",
)

# fetch Coastlines
utils.fetch_and_zip_files(
    [
        "https://www.earthbyte.org/webdav/ftp/incoming/mchin/plate-models/MATTHEWS2016_pmag_ref/Matthews_etal_2016_CoastlineBlocks.gpmlz",
    ],
    model_path,
    "Coastlines",
)

# fetch StaticPolygons
utils.fetch_and_zip_files(
    [
        "https://www.earthbyte.org/webdav/ftp/incoming/mchin/plate-models/MATTHEWS2016_pmag_ref/Matthews_etal_2016_StaticPolygons.gpmlz"
    ],
    model_path,
    "StaticPolygons",
)
