# 56 - City Centerline and OTP

Cross-validates Analysis 55's lane-count -> OTP finding using the independent City of
Pittsburgh street centerline (which includes local streets, not just state roads). Recomputes
per-route lane count from the city network and re-tests it against on-time performance with a
structural OLS baseline and nested F-test.

Run: `uv run python analyses/56_city_centerline_otp/main.py`
