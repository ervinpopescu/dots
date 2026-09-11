import type {
	ExtensionAPI,
	ExtensionContext,
} from "@earendil-works/pi-coding-agent";
import { execFile } from "node:child_process";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

interface RunInfo {
	id: string;
	shortId: string;
	asyncDir: string;
	outputFile: string;
	state: string;
	name: string;
	startedAt?: string;
	active: boolean;
	cwd: string;
}

function getAsyncDirRoot(): string {
	const uid = process.getuid ? process.getuid() : "unknown";
	return path.join(
		os.tmpdir(),
		`pi-subagents-uid-${uid}`,
		"async-subagent-runs",
	);
}

function findInspectorRunner(): string | undefined {
	const candidate = path.join(
		os.homedir(),
		".pi/agent/npm/node_modules/pi-subagents/inspector-runner.mjs",
	);
	return fs.existsSync(candidate) ? candidate : undefined;
}

function getAvailableRuns(): RunInfo[] {
	const root = getAsyncDirRoot();
	if (!fs.existsSync(root)) return [];

	const activeDir = path.join(root, ".active-runs");
	const activeIds = new Set<string>();
	if (fs.existsSync(activeDir)) {
		try {
			for (const file of fs.readdirSync(activeDir)) {
				if (!file.startsWith(".") && file !== "tool-calls") {
					activeIds.add(file);
				}
			}
		} catch (_err) {
			void _err;
		}
	}

	const entries = fs.readdirSync(root).filter((f) => !f.startsWith("."));
	const runs: RunInfo[] = [];

	for (const runId of entries) {
		const runDir = path.join(root, runId);
		try {
			if (!fs.statSync(runDir).isDirectory()) continue;
			const statusPath = path.join(runDir, "status.json");
			let state = "unknown";
			let name = "";
			let startedAt: string | undefined;
			let cwd = process.cwd();

			if (fs.existsSync(statusPath)) {
				const status = JSON.parse(fs.readFileSync(statusPath, "utf8"));
				state = status.state || "unknown";
				cwd = status.cwd || cwd;
				if (status.startedAt) {
					startedAt = new Date(status.startedAt).toLocaleTimeString();
				}
				if (status.steps && status.steps[0]) {
					name =
						status.steps[0].sessionName ||
						status.steps[0].agent ||
						status.steps[0].description ||
						"";
				}
			}

			const outputFile = path.join(runDir, "output-0.log");
			runs.push({
				id: runId,
				shortId: runId.slice(0, 8),
				asyncDir: runDir,
				outputFile,
				state,
				name,
				startedAt,
				active: activeIds.has(runId) || state === "running",
				cwd,
			});
		} catch (_err) {
			void _err;
		}
	}

	// Sort active runs first, then newest
	runs.sort((a, b) => {
		if (a.active && !b.active) return -1;
		if (!a.active && b.active) return 1;
		return 0;
	});

	return runs;
}

