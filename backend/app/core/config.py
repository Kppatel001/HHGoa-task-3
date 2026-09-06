"""Application configuration loaded from environment / .env.

All secrets and tunables live here. Nothing sensitive is hardcoded except the
well-known *public* Hardhat dev key, which is safe to ship for local demos.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # App
    app_env: str = Field(default="development", alias="APP_ENV")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173", alias="CORS_ORIGINS"
    )
    upload_dir: str = Field(default="./data/uploads", alias="UPLOAD_DIR")
    max_upload_size_mb: int = Field(default=10, alias="MAX_UPLOAD_SIZE_MB")
    delete_uploads_after_session: bool = Field(
        default=True, alias="DELETE_UPLOADS_AFTER_SESSION"
    )
    store_embeddings: bool = Field(default=False, alias="STORE_EMBEDDINGS")

    # Database
    database_url: str = Field(default="sqlite:///./faceproof.db", alias="DATABASE_URL")

    # Face
    face_model: str = Field(default="buffalo_l", alias="FACE_MODEL")
    face_exec_provider: str = Field(
        default="CPUExecutionProvider", alias="FACE_EXEC_PROVIDER"
    )
    face_match_threshold: float = Field(default=0.35, alias="FACE_MATCH_THRESHOLD")
    face_det_min_confidence: float = Field(
        default=0.5, alias="FACE_DET_MIN_CONFIDENCE"
    )
    face_min_pixels: int = Field(default=60, alias="FACE_MIN_PIXELS")

    # Search — genuine Google Programmable Search by default.
    # Only GOOGLE_CSE_API_KEY must be supplied at runtime (as a secret env var).
    # Set SEARCH_PROVIDER=demo to use the bundled local fixtures instead.
    search_provider: str = Field(default="google_cse", alias="SEARCH_PROVIDER")
    google_cse_api_key: str = Field(default="", alias="GOOGLE_CSE_API_KEY")
    google_cse_cx: str = Field(default="e7a1f794d6d134d25", alias="GOOGLE_CSE_CX")
    search_max_results: int = Field(default=8, alias="SEARCH_MAX_RESULTS")
    search_http_timeout: float = Field(default=15.0, alias="SEARCH_HTTP_TIMEOUT")
    candidate_max_image_bytes: int = Field(
        default=8_000_000, alias="CANDIDATE_MAX_IMAGE_BYTES"
    )

    # Blockchain
    # "rpc"    -> connect to an external EVM node (Hardhat / testnet)
    # "memory" -> run a real EVM in-process (eth-tester); no node/Node.js needed
    blockchain_mode: str = Field(default="rpc", alias="BLOCKCHAIN_MODE")
    blockchain_rpc_url: str = Field(
        default="http://127.0.0.1:8545", alias="BLOCKCHAIN_RPC_URL"
    )
    blockchain_chain_id: int = Field(default=31337, alias="BLOCKCHAIN_CHAIN_ID")
    blockchain_private_key: str = Field(default="", alias="BLOCKCHAIN_PRIVATE_KEY")
    contract_address: str = Field(default="", alias="CONTRACT_ADDRESS")
    block_explorer_url: str = Field(default="", alias="BLOCK_EXPLORER_URL")
    # Override where deployment artifacts (<chainId>.json) are read from.
    # Empty -> derive path relative to the repo (contracts/deployments).
    deployments_dir: str = Field(default="", alias="DEPLOYMENTS_DIR")

    # Firebase Realtime Database (optional, durable record/history store).
    # Set FIREBASE_DB_URL to enable it; otherwise the local SQLite DB is used.
    # Lightweight REST integration (no heavy SDK) so it works on serverless too.
    firebase_db_url: str = Field(
        default="https://faceproof-1a326-default-rtdb.firebaseio.com",
        alias="FIREBASE_DB_URL",
    )
    firebase_db_secret: str = Field(default="", alias="FIREBASE_DB_SECRET")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @property
    def firebase_enabled(self) -> bool:
        return bool(self.firebase_db_url)

    @field_validator("face_match_threshold")
    @classmethod
    def _check_threshold(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("FACE_MATCH_THRESHOLD must be between 0 and 1")
        return v

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def is_demo_search(self) -> bool:
        return self.search_provider.lower() == "demo"


@lru_cache
def get_settings() -> Settings:
    s = Settings()  # type: ignore[call-arg]
    # On Vercel (or any serverless host) the filesystem is read-only except
    # /tmp, so force writable paths and the stateless-friendly modes there.
    import os as _os

    if _os.environ.get("VERCEL") or _os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        if s.database_url.startswith("sqlite") and "/tmp/" not in s.database_url:
            s.database_url = "sqlite:////tmp/faceproof.db"
        if not s.upload_dir.startswith("/tmp"):
            s.upload_dir = "/tmp/uploads"
        # In-process EVM needs no external node — the only fit for serverless.
        s.blockchain_mode = "memory"
        # Zero-config safety: genuine Google search needs an API key. If none is
        # supplied, fall back to the bundled demo dataset so the pipeline always
        # works out of the box instead of dead-ending on "search unavailable".
        if s.search_provider.lower() == "google_cse" and not s.google_cse_api_key:
            s.search_provider = "demo"
    return s


settings = get_settings()
