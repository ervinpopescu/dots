#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import html
import re
import tempfile


def main():
    print("Gathering chezmoi status...")
    try:
        status_out = subprocess.check_output(["chezmoi", "status"]).decode("utf-8")
    except subprocess.CalledProcessError as e:
        sys.exit(f"Failed to run chezmoi status: {e}")

    lines = [
        l for l in status_out.split("\n") if l.strip() and not l.startswith("chezmoi: warning")
    ]
    files_status = {}
    for line in lines:
        parts = line.split(maxsplit=1)
        if len(parts) == 2:
            status = parts[0]
            filepath = parts[1]

            # Temporary filter: ignore all qtile files
            if ".config/qtile" in filepath:
                continue

            # Ignore directories unless they are explicitly marked as renamed/moved
            home_dir = os.path.expanduser("~")
            full_path = os.path.join(home_dir, filepath)

            # If the status is just modification (M) and it's a directory, it just means contents changed, skip it.
            if os.path.isdir(full_path) and status.strip() in ["M", "MM", "A"]:
                continue

            files_status[filepath] = status

    if not files_status:
        print("No changes found in chezmoi.")
        sys.exit(0)

    print("Gathering chezmoi diff...")
    try:
        diff_text = subprocess.check_output(["chezmoi", "diff", "--no-pager"]).decode("utf-8")
    except subprocess.CalledProcessError as e:
        diff_text = e.output.decode("utf-8")

    diffs = {}
    current_file = None
    current_diff = []

    for line in diff_text.split("\n"):
        if line.startswith("diff --git "):
            if current_file and current_diff:
                diffs[current_file] = "\n".join(current_diff)
            match = re.match(r"diff --git a/(.*?) b/", line)
            if match:
                current_file = match.group(1)
                current_diff = [line]
        else:
            if current_file:
                current_diff.append(line)
    if current_file and current_diff:
        diffs[current_file] = "\n".join(current_diff)

    file_panels = []
    for filepath, status in files_status.items():
        badge_color = "badge-info"
        if status.strip() == "A":
            badge_color = "badge-success"
        elif status.strip() == "D":
            badge_color = "badge-error"
        elif status.strip() == "MM":
            badge_color = "badge-warning"

        panel = f"""
        <div class="file-panel bg-base-100 border border-base-300 rounded-box mb-6 shadow-sm collapse collapse-arrow" data-file="{html.escape(filepath)}">
            <input type="checkbox" checked />
            <div class="collapse-title flex flex-col sm:flex-row justify-between items-start sm:items-center p-3 bg-base-200 border-b border-base-300 gap-4 sm:gap-0 z-10">
                <div class="flex items-center gap-3">
                    <span class="badge {badge_color} font-bold">{html.escape(status)}</span>
                    <span class="font-mono text-sm font-semibold">{html.escape(filepath)}</span>
                </div>
                <div class="flex items-center gap-6 w-full sm:w-auto justify-between sm:justify-end" onclick="event.stopPropagation()">
                    <label class="cursor-pointer label p-0 gap-2">
                        <span class="label-text font-semibold">Viewed</span>
                        <input type="checkbox" class="checkbox checkbox-sm checkbox-primary viewed-checkbox" />
                    </label>
                    <select class="select select-sm select-bordered action-select bg-base-100 w-full sm:w-64">
                        <option value="none">Ignore (Do nothing)</option>
                        <option value="add">Keep Local (chezmoi add)</option>
                        <option value="revert">Revert (chezmoi apply)</option>
                    </select>
                </div>
            </div>
            <div class="collapse-content diff-container p-0 overflow-x-auto rounded-b-box bg-base-100">
                <div class="diff-render p-4"></div>
            </div>
        </div>
        """
        file_panels.append(panel)

    html_template = """<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <title>Chezmoi Diff Review</title>
  <script src="https://unpkg.com/@tailwindcss/browser@4"></script>
  <link href="https://cdn.jsdelivr.net/npm/daisyui@5.0.0-beta.1/daisyui.css" rel="stylesheet" type="text/css" />
  <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/diff2html/bundles/css/diff2html.min.css" />
  <style>
    body { background-color: #1e1e2e; color: #cdd6f4; }
    .d2h-dark-color-scheme {
        --d2h-bg-color: #1e1e2e;
        --d2h-border-color: #313244;
        --d2h-file-header-bg-color: #181825;
        --d2h-empty-placeholder-bg-color: #11111b;
        --d2h-moved-line-bg-color: #f9e2af;
        --d2h-ins-line-bg-color: rgba(166, 227, 161, 0.2);
        --d2h-del-line-bg-color: rgba(243, 139, 168, 0.2);
        --d2h-ins-line-color: #a6e3a1;
        --d2h-del-line-color: #f38ba8;
        --d2h-moved-line-color: #f9e2af;
    }
    .d2h-code-line { font-size: 0.85rem; }
    .file-panel { background-color: #181825; border-color: #313244; }
    .diff-container { background-color: #1e1e2e; }
  </style>
</head>
<body class="font-sans min-h-screen bg-base-300 pb-12">

<div class="navbar bg-base-100 sticky top-0 z-50 shadow-md px-6 flex justify-between border-b border-base-300">
  <div class="flex items-center gap-4">
    <h1 class="text-xl font-bold text-primary">Chezmoi Review</h1>
    <span class="text-sm opacity-70 ml-4"><span class="text-error font-bold">Left/Red</span> is Local File. <span class="text-success font-bold">Right/Green</span> is Chezmoi Source.</span>
    <div class="badge badge-lg badge-neutral gap-2 ml-4">
        Viewed
        <span id="viewed-count" class="font-bold text-primary">0</span>
        /
        <span id="total-count">0</span>
    </div>
  </div>
  <div class="flex flex-wrap gap-2 justify-end">
    <button id="queue-viewed" class="btn btn-secondary btn-sm" type="button">Queue viewed + hide</button>
    <button id="show-viewed" class="btn btn-ghost btn-sm" type="button">Show viewed</button>
    <button class="btn btn-primary shadow-lg" onclick="openReviewModal()">Review Changes</button>
  </div>
</div>

<div id="panels-container" class="p-6 max-w-[95%] mx-auto mt-4">
  __FILE_PANELS__
</div>

<dialog id="review_modal" class="modal">
  <div class="modal-box w-11/12 max-w-4xl bg-base-100">
    <h3 class="font-bold text-2xl mb-4 text-primary">Review Summary</h3>
    <p class="mb-2">Run the following commands in your terminal to apply your choices:</p>
    <textarea id="script-output" class="textarea textarea-bordered w-full font-mono text-sm h-72 bg-base-300 text-base-content" readonly></textarea>

    <div class="alert alert-warning mt-4 shadow-sm text-warning-content">
      <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
      <div>
          <h3 class="font-bold">Template Warning</h3>
          <div class="text-sm">For files managed as chezmoi templates, running <code>chezmoi add</code> will overwrite the template source with a static file. If you have custom template logic in those files, you should manually update them using <code>chezmoi edit</code> instead.</div>
      </div>
    </div>

    <div class="modal-action">
      <button class="btn btn-primary" onclick="copyScript()">Copy Commands</button>
      <form method="dialog">
        <button class="btn btn-neutral">Close</button>
      </form>
    </div>
  </div>
  <form method="dialog" class="modal-backdrop">
    <button>close</button>
  </form>
</dialog>

<script type="text/javascript" src="https://cdn.jsdelivr.net/npm/diff2html/bundles/js/diff2html-ui.min.js"></script>
<script id="diff-data" type="application/json">__DIFF_JSON__</script>

<script>
  document.addEventListener('DOMContentLoaded', () => {
    const diffData = JSON.parse(document.getElementById('diff-data').textContent);
    const panels = document.querySelectorAll('.file-panel');
    document.getElementById('total-count').textContent = panels.length;

    let viewedCount = 0;
    const updateProgress = () => {
      document.getElementById('viewed-count').textContent = viewedCount;
    };

    const viewedFiles = () => [...panels]
      .filter(panel => panel.querySelector('.viewed-checkbox').checked)
      .map(panel => panel.getAttribute('data-file'));

    const hideViewed = () => panels.forEach(panel => {
      if (panel.querySelector('.viewed-checkbox').checked) panel.classList.add('hidden');
    });

    const showViewed = () => panels.forEach(panel => panel.classList.remove('hidden'));

    document.getElementById('queue-viewed').addEventListener('click', () => {
      const files = viewedFiles();
      if (!files.length) {
        alert('Mark at least one file as Viewed first.');
        return;
      }

      const text = `I reviewed these chezmoi files; exclude them from the remaining review:\\n${files.map(file => `- ${file}`).join('\\n')}`;
      if (!window.lavish || !window.lavish.queuePrompt) {
        alert('Lavish queueing is unavailable in this view.');
        return;
      }

      window.lavish.queuePrompt(text, {
        tag: 'reviewed-files',
        text: `Exclude ${files.length} reviewed file${files.length === 1 ? '' : 's'} from the remaining review`,
        queueKey: 'reviewed-files',
        data: { files }
      });
      hideViewed();
    });

    document.getElementById('show-viewed').addEventListener('click', showViewed);

    // Use event delegation for better performance
    document.getElementById('panels-container').addEventListener('change', (e) => {
      if (e.target.classList.contains('viewed-checkbox')) {
        const panel = e.target.closest('.file-panel');
        const diffOuter = panel.querySelector('.diff-container');
        const diffRender = panel.querySelector('.diff-render');

        if (e.target.checked) {
          diffOuter.classList.add('hidden');
          panel.classList.add('opacity-60');
          // Free up memory/DOM nodes for faster browser layout
          diffRender.innerHTML = '';
          diffRender.dataset.rendered = "false";
          viewedCount++;
        } else {
          diffOuter.classList.remove('hidden');
          panel.classList.remove('opacity-60');
          // Re-render when un-viewed
          const filepath = panel.getAttribute('data-file');
          const diffString = diffData[filepath];
          if (diffString && diffString.trim()) {
            const diff2htmlUi = new Diff2HtmlUI(diffRender, diffString, {
              drawFileList: false,
              matching: 'lines',
              outputFormat: 'side-by-side',
              colorScheme: 'dark'
            });
            diff2htmlUi.draw();
          } else {
            diffRender.innerHTML = '<div class="italic opacity-50 p-4">No diff available (new file or binary)</div>';
          }
          diffRender.dataset.rendered = "true";
          viewedCount--;
        }
        updateProgress();
      } else if (e.target.classList.contains('action-select')) {
        const panel = e.target.closest('.file-panel');
        const checkbox = panel.querySelector('.viewed-checkbox');
        const filepath = panel.getAttribute('data-file');
        const action = e.target.value;

        // Auto-mark as viewed when an action is selected
        if (action !== 'none') {
          if (!checkbox.checked) {
            checkbox.checked = true;
            // Manually trigger the change event logic
            const diffOuter = panel.querySelector('.diff-container');
            const diffRender = panel.querySelector('.diff-render');
            diffOuter.classList.add('hidden');
            panel.classList.add('opacity-60');
            diffRender.innerHTML = '';
            diffRender.dataset.rendered = "false";
            viewedCount++;
            updateProgress();
          }

          // Queue prompt for the agent to execute
          let promptStr = "";
          let labelText = "";
          if (action === "add") {
            promptStr = `chezmoi add ~/${filepath}`;
            labelText = `Keep Local: ${filepath}`;
          } else if (action === "revert") {
            promptStr = `chezmoi apply --force ~/${filepath}`;
            labelText = `Revert: ${filepath}`;
          }

          if (promptStr && window.lavish && window.lavish.queuePrompt) {
            window.lavish.queuePrompt(promptStr, {
              tag: 'action',
              text: labelText,
              queueKey: filepath, // Replaces previous choice for this file
              data: { file: filepath, action: action }
            });
          }
        }
      }
    });

    // Lazily render diffs using IntersectionObserver
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const container = entry.target;
          if (container.dataset.rendered !== "true" && !container.closest('.file-panel').querySelector('.viewed-checkbox').checked) {
            const filepath = container.closest('.file-panel').getAttribute('data-file');
            const diffString = diffData[filepath];

            if (diffString && diffString.trim()) {
              // Yield to main thread
              setTimeout(() => {
                // Ensure container is still visible and not checked
                if (container.closest('.file-panel').querySelector('.viewed-checkbox').checked) return;
                const diff2htmlUi = new Diff2HtmlUI(container, diffString, {
                  drawFileList: false,
                  matching: 'lines',
                  outputFormat: 'side-by-side',
                  colorScheme: 'dark'
                });
                diff2htmlUi.draw();
              }, 10);
            } else {
               container.innerHTML = '<div class="italic opacity-50 p-4">No diff available (new file or binary)</div>';
            }
            container.dataset.rendered = "true";
          }
        }
      });
    }, { rootMargin: "800px 0px" });

    panels.forEach(panel => {
      const container = panel.querySelector('.diff-render');
      observer.observe(container);
    });
  });

  function openReviewModal() {
    const output = [];
    output.push("#!/usr/bin/env bash");
    output.push("# Generated by Chezmoi Diff Review\\n");

    let adds = [];
    let reverts = [];

    document.querySelectorAll('.file-panel').forEach(panel => {
      const filepath = panel.getAttribute('data-file');
      const action = panel.querySelector('.action-select').value;
      if (action === 'add') adds.push(filepath);
      if (action === 'revert') reverts.push(filepath);
    });

    if (adds.length > 0) {
      output.push("# --- Apply Local Changes (Keep Local, Add to Chezmoi) ---");
      adds.forEach(f => {
        output.push(`chezmoi add ~/${f}`);
      });
      output.push("");
    }

    if (reverts.length > 0) {
      output.push("# --- Revert to Chezmoi Source (Discard Local Changes) ---");
      reverts.forEach(f => {
        output.push(`chezmoi apply --force ~/${f}`);
      });
    }

    if (adds.length === 0 && reverts.length === 0) {
      output.push("# No actions selected. Select 'Keep Local' or 'Revert' on some files.");
    }

    document.getElementById('script-output').value = output.join("\\n");
    document.getElementById('review_modal').showModal();
  }

  function copyScript() {
    const text = document.getElementById('script-output').value;
    navigator.clipboard.writeText(text).then(() => {
      alert("Copied to clipboard!");
    }).catch(err => {
      alert("Failed to copy! You can select the text manually.");
    });
  }
</script>
</body>
</html>
"""

    safe_diffs = json.dumps(diffs).replace("</script>", "<\\/script>")
    html_out = html_template.replace("__FILE_PANELS__", "\n".join(file_panels)).replace(
        "__DIFF_JSON__", safe_diffs
    )

    out_path = os.path.join(tempfile.gettempdir(), "chezmoi-review.html")
    try:
        with open(out_path, "w") as f:
            f.write(html_out)
        print(f"\n\033[1;32m✓ Generated interactive review artifact at {out_path}\033[0m")
        print("\033[1mTo open the review UI, run:\033[0m")
        print(f"  npx -y lavish-axi {out_path}\n")
    except Exception as e:
        sys.exit(f"Failed to write output to {out_path}: {e}")


if __name__ == "__main__":
    main()
