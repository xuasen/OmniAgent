"""CLI entrypoint for running OmniAgent."""

import uvicorn

from omniagent.settings import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "omniagent.app:create_app",
        factory=True,
        host=settings.server.host,
        port=settings.server.port,
        workers=settings.server.workers,
        log_level=settings.server.log_level,
    )


if __name__ == "__main__":
    main()
