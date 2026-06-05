# 57 - Pavement Condition and OTP

Tests whether pavement roughness (IRI), from SPC's NHS pavement-condition layer, predicts
a bus route's on-time performance -- and crucially whether it survives controlling for road
width (lane count from Analysis 55). Adds road *quality* to the road *geometry* measures of
Analyses 55/56 via a nested OLS ladder and F-tests.

Run: `uv run python analyses/57_pavement_condition_otp/main.py`
