"""Pipeline 08: load Allegheny Go weekly ridership into prt.db."""

from prt_otp_analysis.allegheny_go import main as allegheny_go_main


def main() -> None:
    """Run Allegheny Go ETL."""
    allegheny_go_main()


if __name__ == "__main__":
    main()
