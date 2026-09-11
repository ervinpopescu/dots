import {
	closeTmuxInspector,
	openTmuxInspector,
	readTmuxInspectorBindingForTarget,
	statusTmuxInspector,
	type TmuxRunner,
} from "./actions.ts";
import type { InspectorPlugin } from "../types.ts";

export interface TmuxPluginDeps {
	runner?: TmuxRunner;
}

export function createTmuxInspectorPlugin(deps: TmuxPluginDeps = {}): InspectorPlugin {
	return {
		name: "tmux",
		available: (context) => Boolean(context.env.TMUX),
		owns: (context) => readTmuxInspectorBindingForTarget(context.target) !== undefined,
		open: (context, launch, params) => openTmuxInspector(context, launch, params, deps.runner),
		status: (context) => statusTmuxInspector(context, deps.runner),
		close: (context) => closeTmuxInspector(context, deps.runner),
	};
}
