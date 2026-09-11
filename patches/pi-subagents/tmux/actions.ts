import { execFile, type ExecFileOptionsWithStringEncoding } from "node:child_process";
import * as fs from "node:fs";
import * as path from "node:path";
import type { AgentToolResult } from "@earendil-works/pi-agent-core";
import { writeAtomicJson } from "../../shared/atomic-json.ts";
import type { Details } from "../../shared/types.ts";
import type { InspectorContext, InspectorLaunch, InspectorParams, InspectorTarget } from "../types.ts";

export interface TmuxInspectorBinding {
	schemaVersion: 1;
	kind: "tmux-inspector";
	runId: string;
	asyncDir: string;
	childIndex?: number;
	missionId?: string;
	missionPath?: string;
	windowId?: string;
	paneId: string;
	outputPaneId?: string;
	openedAt: string;
	lastFocusedAt?: string;
	command: string;
}

export function bindingPath(asyncDir: string, index?: number): string {
	return path.join(asyncDir, "inspectors", `tmux${index === undefined ? "" : `-${index}`}.json`);
}

function parse(value: unknown): TmuxInspectorBinding | undefined {
	if (!value || typeof value !== "object" || Array.isArray(value)) return undefined;
	const binding = value as Partial<TmuxInspectorBinding>;
	if (
		binding.schemaVersion !== 1 ||
		binding.kind !== "tmux-inspector" ||
		(binding.childIndex !== undefined && (!Number.isInteger(binding.childIndex) || binding.childIndex < 0)) ||
		typeof binding.runId !== "string" ||
		typeof binding.asyncDir !== "string" ||
		typeof binding.paneId !== "string" ||
		typeof binding.openedAt !== "string" ||
		typeof binding.command !== "string"
	)
		return undefined;
	return binding as TmuxInspectorBinding;
}

export function readTmuxInspectorBinding(asyncDir: string, index?: number): TmuxInspectorBinding | undefined {
	try {
		return parse(JSON.parse(fs.readFileSync(bindingPath(asyncDir, index), "utf8")));
	} catch (_err) {
		void _err;
		return undefined;
	}
}

export function readTmuxInspectorBindingForTarget(target: InspectorTarget): TmuxInspectorBinding | undefined {
	const binding = readTmuxInspectorBinding(target.asyncDir, target.index);
	if (!binding || binding.runId !== target.runId || binding.childIndex !== target.index) return undefined;
	try {
		if (fs.realpathSync(binding.asyncDir) !== fs.realpathSync(target.asyncDir)) return undefined;
	} catch (_err) {
		void _err;
		return undefined;
	}
	return binding;
}

function result(text: string, isError = false): AgentToolResult<Details> {
	return {
		content: [{ type: "text", text }],
		...(isError ? { isError: true } : {}),
		details: { mode: "management", results: [] },
	};
}

export type TmuxRunner = (
	args: readonly string[],
	options?: ExecFileOptionsWithStringEncoding,
) => Promise<{ stdout: string; stderr: string }>;

function defaultRunner(
	args: readonly string[],
	options: ExecFileOptionsWithStringEncoding = { encoding: "utf8" },
): Promise<{ stdout: string; stderr: string }> {
	return new Promise((resolve, reject) => {
		execFile("tmux", [...args], options, (error, stdout, stderr) => {
			if (error) {
				const failure = error instanceof Error ? error : new Error(String(error));
				reject(failure);
				return;
			}
			resolve({ stdout: String(stdout), stderr: String(stderr) });
		});
	});
}

async function isWindowAlive(runner: TmuxRunner, windowId: string): Promise<boolean> {
	try {
		const { stdout } = await runner(["list-windows", "-F", "#{window_id}"]);
		return stdout
			.split("\n")
			.map((line) => line.trim())
			.includes(windowId.trim());
	} catch (_err) {
		void _err;
		return false;
	}
}

async function isPaneAlive(runner: TmuxRunner, paneId: string): Promise<boolean> {
	try {
		const { stdout } = await runner(["list-panes", "-a", "-F", "#{pane_id}"]);
		return stdout
			.split("\n")
			.map((line) => line.trim())
			.includes(paneId.trim());
	} catch (_err) {
		void _err;
		return false;
	}
}

