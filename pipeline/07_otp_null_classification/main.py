"""Pipeline 07: classify OTP null values using schedule and ridership cross-references."""

from prt_otp_analysis.otp_null_classification import main as classify_main


def main() -> None:
    """Run OTP null classification."""
    classify_main()


if __name__ == "__main__":
    main()
