#!/bin/python
import re
import readline
import subprocess
import sys
import time
from datetime import datetime, timedelta

try:
    import zoneinfo
except ImportError:
    sys.exit("Error: Python 3.9+ is required for the zoneinfo timezone module.")


def get_all_panes():
    """Fetches all active tmux panes."""
    fmt = "#{pane_id}|#{pane_tty}|#{pane_current_command}|#{session_name}:#{window_index}.#{pane_index}"
    result = subprocess.check_output(["tmux", "list-panes", "-a", "-F", fmt]).decode().strip()
    return [
        dict(zip(["id", "tty", "cmd", "location"], line.split("|")))
        for line in result.split("\n")
    ]


def select_pane(panes, prompt_text):
    """Use fzf to interactively select a pane with live preview of pane content."""
    # Tab-separated: pane_id (hidden) + visible columns
    lines = [f"{p['id']}\t{p['location']:<20}\t{p['tty']:<15}\t{p['cmd']}" for p in panes]
    fzf_input = "\n".join(lines).encode()

    # {1} is the hidden pane_id field; preview captures its live content
    preview_cmd = "tmux capture-pane -p -t {1} -S -50 2>/dev/null || echo '(preview unavailable)'"

    subprocess.run(["clear"])
    result = subprocess.run(
        [
            "fzf",
            "--prompt",
            f"{prompt_text} > ",
            "--height",
            "50%",
            "--layout",
            "reverse",
            "--border",
            "--delimiter",
            "\t",
            "--with-nth",
            "2..",  # show location / tty / cmd; hide pane_id
            "--nth",
            "2..",  # fuzzy-search only visible columns
            "--preview",
            preview_cmd,
            "--preview-window",
            "right:60%:wrap",
            "--header",
            f"{'LOCATION':<20}\t{'TTY':<15}\tPROCESS",
        ],
        input=fzf_input,
        stdout=subprocess.PIPE,  # capture selection; leave stderr for terminal
    )

    if result.returncode != 0:
        print("No pane selected. Exiting.")
        sys.exit(0)

    chosen_line = result.stdout.decode().strip()
    return panes[lines.index(chosen_line)]


ANSI_ESCAPE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def capture_pane_text(pane_id, history_lines=100):
    """Captures the visible text and scrollback history from a tmux pane."""
    try:
        cmd = ["tmux", "capture-pane", "-p", "-t", pane_id, "-S", f"-{history_lines}"]
        raw = subprocess.check_output(cmd).decode("utf-8")
        return ANSI_ESCAPE.sub("", raw)
    except subprocess.CalledProcessError as e:
        print(f"Failed to capture pane output: {e}")
        return ""


def extract_reset_times(text):
    """Finds all reset strings and extracts the (time, timezone)."""
    pattern = r"resets[\s\u00A0]+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s*\(([^)]+)\)"
    matches = re.findall(pattern, text, re.IGNORECASE)
    # deduplicate while preserving order
    seen = set()
    unique = []
    for m in matches:
        if m not in seen:
            seen.add(m)
            unique.append(m)
    return unique


SEND_DELAY = 60  # seconds after reset before sending, to clear rate limit


def fmt_duration(seconds):
    h, r = divmod(int(seconds), 3600)
    m, s = divmod(r, 60)
    return f"{h}h {m}m {s}s" if h else f"{m}m {s}s"


def sleep_with_progress(total_seconds, label):
    """Sleep in chunks, printing progress every 60s for long waits."""
    chunk = 10 if total_seconds <= 120 else 60
    elapsed = 0
    while elapsed < total_seconds:
        remaining = total_seconds - elapsed
        print(f"  [{label}] {fmt_duration(remaining)} remaining...", flush=True)
        time.sleep(min(chunk, remaining))
        elapsed += chunk


