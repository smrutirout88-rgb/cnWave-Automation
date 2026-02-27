import json
import sys
import os
import matplotlib.pyplot as plt


def plot_iperf(json_file, output_image):

    test_name = os.path.basename(json_file).lower()

    is_uplink = "uplink" in test_name
    is_downlink = "downlink" in test_name
    is_bidir = "bidir" in test_name or "bidirectional" in test_name
    is_udp = "udp" in test_name
    is_tcp = "tcp" in test_name

    with open(json_file, 'r') as f:
        data = json.load(f)

    intervals = data["intervals"]

    # Keep original lists (for compatibility)
    times = []
    sent_bw = []
    recv_bw = []

    # NEW: Separate time tracking to prevent dimension mismatch
    times_sent = []
    times_recv = []

    for i, interval in enumerate(intervals):
        current_time = i + 1
        times.append(current_time)

        if "streams" in interval:
            tx_total = 0
            rx_total = 0

            for stream in interval["streams"]:
                bps = stream["bits_per_second"] / 1_000_000

                if stream.get("sender", False):
                    tx_total += bps
                else:
                    rx_total += bps

            # Sender data
            if tx_total > 0:
                sent_bw.append(tx_total)
                times_sent.append(current_time)

            # Receiver data
            if rx_total > 0:
                recv_bw.append(rx_total)
                times_recv.append(current_time)

            # Backward compatibility (single direction cases)
            if tx_total == 0 and rx_total > 0:
                sent_bw.append(rx_total)
                times_sent.append(current_time)

        elif "sum" in interval:
            value = interval["sum"]["bits_per_second"] / 1_000_000
            sent_bw.append(value)
            times_sent.append(current_time)

    if not sent_bw:
        print("No throughput data found")
        return

    # -----------------------------
    # Correct Average Calculation
    # -----------------------------

    bidirectional = len(recv_bw) > 0

    if is_udp:
        if "end" in data:
            end_data = data["end"]

            # Handle iperf UDP structure safely
            if "streams" in end_data and len(end_data["streams"]) >= 1:
                # Sender stream
                sender_stream = end_data["streams"][0]["udp"]
                sent_bps = sender_stream["bits_per_second"]
                sent_loss = sender_stream.get("lost_percent", 0)

                # Effective throughput after loss
                avg_sent = (sent_bps * (1 - sent_loss / 100)) / 1_000_000

                # Receiver stream (bidirectional case)
                if len(end_data["streams"]) > 1:
                    recv_stream = end_data["streams"][1]["udp"]
                    recv_bps = recv_stream["bits_per_second"]
                    recv_loss = recv_stream.get("lost_percent", 0)

                    avg_recv = (recv_bps * (1 - recv_loss / 100)) / 1_000_000
                    bidirectional = True
                else:
                    bidirectional = False
            else:
                avg_sent = sum(sent_bw) / len(sent_bw)
        else:
            avg_sent = sum(sent_bw) / len(sent_bw)
    else:
        avg_sent = sum(sent_bw) / len(sent_bw)

    if bidirectional and not is_udp:
        avg_recv = sum(recv_bw) / len(recv_bw)

    # -----------------------------
    # PRINT VALUES FOR ROBOT PARSING
    # -----------------------------
    if bidirectional:
        print(f"Average Sent Throughput: {avg_sent:.2f} Mbps")
        print(f"Average Received Throughput: {avg_recv:.2f} Mbps")
    else:
        print(f"Average Throughput: {avg_sent:.2f} Mbps")

    # -----------------------------
    # Dynamic Title
    # -----------------------------
    protocol = "UDP" if is_udp else "TCP"

    if is_uplink:
        title = f"iPerf {protocol} Uplink Performance"
    elif is_downlink:
        title = f"iPerf {protocol} Downlink Performance"
    elif is_bidir:
        title = f"iPerf {protocol} Bidirectional Performance"
    else:
        title = "iPerf Performance Graph"

    plt.figure()

    # -----------------------------
    # Safe Plot Logic
    # -----------------------------
    if is_downlink:
        plt.plot(times_sent, sent_bw, label="Downlink Throughput")
        plt.axhline(y=avg_sent, linestyle="--",
                    label=f"Avg Downlink: {avg_sent:.2f} Mbps")

    elif is_uplink:
        plt.plot(times_sent, sent_bw, label="Uplink Throughput")
        plt.axhline(y=avg_sent, linestyle="--",
                    label=f"Avg Uplink: {avg_sent:.2f} Mbps")

    else:
        # Bidirectional
        plt.plot(times_sent, sent_bw, label="Uplink Throughput")
        plt.axhline(y=avg_sent, linestyle="--",
                    label=f"Avg Uplink: {avg_sent:.2f} Mbps")

        if bidirectional:
            plt.plot(times_recv, recv_bw, label="Downlink Throughput")
            plt.axhline(y=avg_recv, linestyle="--",
                        label=f"Avg Downlink: {avg_recv:.2f} Mbps")

    plt.xlabel("Time (seconds)")
    plt.ylabel("Throughput (Mbps)")
    plt.title(title)
    plt.legend()
    plt.grid(True)

    # Disable scientific offset like +2e3
    ax = plt.gca()
    ax.ticklabel_format(style='plain', axis='y')
    ax.yaxis.get_major_formatter().set_useOffset(False)

    # Ensure directory exists before saving
    output_dir = os.path.dirname(output_image)

    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    plt.savefig(output_image)
    plt.close()


if __name__ == "__main__":
    plot_iperf(sys.argv[1], sys.argv[2])