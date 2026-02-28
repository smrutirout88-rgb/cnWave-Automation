📦 Release Notes
cnWave 60GHz PTP Automation Framework
Version: v1
Release Date: 28 Feb 2026
🚀 Overview

This release introduces cnWave 60GHz PTP Automation Framework, enhancing execution reliability, result accuracy, filtering precision, and dashboard visibility.

Key focus areas:

Full traffic matrix execution stability

Enhanced run-based filtering

Stream comparison accuracy

Controller version integration

Improved dashboard UX and data integrity

🆕 New Features
1️⃣ Non-Blocking Traffic Matrix Execution

Traffic execution now continues even if an individual throughput test fails.

Implemented Run Keyword And Continue On Failure

Ensures complete matrix execution (TCP 1/4 stream, UDP, Bidirectional)

Prevents partial CSV logging

Improves dashboard consistency

Result:
All performance scenarios are executed fully even under failure conditions.

2️⃣ Run-Based Filtering (run_id Integration)

Added run_id column to dashboard_data.csv

Stream comparison graph now filters using run_id instead of timestamp

Eliminates cross-run data mixing

Ensures accurate gain comparison (TCP 1S vs 4S)

Impact:
Reliable historical run comparison and correct summary graph rendering.

3️⃣ Unified Channel / TDD / MCS Filtering

Enhanced filtering logic across:

Home route

Device graph image route

Stream comparison graph

Export route

Filtering now dynamically reflects:

Selected run

Channel (CB1 / CB2)

TDD ratio

MCS index

Frontend improvement:

TDD filter auto-hides when CB2 is selected

4️⃣ Controller Software Version Logging

POP and DN software versions fetched during suite setup

Versions printed in console

Prepared for dashboard display integration before Channel filters

Benefit:
Improves traceability between performance data and device firmware version.

5️⃣ Stream Comparison Graph Enhancement

Replaced summary graph with:

TCP 1-Stream vs 4-Stream Gain Bar Chart

Features:

Per-run filtering

Channel-specific comparison

Accurate performance delta visualization

Clean gain-based display logic

6️⃣ Structured Run Directory Initialization

Dynamic result folder creation

Channel → TDD → MCS directory hierarchy

Consistent naming format for graph images

Improves:

Result traceability

Debug visibility

Automation maintainability


📊 Performance Impact

Full matrix execution without interruption

Reliable graph generation

Consistent run-based analytics

Improved failure traceability

🧪 Validation Scope

Validated scenarios include:

CB1

TDD: 50-50, 75-25, 30-70

MCS: 12, 9, 2

TCP 1S / 4S (DL, UL, Bidirectional)

UDP (DL, UL, Bidirectional)


CB2

TDD: 50-50

MCS: 12, 9, 2

TCP 1S / 4S (DL, UL, Bidirectional)

UDP (DL, UL, Bidirectional)

🔮 Next Planned Enhancements

Multi-run comparison mode

Performance threshold auto-fail logic

Add new chart to compare results between CB1 and CB2 in dashboard

Add upgrade cases

Add regulatory testing

Create SIT approved previous results and make a DB so it can show somewhere we can just select older results in dashboard and w.r.t to builds it can just display the throughout numbers
