import os
import sys

import utils

model_path = utils.get_model_path(sys.argv, "pehrsson2015")

# fetch Rotations
utils.fetch_and_zip_files(
    [
        "https://www.earthbyte.org/webdav/ftp/incoming/mchin/plate-models/PEHRSSON2015/T_Rot_Model_Abs_25Ma_20131004.rot"
    ],
    model_path,
    "Rotations",
)


# fetch Coastlines
utils.fetch_and_zip_files(
    [
        "https://www.earthbyte.org/webdav/ftp/incoming/mchin/plate-models/PEHRSSON2015/PlatePolygons.dbf",
        "https://www.earthbyte.org/webdav/ftp/incoming/mchin/plate-models/PEHRSSON2015/PlatePolygons.sbn",
        "https://www.earthbyte.org/webdav/ftp/incoming/mchin/plate-models/PEHRSSON2015/PlatePolygons.sbx",
        "https://www.earthbyte.org/webdav/ftp/incoming/mchin/plate-models/PEHRSSON2015/PlatePolygons.shp",
        "https://www.earthbyte.org/webdav/ftp/incoming/mchin/plate-models/PEHRSSON2015/PlatePolygons.shp.gplates.xml",
        "https://www.earthbyte.org/webdav/ftp/incoming/mchin/plate-models/PEHRSSON2015/PlatePolygons.shp.xml",
        "https://www.earthbyte.org/webdav/ftp/incoming/mchin/plate-models/PEHRSSON2015/PlatePolygons.shx",
    ],
    model_path,
    "Coastlines",
)

# fetch StaticPolygons
utils.fetch_and_zip_files(
    [
        "https://www.earthbyte.org/webdav/ftp/incoming/mchin/plate-models/PEHRSSON2015/PlatePolygons.dbf",
        "https://www.earthbyte.org/webdav/ftp/incoming/mchin/plate-models/PEHRSSON2015/PlatePolygons.sbn",
        "https://www.earthbyte.org/webdav/ftp/incoming/mchin/plate-models/PEHRSSON2015/PlatePolygons.sbx",
        "https://www.earthbyte.org/webdav/ftp/incoming/mchin/plate-models/PEHRSSON2015/PlatePolygons.shp",
        "https://www.earthbyte.org/webdav/ftp/incoming/mchin/plate-models/PEHRSSON2015/PlatePolygons.shp.gplates.xml",
        "https://www.earthbyte.org/webdav/ftp/incoming/mchin/plate-models/PEHRSSON2015/PlatePolygons.shp.xml",
        "https://www.earthbyte.org/webdav/ftp/incoming/mchin/plate-models/PEHRSSON2015/PlatePolygons.shx",
    ],
    model_path,
    "StaticPolygons",
)
