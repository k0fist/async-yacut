import re
import string


MAX_LENGTH_ORIGINAL_URL = 2048
MAX_LENGTH_SHORT = 16
SHORT_ID_CHARACTERS = string.ascii_letters + string.digits
ALLOWED_SHORT_RE = re.compile(rf'^[{re.escape(SHORT_ID_CHARACTERS )}]+$')
MAX_SHORT_ATTEMPTS = 5
DEFAULT_SHORT_ID_LENGTH = 6