# Django settings
from .database.settings import *  # noqa: F401, F403

# Set logging level
import logging
LOGGING_LEVEL = logging.INFO

# Default queue names
POSTPROCESS_INFO = "POSTPROCESS.INFO"
POSTPROCESS_ERROR = "POSTPROCESS.ERROR"
CATALOG_DATA_READY = "CATALOG.DATA_READY"
REDUCTION_DATA_READY = "REDUCTION.DATA_READY"
REDUCTION_CATALOG_DATA_READY = "REDUCTION_CATALOG.DATA_READY"

# Import local settings if available
try:
    from .local_settings import *  # noqa: F401, F403
except ImportError:
    LOCAL_SETTINGS = False
    pass
