import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { truncateToWidth, visibleWidth } from "@earendil-works/pi-tui";
import { exec } from "child_process";
import { promisify } from "util";
import fs from "fs";

const execAsync = promisify(exec);

export default function (pi: ExtensionAPI) {
  let gitDiff = "";

  async function updateGitDiff(cwd: string, tui: any) {
    try {
      const { stdout } = await execAsync("git --no-optional-locks diff --shortstat 2>/dev/null", { cwd });
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
    } catch (e) {
      if (gitDiff !== "") {
        gitDiff = "";
        tui.requestRender();
      }
    }
  }

  function fishPath(fullPath: string): string {
    const home = process.env.HOME || "";
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

  function getSessionTime(ctx: any): string {
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
          return h > 0 ? `${h}h${m.toString().padStart(2, '0')}m` : `${m}m`;
        }
      }
    } catch (e) {}

    // Fallback if memory doesn't have it
    try {
      const sessionFile = process.env.PI_SESSION_FILE;
      if (sessionFile) {
        const content = fs.readFileSync(sessionFile, 'utf-8');
        const firstLine = content.split('\n')[0];
        if (firstLine) {
          const entry = JSON.parse(firstLine);
          if (entry.timestamp) {
            const startMs = new Date(entry.timestamp).getTime();
            const elapsedMs = Date.now() - startMs;
            const h = Math.floor(elapsedMs / 3600000);
            const m = Math.floor((elapsedMs % 3600000) / 60000);
            return h > 0 ? `${h}h${m.toString().padStart(2, '0')}m` : `${m}m`;
          }
        }
      }
    } catch (e) {}
    return "?m";
  }

  pi.on("session_start", (_event, ctx) => {
    let diffTimer: any = null;

    ctx.ui.setFooter((tui, theme, footerData) => {
      // Setup git polling
      if (!diffTimer) {
        updateGitDiff(ctx.cwd, tui);
        diffTimer = setInterval(() => {
          updateGitDiff(ctx.cwd, tui);
        }, 5000); // Check every 5s
      }

      const unsubBranch = footerData.onBranchChange(() => {
        updateGitDiff(ctx.cwd, tui);
        tui.requestRender();
      });

      return {
        dispose: () => {
          unsubBranch();
          if (diffTimer) clearInterval(diffTimer);
        },
        invalidate() {},
        render(width: number): string[] {
          // Calculate usage stats
          let input = 0, output = 0, cacheRead = 0, cacheWrite = 0, cost = 0;
          let latestPromptTokens = 0;
          for (const e of ctx.sessionManager.getEntries()) {
            if (e.type === "message" && e.message.role === "assistant" && e.message.usage) {
              input += e.message.usage.input || 0;
              output += e.message.usage.output || 0;
              cacheRead += e.message.usage.cacheRead || 0;
              cacheWrite += e.message.usage.cacheWrite || 0;
              cost += e.message.usage.cost?.total || 0;
              latestPromptTokens = (e.message.usage.input || 0) + (e.message.usage.cacheRead || 0) + (e.message.usage.cacheWrite || 0);
            } else if ((e.type === "branch_summary" || e.type === "compaction") && e.usage) {
              input += e.usage.input || 0;
              output += e.usage.output || 0;
              cacheRead += e.usage.cacheRead || 0;
              cacheWrite += e.usage.cacheWrite || 0;
              cost += e.usage.cost?.total || 0;
            } else if (e.type === "message" && e.message.role === "toolResult" && e.message.usage) {
              input += e.message.usage.input || 0;
              output += e.message.usage.output || 0;
              cacheRead += e.message.usage.cacheRead || 0;
              cacheWrite += e.message.usage.cacheWrite || 0;
              cost += e.message.usage.cost?.total || 0;
            }
          }

          const fmt = (n: number) => {
            if (n < 1000) return `${n}`;
            if (n < 10000) return `${(n / 1000).toFixed(1)}k`;
            return `${Math.round(n / 1000)}k`;
          };

          const parts: string[] = [];
          const cyan = "\x1b[36m", bold = "\x1b[1m", reset = "\x1b[0m", dim = "\x1b[2m", white = "\x1b[37m";
          const green = "\x1b[32m", yellow = "\x1b[33m", red = "\x1b[31m", magenta = "\x1b[35m", blue = "\x1b[34m";

          // Model & Effort
          const model = ctx.model?.id || "no-model";
          const effort = (ctx as any).state?.thinkingLevel || (process.env.PI_REASONING_LEVEL) || "default";

          if (effort && effort !== "off") {
            parts.push(`${bold}${cyan}${model}${reset}${dim}[${effort}]${reset}`);
          } else {
            parts.push(`${bold}${cyan}${model}${reset}`);
          }

          // Tokens
          let tokensStr = `↑${fmt(input)}`;
          if (output > 0) tokensStr += ` ↓${fmt(output)}`;
          if (cacheRead > 0) tokensStr += ` R${fmt(cacheRead)}`;
          if (cacheWrite > 0) tokensStr += ` W${fmt(cacheWrite)}`;
          parts.push(`${dim}${tokensStr}${reset}`);

          // Context
          let contextWindow = ctx.model?.contextWindow || 0;
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
        }
      };
    });
  });
}