def calculate_target_datetime(time_str, tz_str):
    """Calculates the absolute future datetime for the target timezone."""
    try:
        tz = zoneinfo.ZoneInfo(tz_str)
    except zoneinfo.ZoneInfoNotFoundError:
        print(f"Warning: Timezone '{tz_str}' not found. Defaulting to local time.")
        tz = None  # Falls back to local system time

    now = datetime.now(tz)
    time_str = time_str.lower()

    if ":" not in time_str:
        time_str = time_str.replace("am", ":00am").replace("pm", ":00pm")

    # Parse the time string (handles both AM/PM and 24hr formats)
    if "am" in time_str or "pm" in time_str:
        target_time = datetime.strptime(time_str, "%I:%M%p").time()
    else:
        target_time = datetime.strptime(time_str, "%H:%M").time()

    # Combine today's date with the target time
    target_dt = datetime.combine(now.date(), target_time, tzinfo=tz)

    # If the time has already passed today, the reset is tomorrow
    if target_dt <= now:
        target_dt += timedelta(days=1)

    return target_dt


if __name__ == "__main__":
    try:
        panes = get_all_panes()

        # 1. Select panes
        source_pane = select_pane(panes, "--- Select the SOURCE pane (to read text from) ---")
        dest_pane = select_pane(
            panes, "--- Select the DESTINATION pane (to send commands to) ---"
        )

        # 2. Read output
        print(f"\nScanning output from {source_pane['id']}...")
        log_text = capture_pane_text(source_pane["id"])

        # 3. Extract matching times
        matches = extract_reset_times(log_text)
        settings_needed = len(matches)

        if settings_needed == 0:
            print("No reset times found in the pane's recent history. Exiting.")
            sys.exit(0)

        print(f"---> Found {settings_needed} reset triggers.")

        # 4. Gather commands and calculate delays dynamically
        tasks = []
        readline.set_history_length(50)
        try:
            for time_str, tz_str in matches:
                target_dt = calculate_target_datetime(time_str, tz_str)
                delay_sec = (target_dt - datetime.now(target_dt.tzinfo)).total_seconds()

                h, r = divmod(int(delay_sec), 3600)
                m, s = divmod(r, 60)

                print(f"\n--- Setting for Reset at {time_str} ({tz_str}) ---")
                print(f"Time until reset: {h}h {m}m {s}s")
                prompt = input("Enter text to send (↑/↓ for history): ")
                if prompt:
                    readline.add_history(prompt)

                tasks.append(
                    {
                        "prompt": prompt,
                        "target_dt": target_dt,
                        "label": f"{time_str} ({tz_str})",
                    }
                )
        except KeyboardInterrupt:
            print("\nConfiguration cancelled.")
            sys.exit(0)

        # 5. Sort tasks chronologically (crucial if resets are out of order)
        tasks.sort(key=lambda x: x["target_dt"].timestamp())

        # 6. Execute Schedule
        total_tasks = len(tasks)
        print("\nStarting execution sequence...")
        for i, task in enumerate(tasks):
            now_ts = datetime.now().timestamp()
            target_ts = task["target_dt"].timestamp()
            wait_seconds = target_ts - now_ts
            send_ts = target_ts + SEND_DELAY
            send_local = datetime.fromtimestamp(send_ts).strftime("%H:%M:%S")

            label = f"[{i + 1}/{total_tasks}] {task['label']}"
            print(f"\n{label} — command will send at {send_local} (local)")

            if wait_seconds > 0:
                print("Waiting for reset...")
                sleep_with_progress(wait_seconds, "until reset")

            print(f"Reset reached. Waiting {SEND_DELAY}s before sending...")
            sleep_with_progress(SEND_DELAY, "post-reset delay")

            subprocess.run(["tmux", "send-keys", "-t", dest_pane["id"], task["prompt"], "C-m"])
            print(f"Sent command for {task['label']}.")

        print("\nAll tasks completed successfully!")

    except Exception as e:
        print(f"Error: {e}")
