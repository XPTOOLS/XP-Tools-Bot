import os
from dotenv import load_dotenv

load_dotenv()

def get_env_or_default(key, default=None, cast_func=str):
    value = os.getenv(key)
    if value is not None and value.strip() != "":
        try:
            return cast_func(value)
        except (ValueError, TypeError) as e:
            print(f"Error casting {key} with value '{value}' to {cast_func.__name__}: {e}")
            return default
    return default

API_ID = get_env_or_default("API_ID", "YOUR_API_ID", int)
API_HASH = get_env_or_default("API_HASH", "YOUR_API_HASH")
BOT_TOKEN = get_env_or_default("BOT_TOKEN", "YOUR_BOT_TOKEN")
SESSION_STRING = get_env_or_default("SESSION_STRING", "YOUR_SESSION_STRING")
OWNER_ID = get_env_or_default("OWNER_ID", "YOUR_OWNER_ID", int)
DEVELOPER_USER_ID = get_env_or_default("DEVELOPER_USER_ID", "YOUR_DEVELOPER_USER_ID", int)
MONGO_URL = get_env_or_default("MONGO_URL", "YOUR_MONGO_URL")
DATABASE_URL = get_env_or_default("DATABASE_URL", "YOUR_DATABASE_URL")
OPENAI_API_KEY = get_env_or_default("OPENAI_API_KEY", "Your_OPENAI_API_KEY_Here")
REPLICATE_API_TOKEN = get_env_or_default("REPLICATE_API_TOKEN", "Your_REPLICATE_API_TOKEN_Here")
GOOGLE_API_KEY = get_env_or_default("GOOGLE_API_KEY", "Your_GOOGLE_API_KEY_Here")
TRANS_API_KEY = get_env_or_default("TRANS_API_KEY", "Your_TRANS_API_KEY_Here")
OCR_API_KEY = get_env_or_default("OCR_API_KEY", "Your_OCR_API_KEY_Here")
MODEL_NAME = get_env_or_default("MODEL_NAME", "gemini-2.0-flash")
CC_SCRAPPER_LIMIT = get_env_or_default("CC_SCRAPPER_LIMIT", 5000, int)
SUDO_CCSCR_LIMIT = get_env_or_default("SUDO_CCSCR_LIMIT", 10000, int)
MULTI_CCSCR_LIMIT = get_env_or_default("MULTI_CCSCR_LIMIT", 2000, int)
MAIL_SCR_LIMIT = get_env_or_default("MAIL_SCR_LIMIT", 10000, int)
SUDO_MAILSCR_LIMIT = get_env_or_default("SUDO_MAILSCR_LIMIT", 15000, int)
CC_GEN_LIMIT = get_env_or_default("CC_GEN_LIMIT", 2000, int)
MULTI_CCGEN_LIMIT = get_env_or_default("MULTI_CCGEN_LIMIT", 5000, int)
TEXT_MODEL = get_env_or_default("TEXT_MODEL", "deepseek-r1-distill-llama-70b")
GROQ_API_URL = get_env_or_default("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
FILE_WORKER_URL = get_env_or_default("FILE_WORKER_URL", "Your_FILE_WORKER_URL_Here")
FILE_API_URL = get_env_or_default("FILE_API_URL", "Your_FILE_API_URL_Here")
GROQ_API_KEY = get_env_or_default("GROQ_API_KEY", "Your_GROQ_API_KEY_Here")
A360APIBASEURL = get_env_or_default("A360APIBASEURL", "https://a360api.vercel.app")
UPDATE_CHANNEL_URL = get_env_or_default("UPDATE_CHANNEL_URL", "https://t.me/XPTOOLSTEAM")
LOG_CHANNEL_ID = get_env_or_default("LOG_CHANNEL_ID", "-1002517323765", int)
raw_prefixes = get_env_or_default("COMMAND_PREFIX", "!|.|#|,|/")
COMMAND_PREFIX = [prefix.strip() for prefix in raw_prefixes.split("|") if prefix.strip()]
DOMAIN_CHK_LIMIT = get_env_or_default("DOMAIN_CHK_LIMIT", 20, int)
PROXY_CHECK_LIMIT = get_env_or_default("PROXY_CHECK_LIMIT", 20, int)
IMGAI_SIZE_LIMIT = get_env_or_default("IMGAI_SIZE_LIMIT", 5242880, int)
MAX_TXT_SIZE = get_env_or_default("MAX_TXT_SIZE", 15728640, int)
MAX_VIDEO_SIZE = get_env_or_default("MAX_VIDEO_SIZE", 2147483648, int)
YT_COOKIES_PATH = get_env_or_default("YT_COOKIES_PATH", "bot/SmartCookies/XPTOOLS.txt")
VIDEO_RESOLUTION = get_env_or_default("VIDEO_RESOLUTION", "1280x720", lambda x: tuple(map(int, x.split('x'))))
IMAGE_UPLOAD_KEY = get_env_or_default("IMAGE_UPLOAD_KEY", "Your_IMAGE_UPLOAD_KEY_Here")
IPINFO_API_TOKEN = get_env_or_default("IPINFO_API_TOKEN", "Your_IPINFO_API_TOKEN_Here")
WEB_SS_KEY = get_env_or_default("WEB_SS_KEY", "Your_WEB_SS_KEY_Here")

required_vars = {
    "API_ID": API_ID,
    "API_HASH": API_HASH,
    "BOT_TOKEN": BOT_TOKEN,
    "SESSION_STRING": SESSION_STRING,
    "OWNER_ID": OWNER_ID,
    "DEVELOPER_USER_ID": DEVELOPER_USER_ID,
    "MONGO_URL": MONGO_URL,
    "DATABASE_URL": DATABASE_URL
}

for var_name, var_value in required_vars.items():
    if var_value is None or var_value == f"Your_{var_name}_Here" or (isinstance(var_value, str) and var_value.strip() == ""):
        raise ValueError(f"Required variable {var_name} is missing or invalid. Set it in .env (VPS), config.py (VPS), or Heroku config vars.")

if not COMMAND_PREFIX:
    raise ValueError("No command prefixes found. Set COMMAND_PREFIX in .env, config.py, or Heroku config vars.")