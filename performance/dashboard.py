import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
import io
import pandas as pd
from flask import Flask, render_template, request, send_file, jsonify
from waitress import serve
import yaml
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({
    "font.family": "Segoe UI",   # Windows-safe
    "font.size": 12,
    "axes.titlesize": 14,
    "axes.labelsize": 12,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
})

import numpy as np
from matplotlib.patches import FancyBboxPatch

app = Flask(__name__)

CSV_FILE = os.path.join(PROJECT_ROOT, "dashboard_data.csv")



def load_csv():
    if not os.path.exists(CSV_FILE):
        return pd.DataFrame()
    return pd.read_csv(CSV_FILE, on_bad_lines="skip")

# =====================================================
# NEW: Load Board Models from ptp_setups.yaml
# =====================================================
def get_board_models():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    yaml_file = os.path.abspath(
        os.path.join(BASE_DIR, "..", "mikrotik", "ptp_setups.yaml")
    )

    if not os.path.exists(yaml_file):
        print("YAML NOT FOUND")
        return []

    with open(yaml_file, "r") as f:
        data = yaml.safe_load(f)

    if not data or "ptp_setups" not in data:
        print("ptp_setups key missing")
        return []

    return list(data["ptp_setups"].keys())


# =====================================================

def get_runs_for_model(board_model):
    if not board_model:
        return []

    model_path = os.path.join(RESULTS_DIR, board_model)

    if not os.path.exists(model_path):
        return []

    runs = [
        folder for folder in os.listdir(model_path)
        if os.path.isdir(os.path.join(model_path, folder))
    ]

    return sorted(runs, reverse=True)
# =====================================================
def generate_message_image(message):
    plt.figure(figsize=(8, 3))
    plt.style.use("dark_background")
    plt.text(0.5, 0.5,
             message,
             ha='center', va='center', fontsize=11)
    plt.xticks([])
    plt.yticks([])
    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format="png", facecolor="#0b1220")
    plt.close()
    img.seek(0)

    return send_file(img, mimetype="image/png")

# ==========================================
# HTML Dashboard Route

@app.route("/")
def home():

    selected_model = request.args.get("board_model")
    selected_run = request.args.get("run")

    channel = request.args.get("channel")
    tdd = request.args.get("tdd")
    mcs = request.args.get("mcs")

    board_models = get_board_models()
    runs = get_runs_for_model(selected_model)

    df = load_csv()

    if df.empty:
        return render_template(
            "index.html",
            data=[],
            tests=[],
            selected_test=None,
            pass_rate=0,
            last_run=None,
            devices=[],
            board_models=board_models,
            selected_model=selected_model,
            runs=runs,
            selected_run=selected_run,
            failed_cases=[]
        )

    # -----------------------------
    # Normalize structured columns
    # -----------------------------
    normalize_cols = ["run_id", "board_model", "channel", "tdd", "mcs", "test_name"]
    for col in normalize_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.sort_values("timestamp")

    test_filter = request.args.get("test_name")
    start_date = request.args.get("start")
    end_date = request.args.get("end")

    # -----------------------------
    # Structured Filtering
    # -----------------------------

    if selected_model:
        df = df[df["board_model"] == selected_model]

    if selected_run:
        df = df[df["run_id"] == selected_run]

    if channel and "channel" in df.columns:
        df = df[df["channel"] == channel]

    if tdd and "tdd" in df.columns:
        df = df[df["tdd"] == tdd]

    if mcs and "mcs" in df.columns:
        df = df[df["mcs"] == mcs]

    # -----------------------------
    # Build dropdown list BEFORE applying test filter
    # -----------------------------
    dropdown_df = df.copy()
    all_tests = dropdown_df["test_name"].dropna().unique().tolist()

    # -----------------------------
    # Exact test match (apply only to main df)
    # -----------------------------
    if test_filter:
        df = df[df["test_name"] == test_filter]

    # -----------------------------
    # Date Filtering (Corrected)
    # -----------------------------
    if start_date:
        start_date = pd.to_datetime(start_date)
        df = df[df["timestamp"] >= start_date]

    if end_date:
        end_date = pd.to_datetime(end_date) + pd.Timedelta(days=1)
        df = df[df["timestamp"] < end_date]

    # -----------------------------
    # PASS RATE
    # -----------------------------
    pass_rate = 0
    if len(df) > 0:
        pass_count = len(df[df["status"].str.strip().str.upper() == "PASS"])
        pass_rate = round((pass_count / len(df)) * 100, 2)

    last_run = df.iloc[-1].to_dict() if len(df) > 0 else None
    # -----------------------------
    # POP / DN Software Version
    # -----------------------------
    pop_version = None
    dn_version = None

    if not df.empty:

        if "pop_version" in df.columns:
            latest_pop = df["pop_version"].dropna()
            if not latest_pop.empty:
                pop_version = latest_pop.iloc[-1]

        if "dn_version" in df.columns:
            latest_dn = df["dn_version"].dropna()
            if not latest_dn.empty:
                dn_version = latest_dn.iloc[-1]

    # -----------------------------
    # Failed Cases
    # -----------------------------
    failed_cases = []
    if "status" in df.columns:
        failed_df = df[df["status"].str.strip().str.upper() == "FAIL"]
        failed_cases = failed_df.to_dict(orient="records")

    return render_template(
        "index.html",
        data=df.to_dict(orient="records"),
        tests=all_tests,
        selected_test=test_filter,
        pass_rate=pass_rate,
        last_run=last_run,
        devices=all_tests,
        board_models=board_models,
        selected_model=selected_model,
        runs=runs,
        selected_run=selected_run,
        channel=channel,
        tdd=tdd,
        mcs=mcs,
        failed_cases=failed_cases,
        pop_version=pop_version,
        dn_version=dn_version
    )

