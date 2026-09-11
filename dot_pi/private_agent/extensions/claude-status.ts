import type {
	ExtensionAPI,
	ExtensionContext,
} from "@earendil-works/pi-coding-agent";
import { truncateToWidth } from "@earendil-works/pi-tui";
import { execFile } from "node:child_process";
import { readFile } from "node:fs/promises";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

const env =
	(globalThis as { process?: { env?: Record<string, string | undefined> } })
		.process?.env ?? {};
const ANTHROPIC_USAGE_URL =
	env.PI_ANTHROPIC_USAGE_URL || "https://api.anthropic.com/api/oauth/usage";
const CODEX_USAGE_URL =
	env.PI_CODEX_USAGE_URL || "https://chatgpt.com/backend-api/wham/usage";
const GEMINI_CODE_ASSIST_URL =
	env.PI_GEMINI_CODE_ASSIST_URL ||
	"https://cloudcode-pa.googleapis.com/v1internal";
const GEMINI_OAUTH_TOKEN_URL =
	env.PI_GEMINI_OAUTH_TOKEN_URL || "https://oauth2.googleapis.com/token";
const GEMINI_OAUTH_CLIENT_ID = env.PI_GEMINI_OAUTH_CLIENT_ID;
const GEMINI_OAUTH_CLIENT_SECRET = env.PI_GEMINI_OAUTH_CLIENT_SECRET;
const OPENAI_AUTH_CLAIM = "https://api.openai.com/auth";
const RESET_TICK_MS = 60_000;
const USAGE_POLL_MS = 300_000;

type RenderRequester = { requestRender(): void };

type UsageWindow = {
	label: string;
	remainingPercent: number;
	resetsAt?: number;
};

type UsageLimit = {
	name?: string;
	windows: UsageWindow[];
};

function isRecord(value: unknown): value is Record<string, unknown> {
	return typeof value === "object" && value !== null && !Array.isArray(value);
}

function clampPercent(value: number): number {
	return Math.min(100, Math.max(0, value));
}

function parseResetAt(value: unknown): number | undefined {
	if (typeof value === "number" && Number.isFinite(value)) {
		return value > 1_000_000_000_000 ? value : value * 1_000;
	}
	if (typeof value !== "string") return undefined;
	const parsed = Date.parse(value);
	return Number.isFinite(parsed) ? parsed : undefined;
}

function formatWindowLabel(seconds?: number, fallback = "limit"): string {
	if (!seconds) return fallback.charAt(0);
	if (Math.abs(seconds - 604_800) < 60) return "w";
	if (Math.abs(seconds - 86_400) < 60) return "d";
	if (Math.abs(seconds - 2_592_000) < 60) return "mo";
	if (Math.abs(seconds - 31_536_000) < 60) return "y";
	if (seconds >= 86_400) return `${Math.round(seconds / 86_400)}d`;
	if (seconds >= 3_600) return `${Math.round(seconds / 3_600)}h`;
	return `${Math.max(1, Math.round(seconds / 60))}m`;
}

function formatResetTimer(resetsAt?: number): string | undefined {
	if (!resetsAt) return undefined;
	const minutes = Math.max(0, Math.ceil((resetsAt - Date.now()) / 60_000));
	if (minutes === 0) return "now";
	if (minutes < 60) return `${minutes}m`;
	const hours = Math.ceil(minutes / 60);
	if (hours < 24) return `${hours}h`;
	const days = Math.floor(hours / 24);
	const remainingHours = hours % 24;
	if (days < 7 && remainingHours > 0) return `${days}d${remainingHours}h`;
	return `${Math.ceil(hours / 24)}d`;
}

function formatLimitName(name?: string): string | undefined {
	if (!name) return undefined;
	if (/spark|bengalfox/i.test(name)) return "spark";
	return name
		.replace(/^codex[-_]?/i, "")
		.replace(/^gpt[-_]?/i, "gpt-")
		.replace(/[_\s]+/g, "-")
		.toLowerCase();
}

function parseCodexWindow(
	value: unknown,
	fallback: string,
): UsageWindow | undefined {
	if (!isRecord(value) || typeof value.used_percent !== "number")
		return undefined;
	const seconds =
		typeof value.limit_window_seconds === "number"
			? value.limit_window_seconds
			: undefined;
	return {
		label: formatWindowLabel(seconds, fallback),
		remainingPercent: 100 - clampPercent(value.used_percent),
		resetsAt: parseResetAt(value.reset_at),
	};
}