export async function openTmuxInspector(
	context: InspectorContext,
	launch: InspectorLaunch,
	params: InspectorParams,
	runner: TmuxRunner = defaultRunner,
): Promise<AgentToolResult<Details>> {
	const existing = readTmuxInspectorBindingForTarget(context.target);
	if (existing) {
		if (existing.windowId && (await isWindowAlive(runner, existing.windowId))) {
			if (params.focus !== false) {
				try {
					await runner(["select-window", "-t", existing.windowId]);
					await runner(["select-pane", "-t", existing.paneId]);
				} catch (_err) {
					void _err;
				}
			}
			return result(
				`Refocused existing read-only tmux inspector window ${existing.windowId} for async run ${context.target.runId}.`,
			);
		}
		if (existing.paneId && (await isPaneAlive(runner, existing.paneId))) {
			if (params.focus !== false) {
				try {
					await runner(["select-pane", "-t", existing.paneId]);
				} catch (_err) {
					void _err;
				}
			}
			return result(
				`Refocused existing read-only tmux inspector pane ${existing.paneId} for async run ${context.target.runId}.`,
			);
		}
	}

	const shortId = context.target.runId.slice(0, 8);
	const windowName = `subagent-${shortId}${context.target.index !== undefined ? `-${context.target.index}` : ""}`;
	const launchCwd = context.target.status.cwd ?? context.cwd;

	const outputPath =
		context.target.index !== undefined
			? path.join(context.target.asyncDir, `output-${context.target.index}.log`)
			: path.join(context.target.asyncDir, "output-0.log");

	const mode =
		context.env.PI_INSPECTOR_TMUX_MODE?.toLowerCase() === "split" ? "split" : "window";

	try {
		let windowId: string | undefined;
		let paneId: string;
		let outputPaneId: string | undefined;

		if (mode === "split") {
			const splitResult = await runner([
				"split-window",
				"-h",
				"-P",
				"-F",
				"#{pane_id}",
				"-c",
				launchCwd,
				launch.displayCommand,
			]);
			paneId = splitResult.stdout.trim();
			if (params.focus !== false) {
				await runner(["select-pane", "-t", paneId]);
			}
		} else {
			const newWinResult = await runner([
				"new-window",
				"-P",
				"-F",
				"#{window_id}:#{pane_id}",
				"-n",
				windowName,
				"-c",
				launchCwd,
				launch.displayCommand,
			]);
			const [wId, pId] = newWinResult.stdout.trim().split(":");
			windowId = wId;
			paneId = pId;

			// Split right pane to show full output stream
			try {
				const outputCmd = `sh -c 'while [ ! -f "${outputPath}" ]; do sleep 0.2; done; less +F "${outputPath}"; exec $SHELL'`;
				const splitResult = await runner([
					"split-window",
					"-h",
					"-P",
					"-F",
					"#{pane_id}",
					"-t",
					windowId,
					"-c",
					launchCwd,
					outputCmd,
				]);
				outputPaneId = splitResult.stdout.trim();
			} catch (_splitErr) {
				void _splitErr;
			}

			// Focus the window directly in front of the user
			if (params.focus !== false) {
				await runner(["select-window", "-t", windowId]);
				await runner(["select-pane", "-t", paneId]);
			}
		}

		const now = (context.now?.() ?? new Date()).toISOString();
		const binding: TmuxInspectorBinding = {
			schemaVersion: 1,
			kind: "tmux-inspector",
			runId: context.target.runId,
			asyncDir: context.target.asyncDir,
			...(context.target.index === undefined ? {} : { childIndex: context.target.index }),
			...(launch.mission ? { missionId: launch.mission.id, missionPath: launch.mission.path } : {}),
			...(windowId ? { windowId } : {}),
			paneId,
			...(outputPaneId ? { outputPaneId } : {}),
			openedAt: now,
			...(params.focus !== false ? { lastFocusedAt: now } : {}),
			command: launch.displayCommand,
		};
		writeAtomicJson(bindingPath(context.target.asyncDir, context.target.index), binding);

		const targetDesc = windowId
			? `window ${windowId} (${windowName})`
			: `pane ${paneId}`;
		const layoutDesc = outputPaneId
			? "Left pane: interactive read-only inspector dashboard. Right pane: full output log viewer (less +F)."
			: "Interactive read-only inspector dashboard.";

		return result(
			`Opened read-only tmux inspector ${targetDesc} for async run ${context.target.runId}.\n${layoutDesc}\nClosing the window/pane does not stop the run.`,
		);
	} catch (cause) {
		const message = cause instanceof Error ? cause.message : String(cause);
		return result(`Tmux inspector error: ${message}`, true);
	}
}

export async function statusTmuxInspector(
	context: InspectorContext,
	runner: TmuxRunner = defaultRunner,
): Promise<AgentToolResult<Details>> {
	const binding = readTmuxInspectorBindingForTarget(context.target);
	if (!binding) {
		return result(
			`No tmux inspector binding exists for async run ${context.target.runId}${context.target.index === undefined ? "" : ` child ${context.target.index}`}.`,
		);
	}
	const alive = binding.windowId
		? await isWindowAlive(runner, binding.windowId)
		: await isPaneAlive(runner, binding.paneId);

	if (!alive) {
		return result(
			`Tmux inspector ${binding.windowId ?? binding.paneId} is no longer running.\nRun state remains authoritative: ${context.target.status.state}.`,
			true,
		);
	}
	return result(
		`Tmux inspector ${binding.windowId ?? binding.paneId} is active for async run ${context.target.runId}.\nRun state: ${context.target.status.state}\nBinding: ${bindingPath(context.target.asyncDir, context.target.index)}`,
	);
}

export async function closeTmuxInspector(
	context: InspectorContext,
	runner: TmuxRunner = defaultRunner,
): Promise<AgentToolResult<Details>> {
	const binding = readTmuxInspectorBindingForTarget(context.target);
	if (!binding) {
		return result(`No tmux inspector binding exists for async run ${context.target.runId}.`);
	}
	try {
		if (binding.windowId) {
			await runner(["kill-window", "-t", binding.windowId]);
		} else {
			await runner(["kill-pane", "-t", binding.paneId]);
		}
	} catch (_err) {
		void _err;
	}
	fs.rmSync(bindingPath(context.target.asyncDir, context.target.index), { force: true });
	return result(
		`Closed tmux inspector ${binding.windowId ?? binding.paneId} for async run ${context.target.runId}. The subagent run was not stopped.`,
	);
}