# ==========================================
# JSON API
# ==========================================
@app.route("/device_data")
def device_data():
    df = load_csv()

    if df.empty:
        return render_template(
            "index.html",
            data=[],
            tests=[],
            selected_test=None,
            pass_rate=0,
            last_run=None,
            devices=[],
            board_models=board_models,
            selected_model=selected_model,
            runs=runs,
            selected_run=selected_run
        )

    df["timestamp"] = pd.to_datetime(df["timestamp"])


    df = df.sort_values("timestamp")

    device = request.args.get("device")

    if device:
        df = df[df["test_name"] == device]

    return jsonify([
        {
            "timestamp": row["timestamp"].strftime("%H:%M:%S"),
            "uplink": row["sent_avg"],
            "downlink": row["recv_avg"],
            "status": row["status"]
        }
        for _, row in df.iterrows()
    ])


# ==========================================
# UPDATED GRAPH LOGIC
# ==========================================
# ==========================================
# UPDATED GRAPH LOGIC (DARK THEME + FIT FIX)
# ==========================================
@app.route("/device_graph_image")
def device_graph_image():

    plt.close('all')

    # ===============================
    # SAFE PARAM EXTRACTION FIRST
    # ===============================
    selected_model = request.args.get("board_model")
    selected_run = request.args.get("run")
    test_filter = request.args.get("test_name")
    start_date = request.args.get("start")
    end_date = request.args.get("end")
    channel = request.args.get("channel") or ""
    tdd = request.args.get("tdd") or ""
    mcs = request.args.get("mcs") or ""

    if not os.path.exists(CSV_FILE):
        return generate_message_image(
            "For selected filter we can not plot graph"
        )

    df = load_csv()
    if df.empty:
        return generate_message_image(
            "For selected filter we can not plot graph"
        )

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")

    # ===============================
    # FILTERING
    # ===============================
    if selected_model and selected_run:
        try:
            run_time = pd.to_datetime(selected_run, format="%Y%m%d_%H%M%S")
            run_end = run_time + pd.Timedelta(minutes=10)
            df = df[(df["timestamp"] >= run_time) &
                    (df["timestamp"] <= run_end)]
        except:
            pass

    if test_filter:
        df = df[df["test_name"] == test_filter]


    if start_date:
        df = df[df["timestamp"] >= pd.to_datetime(start_date)]

    if end_date:
        df = df[df["timestamp"] <
                pd.to_datetime(end_date) + pd.Timedelta(days=1)]

    if df.empty:
        return generate_message_image(
            "For selected filter we can not plot graph"
        )

    # ===============================
    # NUMERIC CLEANING
    # ===============================
    sent = pd.to_numeric(df["sent_avg"], errors="coerce")
    recv = pd.to_numeric(df["recv_avg"], errors="coerce")

    valid_mask = sent.notna() & recv.notna()
    sent = sent[valid_mask]
    recv = recv[valid_mask]

    time_series = pd.to_datetime(df["timestamp"])[valid_mask]
    seconds_axis = (time_series - time_series.min()).dt.total_seconds()


    if len(sent) == 0:
        return generate_message_image(
            "For selected filter we can not plot graph"
        )
        # ===============================
    # SMOOTHING (Wave Effect)
    # ===============================
    sent = sent.rolling(window=3, min_periods=1).mean()
    recv = recv.rolling(window=3, min_periods=1).mean()
    # ===============================
    # ORIGINAL PLOTTING LOGIC (UNCHANGED)
    # ===============================
    plt.style.use("dark_background")
    plt.figure(figsize=(9,4), dpi=120)

    ax = plt.gca()
    ax.set_facecolor("#0b1220")
    plt.gcf().set_facecolor("#0b1220")

    plt.xlabel("Time (seconds)", fontsize=8)
    plt.ylabel("Mbps", fontsize=8)
    plt.title("iPerf Performance - Selected Run", fontsize=9)

    plt.grid(True, alpha=0.2)
    plt.xticks(rotation=30)
    plt.tight_layout(pad=1.2)

    plt.rcParams.update({'font.size': 8})

    # =====================================
    # KEEPING YOUR ORIGINAL CONDITIONAL LOGIC
    # =====================================
    test_name = (test_filter or "").lower()

    is_uplink = "uplink" in test_name
    is_downlink = "downlink" in test_name
    is_bidir = "bidir" in test_name or "bidirectional" in test_name

    if is_uplink:
        avg_val = sent.mean()
        plt.plot(seconds_axis, sent, color="#f1e208", linewidth=2,
                 label="Uplink Throughput")
        plt.axhline(y=avg_val, linestyle="--", color="#f1e208",
                    label=f"Avg Uplink: {avg_val:.2f} Mbps")

    elif is_downlink:
        avg_val = sent.mean()
        plt.plot(seconds_axis, sent, color="#3b82f6", linewidth=2,
                 label="Downlink Throughput")
        plt.axhline(y=avg_val, linestyle="--", color="#3b82f6",
                    label=f"Avg Downlink: {avg_val:.2f} Mbps")

    else:
        plt.plot(seconds_axis, sent, color="#f1e208", linewidth=2,
                 label="Uplink Throughput")
        plt.plot(seconds_axis, recv, color="#3b82f6", linewidth=2,
                 label="Downlink Throughput")

        plt.axhline(y=sent.mean(), linestyle="--", color="#f1e208",
                    label=f"Avg Uplink: {sent.mean():.2f} Mbps")
        plt.axhline(y=recv.mean(), linestyle="--", color="#3b82f6",
                    label=f"Avg Downlink: {recv.mean():.2f} Mbps")

    plt.xlabel("Time", fontsize=8)
    plt.ylabel("Mbps", fontsize=8)

    ax.ticklabel_format(style='plain', axis='y')
    ax.yaxis.get_major_formatter().set_useOffset(False)

    plt.title("iPerf Performance - Selected Run", fontsize=9)

    plt.grid(True, alpha=0.2)
    plt.xticks(rotation=30)
    plt.tight_layout(pad=1.2)

    img = io.BytesIO()
    plt.savefig(img, format="png",
                bbox_inches="tight",
                facecolor="#0b1220")
    plt.close()
    img.seek(0)
    return send_file(img, mimetype="image/png")