function parseCodexLimit(
	value: unknown,
	name?: string,
): UsageLimit | undefined {
	if (!isRecord(value)) return undefined;
	const windows = [
		parseCodexWindow(value.primary_window, "primary"),
		parseCodexWindow(value.secondary_window, "secondary"),
	].filter((window): window is UsageWindow => Boolean(window));
	return windows.length > 0 ? { name, windows } : undefined;
}

function parseCodexUsage(value: unknown): UsageLimit[] {
	if (!isRecord(value)) return [];
	const limits: UsageLimit[] = [];
	const main = parseCodexLimit(value.rate_limit);
	if (main) limits.push(main);
	if (Array.isArray(value.additional_rate_limits)) {
		for (const item of value.additional_rate_limits) {
			if (!isRecord(item)) continue;
			const name =
				typeof item.limit_name === "string" ? item.limit_name : undefined;
			const limit = parseCodexLimit(item.rate_limit, name);
			if (limit) limits.push(limit);
		}
	}
	return limits;
}

function parseClaudeUsage(value: unknown): UsageLimit[] {
	if (!isRecord(value)) return [];
	const buckets = [
		["five_hour", "5h", undefined],
		["seven_day", "w", undefined],
		["seven_day_opus", "w", "opus"],
		["seven_day_sonnet", "w", "sonnet"],
	] as const;
	const limits: UsageLimit[] = [];
	for (const [key, label, name] of buckets) {
		const bucket = value[key];
		if (!isRecord(bucket) || typeof bucket.utilization !== "number") continue;
		limits.push({
			name,
			windows: [
				{
					label,
					remainingPercent: 100 - clampPercent(bucket.utilization),
					resetsAt: parseResetAt(bucket.resets_at),
				},
			],
		});
	}
	return limits;
}

