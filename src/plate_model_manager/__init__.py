#
#    Copyright (C) 2024-2026 The University of Sydney, Australia
#
#    This program is free software; you can redistribute it and/or modify it under
#    the terms of the GNU General Public License, version 2, as published by
#    the Free Software Foundation.
#
#    This program is distributed in the hope that it will be useful, but WITHOUT
#    ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#    FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
#    for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
from .utils.misc import get_distribution_version

# __version__ = "1.3.0"
__version__ = get_distribution_version()
del get_distribution_version

from .auxiliary import check_update, get_plate_model
from .plate_model import PlateModel
from .plate_model_manager import PlateModelManager
from .present_day_rasters import PresentDayRasterManager
from .utils.misc import (
    disable_stdout_logging,
    is_debug_mode,
    set_logging_level,
    setup_logging,
    turn_on_debug_logging,
)
from .utils.enums import ReferenceFrame, GenerationMethod
from .utils.download import FileDownloader
from .zenodo import ZenodoRecord

setup_logging()


__all__ = [
    "PlateModelManager",
    "PresentDayRasterManager",
    "PlateModel",
    "get_plate_model",
    "FileDownloader",
]
