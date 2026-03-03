"""Pipeline 01: build the project SQLite database from source CSV inputs."""

from prt_otp_analysis.build_db import main as build_db_main


def main() -> None:
    """Run the canonical database build step."""
    build_db_main()


if __name__ == "__main__":
    main()
