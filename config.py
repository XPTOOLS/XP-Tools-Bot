import os

# Don't use dotenv on Render - environment variables are injected directly
try:
    from dotenv import load_dotenv
    # Only load .env if it exists (for local development)
    if os.path.exists('.env'):
        load_dotenv()
        print("Loaded .env file for local development")
except ImportError:
    pass

def get_env_or_default(key, default=None, cast_func=str):
    value = os.getenv(key)
    if value is not None and value.strip() != "":
        try:
            return cast_func(value)
        except (ValueError, TypeError) as e:
            print(f"Error casting {key} with value '{value}' to {cast_func.__name__}: {e}")
            return default
    return default

API_ID = get_env_or_default("API_ID", None, int)
API_HASH = get_env_or_default("API_HASH", None)
BOT_TOKEN = get_env_or_default("BOT_TOKEN", None)
SESSION_STRING = get_env_or_default("SESSION_STRING", None)
OWNER_ID = get_env_or_default("OWNER_ID", None, int)
DEVELOPER_USER_ID = get_env_or_default("DEVELOPER_USER_ID", None, int)
MONGO_URL = get_env_or_default("MONGO_URL", None)
DATABASE_URL = get_env_or_default("DATABASE_URL", None)
OPENAI_API_KEY = get_env_or_default("OPENAI_API_KEY", "")
REPLICATE_API_TOKEN = get_env_or_default("REPLICATE_API_TOKEN", "")
GOOGLE_API_KEY = get_env_or_default("GOOGLE_API_KEY", "")
TRANS_API_KEY = get_env_or_default("TRANS_API_KEY", "")
OCR_API_KEY = get_env_or_default("OCR_API_KEY", "")
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
FILE_WORKER_URL = get_env_or_default("FILE_WORKER_URL", "")
FILE_API_URL = get_env_or_default("FILE_API_URL", "")
GROQ_API_KEY = get_env_or_default("GROQ_API_KEY", "")
A360APIBASEURL = get_env_or_default("A360APIBASEURL", "https://a360api.vercel.app")
UPDATE_CHANNEL_URL = get_env_or_default("UPDATE_CHANNEL_URL", "https://t.me/XPTOOLSTEAM")
LOG_CHANNEL_ID = get_env_or_default("LOG_CHANNEL_ID", -1002517323765, int)
raw_prefixes = get_env_or_default("COMMAND_PREFIX", "!|.|#|,|/")
COMMAND_PREFIX = [prefix.strip() for prefix in raw_prefixes.split("|") if prefix.strip()]
DOMAIN_CHK_LIMIT = get_env_or_default("DOMAIN_CHK_LIMIT", 20, int)
PROXY_CHECK_LIMIT = get_env_or_default("PROXY_CHECK_LIMIT", 20, int)
IMGAI_SIZE_LIMIT = get_env_or_default("IMGAI_SIZE_LIMIT", 5242880, int)
MAX_TXT_SIZE = get_env_or_default("MAX_TXT_SIZE", 15728640, int)
MAX_VIDEO_SIZE = get_env_or_default("MAX_VIDEO_SIZE", 2147483648, int)
YT_COOKIES_PATH = get_env_or_default("YT_COOKIES_PATH", "bot/SmartCookies/XPTOOLS.txt")
VIDEO_RESOLUTION = get_env_or_default("VIDEO_RESOLUTION", "1280x720", lambda x: tuple(map(int, x.split('x'))))
IMAGE_UPLOAD_KEY = get_env_or_default("IMAGE_UPLOAD_KEY", "")
IPINFO_API_TOKEN = get_env_or_default("IPINFO_API_TOKEN", "")
WEB_SS_KEY = get_env_or_default("WEB_SS_KEY", "")

# Validate required variables
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

missing_vars = []
for var_name, var_value in required_vars.items():
    if var_value is None or (isinstance(var_value, str) and var_value.strip() == ""):
        missing_vars.append(var_name)

if missing_vars:
    raise ValueError(f"Required variables missing: {', '.join(missing_vars)}. Set them in Render environment variables.")

if not COMMAND_PREFIX:
    raise ValueError("No command prefixes found. Set COMMAND_PREFIX in environment variables.")

print(f"Configuration loaded successfully. Bot prefix: {COMMAND_PREFIX}")
