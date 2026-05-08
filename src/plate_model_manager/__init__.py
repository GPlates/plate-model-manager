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

setup_logging()


__all__ = [
    "PlateModelManager",
    "PresentDayRasterManager",
    "PlateModel",
    "get_plate_model",
]