async function openInTmux(
	run: RunInfo,
	options: { split?: boolean } = {},
): Promise<string> {
	if (!process.env.TMUX) {
		throw new Error("tmux is not running ($TMUX is not set).");
	}

	const runnerPath = findInspectorRunner();
	if (!runnerPath) {
		throw new Error("Could not find pi-subagents/inspector-runner.mjs");
	}

	const windowName = `subagent-${run.shortId}`;

	// Check if a window with this name already exists
	try {
		const { stdout } = await execFileAsync("tmux", [
			"list-windows",
			"-F",
			"#{window_name}:#{window_id}",
		]);
		for (const line of stdout.split("\n")) {
			const [name, wid] = line.trim().split(":");
			if (name === windowName && wid) {
				await execFileAsync("tmux", ["select-window", "-t", wid]);
				return `Switched to existing tmux window ${wid} (${windowName})`;
			}
		}
	} catch (_err) {
		void _err;
	}

	const inspectorCmd = `"${process.execPath}" "${runnerPath}" --async-dir "${run.asyncDir}" --run-id "${run.id}" --allow-steer true --allow-stop true`;
	const outputLogCmd = `sh -c 'while [ ! -f "${run.outputFile}" ]; do sleep 0.2; done; less +F "${run.outputFile}"; exec $SHELL'`;

	if (options.split) {
		// Split current window horizontally
		const { stdout: paneId } = await execFileAsync("tmux", [
			"split-window",
			"-h",
			"-P",
			"-F",
			"#{pane_id}",
			"-c",
			run.cwd,
			inspectorCmd,
		]);
		await execFileAsync("tmux", ["select-pane", "-t", paneId.trim()]);
		return `Opened subagent ${run.shortId} in split pane ${paneId.trim()}`;
	}

	// Create new window
	const { stdout: winOut } = await execFileAsync("tmux", [
		"new-window",
		"-P",
		"-F",
		"#{window_id}",
		"-n",
		windowName,
		"-c",
		run.cwd,
		inspectorCmd,
	]);
	const windowId = winOut.trim();

	// Split right pane to display the full output stream
	try {
		await execFileAsync("tmux", [
			"split-window",
			"-h",
			"-t",
			windowId,
			"-c",
			run.cwd,
			outputLogCmd,
		]);
	} catch (_splitErr) {
		void _splitErr;
	}

	// Focus the window directly in front of the user
	await execFileAsync("tmux", ["select-window", "-t", windowId]);
	await execFileAsync("tmux", ["select-pane", "-t", `${windowId}.1`]);

	return `Opened subagent ${run.shortId} in new window ${windowId} (Left: Read-Only Dashboard, Right: Full Output)`;
}

export default function (pi: ExtensionAPI) {
	const handleInspect = async (
		rawArgs: string,
		ctx: { ui: ExtensionContext["ui"] },
	) => {
		const args = rawArgs.trim();
		const splitMode = args.includes("--split") || args.includes("-s");
		const targetId = args.replace("--split", "").replace("-s", "").trim();

		const runs = getAvailableRuns();
		if (runs.length === 0) {
			ctx.ui.notify("No subagent runs found.", "error");
			return;
		}

		let chosenRun: RunInfo | undefined;

		if (targetId) {
			chosenRun = runs.find(
				(r) =>
					r.id === targetId || r.shortId === targetId || r.id.startsWith(targetId),
			);
			if (!chosenRun) {
				ctx.ui.notify(`No subagent run matching '${targetId}' found.`, "error");
				return;
			}
		} else {
			const activeRuns = runs.filter((r) => r.active);
			if (activeRuns.length === 1) {
				chosenRun = activeRuns[0];
			} else {
				const options = runs.slice(0, 10).map((r) => {
					const badge = r.active ? "● [running]" : "○ [settled]";
					const title = r.name ? ` — ${r.name.slice(0, 45)}` : "";
					return `${badge} ${r.shortId}${title}`;
				});

				const selected = await ctx.ui.select(
					"Select subagent run to inspect in tmux:",
					options,
				);
				if (!selected) return;

				const selectedShortId = selected.split(" ")[1]?.trim();
				chosenRun = runs.find((r) => r.shortId === selectedShortId);
			}
		}

		if (!chosenRun) return;

		try {
			const msg = await openInTmux(chosenRun, { split: splitMode });
			ctx.ui.notify(msg, "info");
		} catch (error) {
			const message = error instanceof Error ? error.message : String(error);
			ctx.ui.notify(`Failed to open tmux inspector: ${message}`, "error");
		}
	};

	pi.registerCommand("subagent-inspect", {
		description:
			"Open subagent in new tmux window/pane with read-only dashboard & full output",
		handler: handleInspect,
	});

	pi.registerCommand("subagent-view", {
		description:
			"Alias for /subagent-inspect: open subagent in tmux with read-only dashboard & full output",
		handler: handleInspect,
	});

	pi.registerShortcut("ctrl+alt+i", {
		description: "Open active subagent in new tmux inspector window",
		handler: async (ctx) => {
			await handleInspect("", ctx);
		},
	});
}
