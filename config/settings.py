import os

class Settings:
    # Web Engine Gateways
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))

    # Small Language Model Configurations
    MODEL_DIR: str = os.getenv(
        "MODEL_DIR", 
        "models/phi3/cpu_and_mobile/cpu-int4-rtn-block-32-acc-level-4"
    )
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", 200))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", 0.1))
    TOP_P: float = float(os.getenv("TOP_P", 0.9))

    # High-Velocity Redis Cache Topology
    # Defaults to local loopback for terminal tests; overridden by environment variables in Docker
    REDIS_HOST: str = os.getenv("REDIS_HOST", "127.0.0.1")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    REDIS_TTL: int = int(os.getenv("REDIS_TTL", 3600))

settings = Settings()