@app.route("/export")
def export_excel():

    if not os.path.exists(CSV_FILE):
        return "No data available"

    df=load_csv()

    if df.empty:
        return "No data available"

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # safe trimming of params
    selected_model = request.args.get("board_model") or ""
    selected_model = selected_model.strip()

    channel = request.args.get("channel") or ""
    tdd = request.args.get("tdd") or ""
    mcs = request.args.get("mcs") or ""

    selected_run = request.args.get("run") or ""
    selected_run = selected_run.strip()

    test_filter = request.args.get("test_name") or ""
    test_filter = test_filter.strip()

    start_date = request.args.get("start") or ""
    start_date = start_date.strip()

    end_date = request.args.get("end") or ""
    end_date = end_date.strip()


    if selected_model and selected_run:
        try:
            run_time = pd.to_datetime(selected_run, format="%Y%m%d_%H%M%S")
            run_end = run_time + pd.Timedelta(minutes=10)

            df = df[
                (df["timestamp"] >= run_time) &
                (df["timestamp"] <= run_end)
            ]
        except:
            pass

    if test_filter:
        df = df[df["test_name"].str.contains(test_filter, na=False)]
    
    # # Apply only if CSV actually contains these strings
    # if channel and df["test_name"].str.contains(channel, na=False).any():
    #     df = df[df["test_name"].str.contains(channel, na=False)]

    # if tdd and df["test_name"].str.contains(tdd, na=False).any():
    #     df = df[df["test_name"].str.contains(tdd, na=False)]

    # if mcs and df["test_name"].str.contains(f"MCS{mcs}", na=False).any():
    #     df = df[df["test_name"].str.contains(f"MCS{mcs}", na=False)]

    if start_date:
        start_date = pd.to_datetime(start_date)
        df = df[df["timestamp"] >= start_date]

    if end_date:
        end_date = pd.to_datetime(end_date) + pd.Timedelta(days=1)
        df = df[df["timestamp"] < end_date]

    if df.empty:
        return "No filtered data available"

    df = df.sort_values("timestamp")

    output = io.BytesIO()

    metadata = pd.DataFrame({
        "Filter": [
            "Board Model",
            "Run",
            "Channel",
            "TDD",
            "MCS",
            "Test",
            "Start Date",
            "End Date"
        ],
        "Value": [
            selected_model or "All",
            selected_run or "All",
            channel or "All",
            tdd or "All",
            mcs or "All",
            test_filter or "All",
            start_date if start_date else "All",
            end_date if end_date else "All"
        ]
    })

    export_df = df.copy()
    export_df.rename(columns={
        "timestamp": "Timestamp",
        "test_name": "Test Name",
        "sent_avg": "Uplink (Mbps)",
        "recv_avg": "Downlink (Mbps)",
        "status": "Status"
    }, inplace=True)

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        metadata.to_excel(writer, sheet_name="Test Details", index=False)
        export_df.to_excel(writer, sheet_name="Test Results", index=False)

    output.seek(0)

    filename = "iperf_throughput_report.xlsx"

    return send_file(
        output,
        download_name=filename,
        as_attachment=True
    )


