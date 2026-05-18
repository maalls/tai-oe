"""Runtime launcher for FastAPI transport."""

import os

import uvicorn
from src.infrastructure.runtime.env_loader import load_runtime_env


def main() -> None:
    load_runtime_env(__file__)
    port = int(os.environ.get("PORT", "8088"))
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    main()
