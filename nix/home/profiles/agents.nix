{
  config,
  lib,
  pkgs,
  profile,
  ...
}:
let
  piPackage = lib.attrByPath [ "pi-coding-agent" ] null pkgs;
  agentPackages = builtins.filter (package: package != null) (
    map (name: lib.attrByPath [ name ] null pkgs) [
      "aicommits"
      "claude-code"
      "gemini-cli"
    ]
  );

  piAgentSettings = {
    autocompleteMaxVisible = 15;
    collapseChangelog = true;
    defaultModel = if profile == "cloudtop" then "gemini-3.6-flash" else "gpt-5.6-luna";
    defaultProvider = if profile == "cloudtop" then "google" else "openai-codex";
    defaultThinkingLevel = "high";
    hideThinkingBlock = true;
    lastChangelogVersion = "0.84.2";
    packages = [
      "npm:pi-mcp-adapter"
      "npm:pi-subagents"
      "npm:pi-web-access"
      "npm:context-mode"
      "npm:pi-lens"
      "npm:@narumitw/pi-plan-mode"
      "npm:pi-add-dir"
      "npm:pi-interactive-shell"
      "npm:@trevonistrevon/pi-loop"
    ];
    quietStartup = true;
    theme = "dark";
  };

  claudeStatusline = pkgs.writeText "claude-statusline.sh" (
    lib.replaceStrings
      [
        "{{ if not .is_linux -}}"
        "{{- else -}}"
        "{{ end }}"
      ]
      [
        "if [ \"$(uname -s)\" = \"Darwin\" ]; then"
        "else"
        "fi"
      ]
      (builtins.readFile ../../../dot_claude/executable_statusline.sh.tmpl)
  );
in
{
  home.packages = agentPackages;

  home.file = {
    ".agents/AGENTS.md".source = ../../../dot_agents/AGENTS.md;
    ".agents/skills/parallel-review-fix-swarm".source =
      ../../../dot_agents/skills/parallel-review-fix-swarm;
    ".claude/CLAUDE.md".source = ../../../dot_agents/AGENTS.md;
    ".claude/statusline.sh" = {
      source = claudeStatusline;
      executable = true;
    };
    ".gemini/GEMINI.md".source = ../../../dot_agents/AGENTS.md;
    ".pi/agent/extensions/claude-status.ts".source = ../../../dot_pi/agent/extensions/claude-status.ts;
    ".pi/settings.json".text = builtins.toJSON {
      defaultModel = if profile == "cloudtop" then "gemini-3.1-pro-preview" else "gpt-5.6-luna";
      defaultProvider = if profile == "cloudtop" then "google" else "openai-codex";
      defaultThinkingLevel = "high";
    };
    ".gemini/settings.json".text = builtins.toJSON {
      security.auth.selectedType = "gemini-api-key";
      general = {
        previewFeatures = true;
        vimMode = true;
        enablePromptCompletion = true;
        sessionRetention = {
          enabled = true;
          warningAcknowledged = true;
          maxAge = "30d";
        };
        enableAutoUpdate = false;
        preferredEditor = "nvim";
        plan.enabled = true;
      };
      ui = {
        dynamicWindowTitle = false;
        hideBanner = true;
        showMemoryUsage = true;
        showLineNumbers = false;
        hideWindowTitle = true;
        useBackgroundColor = false;
        hideTips = true;
        footer = {
          showLabels = true;
          items = [
            "workspace"
            "git-branch"
            "model-name"
            "context-used"
            "quota"
            "memory-usage"
            "session-id"
            "code-changes"
            "token-count"
          ];
        };
        showModelInfoInChat = true;
        autoThemeSwitching = false;
      };
      tools.shell.showColor = true;
      experimental.modelSteering = true;
      model = {
        compressionThreshold = 0.6;
        name = "gemini-3.1-pro-preview-customtools";
      };
      agents.overrides = { };
      mcpServers = {
        rust-analyzer = {
          command = "rust-analyzer-mcp";
          args = [ ];
        };
        google-workspace = {
          command = "node";
          args = [
            "${config.home.homeDirectory}/.gemini/extensions/google-workspace/workspace-server/dist/index.js"
          ];
        };
      };
      context.fileName = [
        "AGENTS.md"
        "GEMINI.md"
      ];
      skills = [ "~/.agents/skills" ];
    };
    ".claude/settings.json" = {
      enable = profile != "cloudtop";
      text = builtins.toJSON {
        agentPushNotifEnabled = true;
        autoDreamEnabled = false;
        effortLevel = "medium";
        enabledPlugins = {
          "claude-md-management@claude-plugins-official" = true;
          "code-review@claude-plugins-official" = true;
          "code-simplifier@claude-plugins-official" = true;
          "commit-commands@claude-plugins-official" = true;
          "feature-dev@claude-plugins-official" = true;
          "frontend-design@claude-plugins-official" = true;
          "lua-lsp@claude-plugins-official" = true;
          "pyright-lsp@claude-plugins-official" = true;
          "rust-analyzer-lsp@claude-plugins-official" = true;
          "security-guidance@claude-plugins-official" = true;
          "skill-creator@claude-plugins-official" = true;
          "superpowers@claude-plugins-official" = true;
        };
        permissions.allow = [ "Bash(git push no-mistakes *)" ];
        env.CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS = "1";
        includeCoAuthoredBy = false;
        inputNeededNotifEnabled = true;
        model = if profile == "cloudtop" then "sonnet[1m]" else "sonnet";
        skipAutoPermissionPrompt = true;
        skipDangerousModePermissionPrompt = true;
        statusLine = {
          command = "bash ${config.home.homeDirectory}/.claude/statusline.sh";
          type = "command";
        };
        tui = "fullscreen";
        voice.enabled = false;
        voice.mode = "hold";
        voiceEnabled = false;
      };
    };
  };

  programs.pi-coding-agent = lib.mkIf (piPackage != null) {
    enable = true;
    package = piPackage;
    extraPackages = with pkgs; [
      fd
      git
      jq
      ripgrep
    ];
    settings = piAgentSettings;
    context = ../../../dot_agents/AGENTS.md;
  };
}