@app.route("/run_graph")
def run_graph():

    board_model = request.args.get("board_model")
    run = request.args.get("run")
    channel = request.args.get("channel")
    tdd = request.args.get("tdd")
    mcs = request.args.get("mcs")
    test_name = request.args.get("test_name")

    if not all([board_model, run, channel, tdd, mcs, test_name]):
        return generate_message_image("Graph parameters missing")

    tdd_folder = f"TDD {tdd}"
    mcs_folder = f"MCS{mcs}"
    graph_name = f"{test_name}_graph.png"

    graph_path = os.path.join(
        RESULTS_DIR,
        board_model,
        run,
        channel,
        tdd_folder,
        mcs_folder,
        graph_name
    )

    if not os.path.exists(graph_path):
        return generate_message_image(
            f"Graph not found:\n{graph_path}"
        )

    return send_file(graph_path, mimetype="image/png")

@app.route("/stream_comparison_graph")
def stream_comparison_graph():

    if not os.path.exists(CSV_FILE):
        return generate_message_image("No CSV data found")

    df = load_csv()
    if df.empty:
        return generate_message_image("CSV file is empty")

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    # Normalize filter columns
    normalize_cols = ["run_id", "board_model", "channel", "tdd", "mcs", "test_name"]
    for col in normalize_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    selected_run = request.args.get("run")
    selected_model = request.args.get("board_model")
    channel = request.args.get("channel")
    tdd = request.args.get("tdd")
    mcs = request.args.get("mcs")
    test_filter = request.args.get("test_name")

    if selected_run: selected_run = str(selected_run).strip()
    if selected_model: selected_model = str(selected_model).strip()
    if channel: channel = str(channel).strip()
    if tdd: tdd = str(tdd).strip()
    if mcs: mcs = str(mcs).strip()
    if test_filter: test_filter = str(test_filter).strip()

    if not selected_run:
        return generate_message_image("Select a Run ID")

    if not test_filter:
        return generate_message_image("Select a test")

    if "run_id" not in df.columns:
        return generate_message_image("run_id column missing in CSV")

    # Structured filtering
    df = df[df["run_id"] == selected_run]

    if selected_model and "board_model" in df.columns:
        df = df[df["board_model"] == selected_model]

    if channel and "channel" in df.columns:
        df = df[df["channel"] == channel]

    if tdd and "tdd" in df.columns:
        df = df[df["tdd"] == tdd]

    if mcs and "mcs" in df.columns:
        df = df[df["mcs"] == mcs]

    if df.empty:
        return generate_message_image("No data for selected filters")

    base_name = test_filter.replace("-1Stream", "").replace("-4Stream", "")

    plt.figure(figsize=(8, 5))
    plt.style.use("dark_background")

    width = 0.28
    gap = 0.05

    # =====================================================
    # 🔥 NEW: UDP GRAPH LOGIC (NO STREAM SPLIT REQUIRED)
    # =====================================================
    if "udp" in base_name.lower():

        udp_row = df[df["test_name"].str.contains(base_name, na=False)].copy()

        if udp_row.empty:
            return generate_message_image("UDP data not found")

        udp_row["sent_avg"] = pd.to_numeric(udp_row["sent_avg"], errors="coerce")
        udp_row["recv_avg"] = pd.to_numeric(udp_row["recv_avg"], errors="coerce")

        sent_value = udp_row["sent_avg"].mean()
        recv_value = udp_row["recv_avg"].mean()

        labels = []
        values = []

        if sent_value > 0:
            labels.append("Uplink")
            values.append(sent_value)

        if recv_value > 0:
            labels.append("Downlink")
            values.append(recv_value)

        if not values:
            return generate_message_image("UDP throughput invalid")

        x = np.arange(len(labels))

        if len(values) == 0:
            return generate_message_image("UDP throughput invalid")

        bar_width = 0.3  # make it slimmer

        bars = plt.bar(
            x,
            values,
            width=bar_width,
            color="#08c284"
        )

        # Control horizontal space
        if len(labels) == 1:
            plt.xlim(-0.8, 0.8)
        else:
            plt.xlim(-0.6, len(labels) - 0.4)

        # Add vertical headroom
        plt.ylim(0, max(values) * 1.2)

        for bar in bars:
            height = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width() / 2,
                height + 5,
                f"{height:.1f}",
                ha="center"
            )

        plt.xticks(x, labels)
        plt.ylabel("Throughput (Mbps)")
        plt.title(f"{base_name} Throughput")
        plt.grid(axis="y", alpha=0.2)

        plt.tight_layout(pad=2.0)

        img = io.BytesIO()
        plt.savefig(img, format="png", facecolor="#0b1220")
        plt.close()
        img.seek(0)

        return send_file(img, mimetype="image/png")

    # =====================================================
    # TCP LOGIC (CLEAN + CONSISTENT)
    # =====================================================

    one_stream = df[df["test_name"] == f"{base_name}-1Stream"].copy()
    four_stream = df[df["test_name"] == f"{base_name}-4Stream"].copy()

    if one_stream.empty or four_stream.empty:
        return generate_message_image(
            "Both 1Stream and 4Stream must exist in same run"
        )

    for col in ["sent_avg", "recv_avg"]:
        if col in one_stream.columns:
            one_stream[col] = pd.to_numeric(one_stream[col], errors="coerce")
        if col in four_stream.columns:
            four_stream[col] = pd.to_numeric(four_stream[col], errors="coerce")

    one_stream.dropna(subset=["sent_avg"], inplace=True)
    four_stream.dropna(subset=["sent_avg"], inplace=True)

    if one_stream.empty or four_stream.empty:
        return generate_message_image("Numeric throughput data missing")

    test_name_lower = base_name.lower()

    # -------------------------------
    # Determine direction correctly
    # -------------------------------
    if "bidir" in test_name_lower or "bidirectional" in test_name_lower:

        labels = ["Uplink", "Downlink"]

        one_values = [
            one_stream["sent_avg"].mean(),
            one_stream["recv_avg"].mean()
        ]

        four_values = [
            four_stream["sent_avg"].mean(),
            four_stream["recv_avg"].mean()
        ]

    elif "uplink" in test_name_lower:

        labels = ["Uplink"]

        one_values = [one_stream["sent_avg"].mean()]
        four_values = [four_stream["sent_avg"].mean()]

    elif "downlink" in test_name_lower:

        labels = ["Downlink"]

        one_values = [one_stream["sent_avg"].mean()]
        four_values = [four_stream["sent_avg"].mean()]

    else:
        # fallback
        labels = ["Throughput"]
        one_values = [one_stream["sent_avg"].mean()]
        four_values = [four_stream["sent_avg"].mean()]

    x = np.arange(len(labels))

    # -------------------------------
    # Symmetric spacing (correct way)
    # -------------------------------
    bars1 = plt.bar(
        x - (width/2 + gap/2),
        one_values,
        width,
        label="1 Stream",
        color="#08e4a2"
    )

    bars2 = plt.bar(
        x + (width/2 + gap/2),
        four_values,
        width,
        label="4 Stream",
        color="#15ade9"
    )

    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width()/2,
                height + 5,
                f"{height:.1f}",
                ha="center"
            )

    # Proper axis limits
    plt.xlim(-0.6, len(labels) - 0.4)
    plt.ylim(0, max(one_values + four_values) * 1.2)

    plt.xticks(x, labels)
    plt.ylabel("Throughput (Mbps)")
    plt.title(f"{base_name} Throughput: 1 Stream vs 4 Stream")
    plt.legend()
    plt.grid(axis="y", alpha=0.2)

    plt.tight_layout(pad=2.0)

    img = io.BytesIO()
    plt.savefig(img, format="png", facecolor="#0b1220")
    plt.close()
    img.seek(0)

    return send_file(img, mimetype="image/png")

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=8000)