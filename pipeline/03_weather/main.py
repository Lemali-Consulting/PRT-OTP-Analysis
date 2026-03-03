"""Pipeline 03: load monthly NOAA weather features into prt.db."""

from prt_otp_analysis.weather import main as weather_main


def main() -> None:
    """Run weather ETL."""
    weather_main()


if __name__ == "__main__":
    main()
