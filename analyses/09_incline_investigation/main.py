"""Data audit of the Monongahela Incline's presence in OTP data."""

from pathlib import Path

import polars as pl

from prt_otp_analysis.common import output_dir, query_to_polars

HERE = Path(__file__).resolve().parent
OUT = output_dir(HERE)


def investigate() -> str:
    """Query all tables for Incline-related data and build a report."""
    lines = []
    lines.append("=" * 60)
    lines.append("Monongahela Incline Investigation Report")
    lines.append("=" * 60)

    # 1. Routes table
    lines.append("\n## 1. Routes table (route_id = 'MI' or mode = 'INCLINE')")
    routes = query_to_polars("""
        SELECT * FROM routes WHERE route_id = 'MI' OR mode = 'INCLINE'
    """)
    if len(routes) > 0:
        for row in routes.iter_rows(named=True):
            lines.append(f"  route_id={row['route_id']}, name={row['route_name']}, mode={row['mode']}")
    else:
        lines.append("  No matching rows found.")

    # 2. OTP monthly
    lines.append("\n## 2. OTP monthly (route_id = 'MI')")
    otp = query_to_polars("""
        SELECT * FROM otp_monthly WHERE route_id = 'MI'
    """)
    if len(otp) > 0:
        lines.append(f"  {len(otp)} rows found:")
        for row in otp.iter_rows(named=True):
            lines.append(f"    month={row['month']}, otp={row['otp']}")
    else:
        lines.append("  No OTP data found for MI.")

    # 3. Route stops
    lines.append("\n## 3. Route stops (route_id = 'MI')")
    route_stops = query_to_polars("""
        SELECT rs.*, s.stop_name, s.lat, s.lon
        FROM route_stops rs
        LEFT JOIN stops s ON rs.stop_id = s.stop_id
        WHERE rs.route_id = 'MI'
    """)
    if len(route_stops) > 0:
        lines.append(f"  {len(route_stops)} stop-route pairs found:")
        for row in route_stops.iter_rows(named=True):
            lines.append(
                f"    stop_id={row['stop_id']}, name={row['stop_name']}, "
                f"dir={row['direction']}, trips_wd={row['trips_wd']}, trips_7d={row['trips_7d']}"
            )
    else:
        lines.append("  No stops associated with MI in route_stops.")

    # 4. Stops table (search for incline-related stops)
    lines.append("\n## 4. Stops table (name containing 'incline' or 'monongahela')")
    stops = query_to_polars("""
        SELECT * FROM stops
        WHERE LOWER(stop_name) LIKE '%incline%'
           OR LOWER(stop_name) LIKE '%monongahela%'
    """)
    if len(stops) > 0:
        lines.append(f"  {len(stops)} stops found:")
        for row in stops.iter_rows(named=True):
            lines.append(
                f"    stop_id={row['stop_id']}, name={row['stop_name']}, "
                f"hood={row['hood']}, muni={row['muni']}"
            )
    else:
        lines.append("  No incline-related stops found in current stops.")

    # 5. Stop reference (historical)
    lines.append("\n## 5. Stop reference (mode = 'INCLINE' or name containing 'incline')")
    stop_ref = query_to_polars("""
        SELECT * FROM stop_reference
        WHERE mode = 'INCLINE'
           OR LOWER(stop_name) LIKE '%incline%'
           OR LOWER(stop_name) LIKE '%monongahela%'
    """)
    if len(stop_ref) > 0:
        lines.append(f"  {len(stop_ref)} historical stops found:")
        for row in stop_ref.iter_rows(named=True):
            lines.append(
                f"    stop_id={row['stop_id']}, name={row['stop_name']}, "
                f"mode={row['mode']}, first={row['first_served']}, last={row['last_served']}"
            )
    else:
        lines.append("  No incline-related stops in historical reference.")

    # 6. Conclusion
    lines.append("\n## 6. Conclusion")
    if len(otp) == 0:
        lines.append("  The Monongahela Incline (MI) exists in the routes table but has")
        lines.append("  NO entries in otp_monthly. OTP was never recorded for this route")
        lines.append("  in the dataset. This is a data pipeline artifact -- the Incline")
        lines.append("  was included in the route catalog but excluded from OTP measurement.")
    else:
        otp_values = otp["otp"].to_list()
        non_null = [v for v in otp_values if v is not None and v > 0]
        if not non_null:
            lines.append("  The Incline has OTP rows but all values are zero or null.")
            lines.append("  This suggests OTP measurement was set up but never populated.")
        else:
            lines.append(f"  The Incline has {len(non_null)} months with non-zero OTP data.")
            lines.append("  Further analysis needed to evaluate its performance.")

    return "\n".join(lines)


def main() -> None:
    """Entry point: investigate the Incline data and produce a report."""
    print("=" * 60)
    print("Analysis 09: Incline Investigation")
    print("=" * 60)

    print("\nInvestigating...")
    report = investigate()
    print(report)

    # Save report
    report_path = OUT / "incline_report.txt"
    report_path.write_text(report, encoding="utf-8")
    print(f"\n  Report saved to {report_path}")

    # Save any OTP data as CSV
    otp = query_to_polars("SELECT * FROM otp_monthly WHERE route_id = 'MI'")
    route_stops = query_to_polars("""
        SELECT rs.*, s.stop_name
        FROM route_stops rs
        LEFT JOIN stops s ON rs.stop_id = s.stop_id
        WHERE rs.route_id = 'MI'
    """)
    stop_ref = query_to_polars("""
        SELECT * FROM stop_reference
        WHERE mode = 'INCLINE' OR LOWER(stop_name) LIKE '%incline%'
    """)

    # Combine all incline data into one CSV
    all_data = []
    if len(otp) > 0:
        all_data.append(otp.with_columns(source=pl.lit("otp_monthly")))
    if len(route_stops) > 0:
        # Select compatible columns
        rs_summary = route_stops.select("route_id", "stop_id", "stop_name", "direction", "trips_wd", "trips_7d")
        rs_summary.write_csv(OUT / "incline_route_stops.csv")
        print(f"  Route stops saved to {OUT / 'incline_route_stops.csv'}")
    if len(stop_ref) > 0:
        stop_ref.write_csv(OUT / "incline_stop_reference.csv")
        print(f"  Stop reference saved to {OUT / 'incline_stop_reference.csv'}")

    if len(otp) > 0:
        otp.write_csv(OUT / "incline_report.csv")
        print(f"  OTP data saved to {OUT / 'incline_report.csv'}")
    else:
        # Write empty CSV with headers
        pl.DataFrame({"route_id": [], "month": [], "otp": []}).write_csv(OUT / "incline_report.csv")
        print(f"  Empty OTP CSV saved to {OUT / 'incline_report.csv'}")

    print("\nDone.")


if __name__ == "__main__":
    main()
