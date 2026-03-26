import pandas as pd
import sqlite3
import numpy as np

def predict_failures():
    conn = sqlite3.connect("netfix_metrics.db")
    df = pd.read_sql("SELECT * FROM metrics", conn)
    conn.close()

    alerts = []
    devices = df["device_name"].unique()

    for device in devices:
        device_df = df[df["device_name"] == device].sort_values("timestamp")
        metrics_list = device_df["metric_name"].unique()

        for metric in metrics_list:
            metric_df = device_df[device_df["metric_name"] == metric].copy()
            if len(metric_df) < 3:
                continue

            values = metric_df["value"].values
            crit = metric_df["crit_threshold"].values[0]
            warn = metric_df["warn_threshold"].values[0]
            current = values[-1]
            status = metric_df["status"].values[-1]

            if status == "CRITICAL":
                continue

            x = np.arange(len(values))
            slope = np.polyfit(x, values, 1)[0]

            if slope > 0 and current > warn * 0.8:
                steps_to_crit = (crit - current) / slope if slope > 0 else 999
                if 0 < steps_to_crit < 6:
                    minutes = int(steps_to_crit * 5)
                    alerts.append({
                        "device": device,
                        "metric": metric,
                        "current": round(current, 1),
                        "threshold": crit,
                        "trend": round(slope, 2),
                        "eta_minutes": minutes,
                        "message": f"{device} — {metric} is trending towards CRITICAL. Current: {round(current,1)}, predicted to hit {crit} in ~{minutes} mins."
                    })

    return alerts