function parseGeminiUsage(value: unknown, activeModel: string): UsageLimit[] {
	if (!isRecord(value) || !Array.isArray(value.buckets)) return [];
	const buckets = value.buckets.filter(
		(bucket): bucket is Record<string, unknown> =>
			isRecord(bucket) && typeof bucket.remainingFraction === "number",
	);
	if (buckets.length === 0) return [];
	const normalizedModel = activeModel.toLowerCase().replace(/^models\//, "");
	const matching = buckets.filter((bucket) => {
		const model =
			typeof bucket.modelId === "string" ? bucket.modelId.toLowerCase() : "";
		return (
			model === normalizedModel ||
			model.includes(normalizedModel) ||
			normalizedModel.includes(model)
		);
	});
	const candidates = matching.length > 0 ? matching : buckets;
	const bucket = candidates.reduce((lowest, candidate) =>
		(candidate.remainingFraction as number) < (lowest.remainingFraction as number)
			? candidate
			: lowest,
	);
	return [
		{
			windows: [
				{
					label: "d",
					remainingPercent: clampPercent((bucket.remainingFraction as number) * 100),
					resetsAt: parseResetAt(bucket.resetTime),
				},
			],
		},
	];
}

function extractAccountId(accessToken: string): string | undefined {
	try {
		const parts = accessToken.split(".");
		if (parts.length !== 3) return undefined;
		const encoded = parts[1].replace(/-/g, "+").replace(/_/g, "/");
		const payload = JSON.parse(
			atob(encoded.padEnd(Math.ceil(encoded.length / 4) * 4, "=")),
		);
		if (!isRecord(payload) || !isRecord(payload[OPENAI_AUTH_CLAIM]))
			return undefined;
		const accountId = payload[OPENAI_AUTH_CLAIM].chatgpt_account_id;
		return typeof accountId === "string" ? accountId : undefined;
	} catch {
		return undefined;
	}
}

export default function (pi: ExtensionAPI) {
	let providerUsage: UsageLimit[] = [];
	let gitDiff = "";
	let refreshProviderUsage: ((ctx: ExtensionContext) => void) | undefined;
	let activeModel: ExtensionContext["model"];
	let footerTui: RenderRequester | undefined;
	let usageRequest: Promise<void> | undefined;
	let usageRequestProvider: string | undefined;
	let geminiProjectId: string | undefined;
	let geminiTokenCache: { accessToken: string; expiresAt: number } | undefined;

	function setProviderUsage(usage: UsageLimit[], tui: RenderRequester) {
		if (JSON.stringify(providerUsage) !== JSON.stringify(usage)) {
			providerUsage = usage;
		}
		tui.requestRender();
	}

	async function fetchJson(
		url: string,
		init: RequestInit,
	): Promise<unknown | undefined> {
		const controller = new AbortController();
		const timeout = setTimeout(() => controller.abort(), 10_000);
		try {
			const response = await fetch(url, { ...init, signal: controller.signal });
			return response.ok ? response.json() : undefined;
		} finally {
			clearTimeout(timeout);
		}
	}

	function claudeAccessToken(value: unknown): string | undefined {
		if (!isRecord(value) || !isRecord(value.claudeAiOauth)) return undefined;
		const token = value.claudeAiOauth.accessToken;
		return typeof token === "string" ? token : undefined;
	}

	async function getClaudeTokenCandidates(
		ctx: ExtensionContext,
	): Promise<string[]> {
		const tokens: string[] = [];
		if (env.PI_CLAUDE_OAUTH_TOKEN) tokens.push(env.PI_CLAUDE_OAUTH_TOKEN);
		try {
			const providerAuth = await ctx.modelRegistry.getProviderAuth("anthropic");
			const providerToken = providerAuth?.auth.apiKey;
			if (providerToken?.startsWith("sk-ant-oat")) tokens.push(providerToken);
		} catch {
			// Fall back to the Claude Code login below.
		}

		if (env.HOME) {
			try {
				const credentials = JSON.parse(
					await readFile(`${env.HOME}/.claude/.credentials.json`, "utf8"),
				);
				const token = claudeAccessToken(credentials);
				if (token) tokens.push(token);
			} catch {
				// Claude Code commonly stores credentials in the macOS keychain instead.
			}
		}

		try {
			const { stdout } = await execFileAsync(
				"security",
				["find-generic-password", "-s", "Claude Code-credentials", "-w"],
				{ encoding: "utf8", timeout: 3_000 },
			);
			const token = claudeAccessToken(JSON.parse(stdout));
			if (token) tokens.push(token);
		} catch {
			// The security command is only available on macOS.
		}

		return [...new Set(tokens)];
	}

	async function fetchCodexUsage(
		ctx: ExtensionContext,
	): Promise<UsageLimit[] | undefined> {
		const providerAuth = await ctx.modelRegistry.getProviderAuth("openai-codex");
		const accessToken = providerAuth?.auth.apiKey;
		if (!accessToken) return [];
		const accountId = extractAccountId(accessToken);
		const payload = await fetchJson(CODEX_USAGE_URL, {
			headers: {
				Accept: "application/json",
				Authorization: `Bearer ${accessToken}`,
				...(accountId ? { "ChatGPT-Account-Id": accountId } : {}),
				originator: "pi",
			},
		});
		return payload === undefined ? undefined : parseCodexUsage(payload);
	}

	async function fetchClaudeUsage(
		ctx: ExtensionContext,
	): Promise<UsageLimit[] | undefined> {
		const tokens = await getClaudeTokenCandidates(ctx);
		if (tokens.length === 0) return [];
		for (const accessToken of tokens) {
			const payload = await fetchJson(ANTHROPIC_USAGE_URL, {
				headers: {
					Accept: "application/json",
					Authorization: `Bearer ${accessToken}`,
					"anthropic-beta": "oauth-2025-04-20",
					"User-Agent": "pi-statusline/1.0",
				},
			});
			if (payload !== undefined) return parseClaudeUsage(payload);
		}
		return undefined;
	}

	async function getGeminiAccessToken(): Promise<string | undefined> {
		if (env.PI_GEMINI_OAUTH_TOKEN) return env.PI_GEMINI_OAUTH_TOKEN;
		if (geminiTokenCache && geminiTokenCache.expiresAt > Date.now() + 30_000) {
			return geminiTokenCache.accessToken;
		}
		if (!env.HOME) return undefined;

		let credentials: unknown;
		try {
			credentials = JSON.parse(
				await readFile(`${env.HOME}/.gemini/oauth_creds.json`, "utf8"),
			);
		} catch {
			return undefined;
		}
		if (!isRecord(credentials)) return undefined;
		const accessToken = credentials.access_token;
		const expiresAt = credentials.expiry_date;
		if (
			typeof accessToken === "string" &&
			typeof expiresAt === "number" &&
			expiresAt > Date.now() + 30_000
		) {
			return accessToken;
		}
		if (typeof credentials.refresh_token !== "string") return undefined;
		if (!GEMINI_OAUTH_CLIENT_ID || !GEMINI_OAUTH_CLIENT_SECRET) {
			return undefined;
		}

		const payload = await fetchJson(GEMINI_OAUTH_TOKEN_URL, {
			method: "POST",
			headers: { "Content-Type": "application/x-www-form-urlencoded" },
			body: new URLSearchParams({
				client_id: GEMINI_OAUTH_CLIENT_ID,
				client_secret: GEMINI_OAUTH_CLIENT_SECRET,
				grant_type: "refresh_token",
				refresh_token: credentials.refresh_token,
			}),
		});
		if (!isRecord(payload) || typeof payload.access_token !== "string") {
			return undefined;
		}
		const expiresIn =
			typeof payload.expires_in === "number" ? payload.expires_in : 3_600;
		geminiTokenCache = {
			accessToken: payload.access_token,
			expiresAt: Date.now() + expiresIn * 1_000,
		};
		return geminiTokenCache.accessToken;
	}

	async function fetchGeminiUsage(
		ctx: ExtensionContext,
	): Promise<UsageLimit[] | undefined> {
		const accessToken = await getGeminiAccessToken();
		if (!accessToken) return [];
		const headers = {
			Authorization: `Bearer ${accessToken}`,
			"Content-Type": "application/json",
		};
		geminiProjectId ??= env.GOOGLE_CLOUD_PROJECT || env.GOOGLE_CLOUD_PROJECT_ID;
		if (!geminiProjectId) {
			const setup = await fetchJson(`${GEMINI_CODE_ASSIST_URL}:loadCodeAssist`, {
				method: "POST",
				headers,
				body: JSON.stringify({
					metadata: {
						ideType: "IDE_UNSPECIFIED",
						platform: "PLATFORM_UNSPECIFIED",
						pluginType: "GEMINI",
					},
				}),
			});
			if (isRecord(setup) && typeof setup.cloudaicompanionProject === "string") {
				geminiProjectId = setup.cloudaicompanionProject;
			}
		}
		if (!geminiProjectId) return [];

		const payload = await fetchJson(
			`${GEMINI_CODE_ASSIST_URL}:retrieveUserQuota`,
			{
				method: "POST",
				headers,
				body: JSON.stringify({ project: geminiProjectId }),
			},
		);
		return payload === undefined
			? undefined
			: parseGeminiUsage(payload, ctx.model?.id || "");
	}

	async function fetchProviderUsage(
		ctx: ExtensionContext,
	): Promise<UsageLimit[] | undefined> {
		switch (ctx.model?.provider) {
			case "openai-codex":
				return fetchCodexUsage(ctx);
			case "anthropic":
				return fetchClaudeUsage(ctx);
			case "google":
				return fetchGeminiUsage(ctx);
			default:
				return [];
		}
	}

	async function updateProviderUsage(
		ctx: ExtensionContext,
		tui: RenderRequester,
	) {
		const provider = ctx.model?.provider;
		if (
			!provider ||
			!["openai-codex", "anthropic", "google"].includes(provider)
		) {
			setProviderUsage([], tui);
			return;
		}
		if (usageRequest) {
			if (usageRequestProvider === provider) return usageRequest;
			await usageRequest;
			return updateProviderUsage(ctx, tui);
		}

		usageRequestProvider = provider;
		usageRequest = (async () => {
			try {
				const usage = await fetchProviderUsage(ctx);
				if (usage !== undefined && ctx.model?.provider === provider) {
					setProviderUsage(usage, tui);
				}
			} catch {
				// Keep the last successful snapshot during transient auth or network failures.
			}
		})().finally(() => {
			usageRequest = undefined;
			usageRequestProvider = undefined;
		});
		return usageRequest;
	}

	async function updateGitDiff(cwd: string, tui: RenderRequester) {
		try {
			const { code, stdout } = await pi.exec(
				"git",
				["--no-optional-locks", "diff", "--shortstat"],
				{ cwd, timeout: 3_000 },
			);
			if (code !== 0) throw new Error("git diff failed");

			let insertions = 0;
			let deletions = 0;
			const insMatch = stdout.match(/(\d+) insertion/);
			const delMatch = stdout.match(/(\d+) deletion/);
			if (insMatch) insertions = parseInt(insMatch[1], 10);
			if (delMatch) deletions = parseInt(delMatch[1], 10);

			let newDiff = "";
			if (insertions > 0 || deletions > 0) {
				newDiff = ` \x1b[32m+${insertions}\x1b[0m \x1b[31m-${deletions}\x1b[0m`;
			}

			if (gitDiff !== newDiff) {
				gitDiff = newDiff;
				tui.requestRender();
			}
		} catch {
			if (gitDiff !== "") {
				gitDiff = "";
				tui.requestRender();
			}
		}
	}

	function fishPath(fullPath: string): string {
		const home = env.HOME || "";
		let p = fullPath;
		if (home && p.startsWith(home)) {
			p = "~" + p.slice(home.length);
		}
		const parts = p.split("/");
		const result = [];
		for (let i = 0; i < parts.length - 1; i++) {
			if (parts[i] === "") result.push("");
			else if (parts[i] === "~") result.push("~");
			else result.push(parts[i].charAt(0));
		}
		result.push(parts[parts.length - 1]);
		return result.join("/");
	}

	function getSessionTime(ctx: ExtensionContext): string {
		// We can just rely on the ctx.sessionManager's first entry
		try {
			const entries = ctx.sessionManager.getEntries();
			if (entries && entries.length > 0) {
				const firstEntry = entries[0];
				if (firstEntry.timestamp) {
					// firstEntry.timestamp is a Date object or ISO string in memory
					const startMs = new Date(firstEntry.timestamp).getTime();
					const elapsedMs = Date.now() - startMs;
					const h = Math.floor(elapsedMs / 3600000);
					const m = Math.floor((elapsedMs % 3600000) / 60000);
					return h > 0 ? `${h}h${m.toString().padStart(2, "0")}m` : `${m}m`;
				}
			}
		} catch {
			return "?m";
		}

		return "?m";
	}

	pi.on("model_select", (event, ctx) => {
		// The context captured by the footer at session_start can retain the
		// previous model. Use the event model so model-specific values such as
		// contextWindow update immediately after a model switch.
		activeModel = event.model;
		footerTui?.requestRender();
		refreshProviderUsage?.(ctx);
	});

	pi.on("session_start", (_event, ctx) => {
		activeModel = ctx.model;
		let diffTimer: ReturnType<typeof setInterval> | undefined;
		let resetTimer: ReturnType<typeof setInterval> | undefined;
		let startupUsageTimer: ReturnType<typeof setTimeout> | undefined;
		let usageTimer: ReturnType<typeof setInterval> | undefined;

		ctx.ui.setFooter((tui, _theme, footerData) => {
			footerTui = tui;
			updateGitDiff(ctx.cwd, tui);
			diffTimer = setInterval(() => {
				updateGitDiff(ctx.cwd, tui);
			}, 5_000);

			refreshProviderUsage = (currentCtx) => {
				void updateProviderUsage(currentCtx, tui);
			};
			refreshProviderUsage(ctx);
			startupUsageTimer = setTimeout(() => refreshProviderUsage?.(ctx), 1_000);
			resetTimer = setInterval(() => tui.requestRender(), RESET_TICK_MS);
			usageTimer = setInterval(() => {
				refreshProviderUsage?.(ctx);
			}, USAGE_POLL_MS);

			const unsubBranch = footerData.onBranchChange(() => {
				updateGitDiff(ctx.cwd, tui);
				tui.requestRender();
			});

			return {
				dispose: () => {
					unsubBranch();
					if (footerTui === tui) footerTui = undefined;
					if (diffTimer) clearInterval(diffTimer);
					if (resetTimer) clearInterval(resetTimer);
					if (startupUsageTimer) clearTimeout(startupUsageTimer);
					if (usageTimer) clearInterval(usageTimer);
					refreshProviderUsage = undefined;
				},
				invalidate() {},
				render(width: number): string[] {
					// Calculate usage stats
					let input = 0,
						output = 0,
						cacheRead = 0,
						cacheWrite = 0,
						cost = 0;
					let latestPromptTokens = 0;
					for (const e of ctx.sessionManager.getEntries()) {
						if (e.type === "message" && e.message.role === "assistant") {
							const messageUsage = e.message.usage;
							input += messageUsage.input || 0;
							output += messageUsage.output || 0;
							cacheRead += messageUsage.cacheRead || 0;
							cacheWrite += messageUsage.cacheWrite || 0;
							cost += messageUsage.cost?.total || 0;
							latestPromptTokens =
								(messageUsage.input || 0) +
								(messageUsage.cacheRead || 0) +
								(messageUsage.cacheWrite || 0);
						} else if (
							(e.type === "branch_summary" || e.type === "compaction") &&
							e.usage
						) {
							input += e.usage.input || 0;
							output += e.usage.output || 0;
							cacheRead += e.usage.cacheRead || 0;
							cacheWrite += e.usage.cacheWrite || 0;
							cost += e.usage.cost?.total || 0;
						} else if (
							e.type === "message" &&
							e.message.role === "toolResult" &&
							e.message.usage
						) {
							const messageUsage = e.message.usage;
							input += messageUsage.input || 0;
							output += messageUsage.output || 0;
							cacheRead += messageUsage.cacheRead || 0;
							cacheWrite += messageUsage.cacheWrite || 0;
							cost += messageUsage.cost?.total || 0;
						}
					}

					const fmt = (n: number) => {
						if (n < 1000) return `${n}`;
						if (n < 10000) return `${(n / 1000).toFixed(1)}k`;
						return `${Math.round(n / 1000)}k`;
					};

					const parts: string[] = [];
					const cyan = "\x1b[36m",
						bold = "\x1b[1m",
						reset = "\x1b[0m",
						dim = "\x1b[2m",
						white = "\x1b[37m";
					const green = "\x1b[32m",
						yellow = "\x1b[33m",
						red = "\x1b[31m",
						magenta = "\x1b[35m",
						blue = "\x1b[34m";

					// Model & Effort
					const model = activeModel ?? ctx.model;
					const modelId = model?.id || "no-model";
					const effort = ctx.thinkingLevel || env.PI_REASONING_LEVEL || "default";

					if (effort && effort !== "off") {
						parts.push(`${bold}${cyan}${modelId}${reset}${dim}[${effort}]${reset}`);
					} else {
						parts.push(`${bold}${cyan}${modelId}${reset}`);
					}

					// Tokens
					let tokensStr = `↑${fmt(input)}`;
					if (output > 0) tokensStr += ` ↓${fmt(output)}`;
					if (cacheRead > 0) tokensStr += ` R${fmt(cacheRead)}`;
					if (cacheWrite > 0) tokensStr += ` W${fmt(cacheWrite)}`;
					parts.push(`${dim}${tokensStr}${reset}`);

					// Context
					const contextWindow = model?.contextWindow || 0;
					if (contextWindow > 0) {
						// Using context limit calculation
						const pct = Math.round((latestPromptTokens / contextWindow) * 100);
						let color = green;
						if (pct >= 80) color = red;
						else if (pct >= 50) color = yellow;

						const fmtMax = (n: number) => {
							if (n < 1000) return `${n}`;
							if (n < 1000000) return `${Math.round(n / 1000)}k`;
							return `${(n / 1000000).toFixed(1)}M`;
						};

						// Adding a space before the slash for readability
						parts.push(`ctx:${color}${pct}%${reset} / ${fmtMax(contextWindow)}`);
					}

					// Provider subscription limits
					const limitParts: string[] = [];
					for (const limit of providerUsage) {
						const limitName = formatLimitName(limit.name);
						for (const window of limit.windows) {
							const remaining = Math.round(window.remainingPercent);
							const color = remaining <= 20 ? red : remaining <= 50 ? yellow : green;
							const prefix = limitName ? `${limitName}/` : "";
							const resetTimer = formatResetTimer(window.resetsAt);
							const resetText = resetTimer ? `${dim}↻${resetTimer}${reset}` : "";
							limitParts.push(
								`${prefix}${window.label}:${color}${remaining}%${reset}${resetText}`,
							);
						}
					}
					if (limitParts.length > 0) {
						parts.push(limitParts.join(" "));
					}

					// Cost
					if (cost > 0) {
						parts.push(`${dim}${white}$${cost.toFixed(3)}${reset}`);
					}

					// Time
					parts.push(`${dim}${white}${getSessionTime(ctx)}${reset}`);

					// Git branch
					const branch = footerData.getGitBranch();
					if (branch) {
						parts.push(`${magenta}${branch}${reset}${gitDiff}`);
					}

					// Path
					const shortPath = fishPath(ctx.cwd);
					parts.push(`${blue}${shortPath}${reset}`);

					const sep = ` ${dim}|${reset} `;
					const line = parts.join(sep);

					// Truncate to terminal width with ansi support
					return [truncateToWidth(line, width, dim + "..." + reset)];
				},
			};
		});
	});
}
