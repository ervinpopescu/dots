{
  description = "Ervin's cross-platform Nix and Home Manager configuration";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    home-manager = {
      url = "github:nix-community/home-manager";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    nix-darwin = {
      url = "github:nix-darwin/nix-darwin";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    system-manager = {
      url = "github:numtide/system-manager";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    sops-nix = {
      url = "github:Mic92/sops-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    inputs@{
      self,
      nixpkgs,
      home-manager,
      nix-darwin,
      system-manager,
      sops-nix,
      ...
    }:
    let
      lib = nixpkgs.lib;
      supportedSystems = [
        "x86_64-linux"
        "aarch64-linux"
        "aarch64-darwin"
      ];

      forAllSystems = f: lib.genAttrs supportedSystems (system: f system);

      pkgsFor =
        system:
        import nixpkgs {
          inherit system;
          config.allowUnfree = true;
        };

      hmToolsFor =
        system:
        import ./nix/lib/home-manager-tools.nix {
          pkgs = pkgsFor system;
          homeManagerPackage = home-manager.packages.${system}.default;
        };

      renderedShellCheckFor =
        system:
        let
          pkgs = pkgsFor system;
          profiles = [
            "aslan"
            "cloudtop"
            "hp"
            "lenovo"
            "macbook"
          ];
          renderedBinSources = lib.concatMap (
            profile:
            builtins.attrValues (
              import ./nix/lib/rendered-bin.nix {
                inherit lib pkgs profile;
              }
            )
          ) profiles;
          renderTemplate =
            profile: name: template:
            let
              capabilities = import ./nix/lib/profiles.nix { inherit profile; };
              templateData = builtins.toJSON {
                is_arch = builtins.elem profile [
                  "aslan"
                  "lenovo"
                ];
                is_linux = capabilities.isLinux;
                is_hetzner = capabilities.isServer;
              };
            in
            pkgs.runCommand "rendered-${name}-${profile}.sh"
              {
                nativeBuildInputs = [ pkgs.chezmoi ];
              }
              ''
                export HOME="$TMPDIR/home"
                export XDG_CACHE_HOME="$TMPDIR/cache"
                mkdir -p "$HOME" "$XDG_CACHE_HOME"
                chezmoi execute-template --no-tty \
                  --source ${./.} \
                  --override-data ${lib.escapeShellArg templateData} \
                  --file ${template} >"$out"
              '';
          renderedSystemDeploySources = map (
            profile: renderTemplate profile "system-deploy" ./run_after_system-deploy.sh.tmpl
          ) (builtins.filter (profile: profile != "macbook") profiles);
          renderedStatuslineSources = map (
            profile: renderTemplate profile "claude-statusline" ./dot_claude/executable_statusline.sh.tmpl
          ) profiles;
          renderedInstallDepsSources = [
            (renderTemplate "aslan" "install-deps" ./run_onchange_install-deps.sh.tmpl)
          ];
          renderedSources =
            renderedBinSources
            ++ renderedSystemDeploySources
            ++ renderedStatuslineSources
            ++ renderedInstallDepsSources;
        in
        pkgs.runCommand "rendered-shell-check" { nativeBuildInputs = [ pkgs.shellcheck ]; } ''
          for source in ${lib.escapeShellArgs (map toString renderedSources)}; do
            shellcheck --severity=warning "$source"
          done
          touch "$out"
        '';

      # Every fixed-path host declares its home path explicitly. Cloudtop instead
      # reads the activating account's existing HOME under --impure.
      mkHome =
        {
          system,
          profile,
          username ? "ervin",
          homeDirectory,
        }:
        let
          hmTools = hmToolsFor system;
        in
        home-manager.lib.homeManagerConfiguration {
          pkgs = pkgsFor system;
          extraSpecialArgs = {
            inherit hmTools profile self;
          };
          modules = [
            sops-nix.homeManagerModules.sops
            ./nix/home/profiles/common.nix
            ./nix/home/profiles/development.nix
            ./nix/home/profiles/legacy-static.nix
            ./nix/home/profiles/agents.nix
            ./nix/home/profiles/${profile}.nix
            {
              home.username = username;
              home.homeDirectory = homeDirectory;
            }
          ];
        };

      aslanSystemConfig = system-manager.lib.makeSystemConfig {
        modules = [ ./nix/system/aslan.nix ];
      };
    in
    {
      homeConfigurations = {
        "ervin@lenovo" = mkHome {
          system = "x86_64-linux";
          profile = "lenovo";
          homeDirectory = "/home/ervin";
        };
        # Cloudtop is evaluated with --impure so Home Manager targets the
        # account's existing HOME instead of assuming /home/ervin.
        "ervin@cloudtop" = mkHome {
          system = "x86_64-linux";
          profile = "cloudtop";
          homeDirectory =
            let
              home = builtins.getEnv "HOME";
            in
            if home == "" then "/nonexistent/cloudtop-home" else home;
        };
        "ervin@hp" = mkHome {
          system = "x86_64-linux";
          profile = "hp";
          homeDirectory = "/home/ervin";
        };
        "ervin@aslan" = mkHome {
          system = "x86_64-linux";
          profile = "aslan";
          homeDirectory = "/home/ervin";
        };
        "ervin@macbook-apple-silicon" = mkHome {
          system = "aarch64-darwin";
          profile = "macbook";
          homeDirectory = "/Users/ervin";
        };
      };

      darwinConfigurations = {
        "macbook-apple-silicon" = nix-darwin.lib.darwinSystem {
          system = "aarch64-darwin";
          modules = [
            ./nix/darwin/macbook.nix
            home-manager.darwinModules.home-manager
            (
              { lib, ... }:
              let
                hmTools = hmToolsFor "aarch64-darwin";
              in
              {
                home-manager.useGlobalPkgs = true;
                home-manager.useUserPackages = true;
                home-manager.backupCommand = "${hmTools.backupCollisionForActivation}/bin/hm-backup-collision-for-activation";
                home-manager.extraSpecialArgs = {
                  profile = "macbook";
                  inherit hmTools self;
                };
                home-manager.users.ervin = {
                  imports = [
                    ./nix/home/profiles/common.nix
                    ./nix/home/profiles/development.nix
                    ./nix/home/profiles/legacy-static.nix
                    ./nix/home/profiles/agents.nix
                    ./nix/home/profiles/macbook.nix
                  ];
                };
                system.activationScripts.postActivation.text = lib.mkAfter ''
                  oldSystem=$(readlink -e /run/current-system 2>/dev/null || true)
                  launchctl asuser "$(id -u ervin)" sudo -u ervin --set-home \
                    env HOME=/Users/ervin \
                    ${hmTools.restoreCollisions}/bin/hm-restore-backups \
                    --forward "$oldSystem" "$systemConfig"
                '';
              }
            )
          ];
        };
      };

      # System Manager's CLI consumes systemConfigs.default. Keep the named
      # Aslan output for direct evaluation and documentation as well.
      systemConfigs = {
        default = aslanSystemConfig;
        aslan = aslanSystemConfig;
      };

      packages = forAllSystems (
        system:
        let
          hmTools = hmToolsFor system;
        in
        {
          hm-preflight = hmTools.preflight;
          hm-restore-backups = hmTools.restoreCollisions;
          hm-switch = hmTools.switchCommand;
        }
      );

      apps = forAllSystems (
        system:
        let
          hmTools = hmToolsFor system;
        in
        {
          hm-preflight = {
            type = "app";
            program = lib.getExe hmTools.preflight;
          };
          hm-restore-backups = {
            type = "app";
            program = lib.getExe hmTools.restoreCollisions;
          };
          hm-switch = {
            type = "app";
            program = lib.getExe hmTools.switchCommand;
          };
        }
      );

      checks = forAllSystems (
        system:
        {
          home-manager-backup-restore = (hmToolsFor system).test;
          rendered-shells = renderedShellCheckFor system;
        }
        // lib.optionalAttrs (system == "x86_64-linux") {
          home-aslan = self.homeConfigurations."ervin@aslan".activationPackage;
          home-cloudtop = self.homeConfigurations."ervin@cloudtop".activationPackage;
          home-hp = self.homeConfigurations."ervin@hp".activationPackage;
          home-lenovo = self.homeConfigurations."ervin@lenovo".activationPackage;
          system-aslan = self.systemConfigs.aslan;
        }
        // lib.optionalAttrs (system == "aarch64-darwin") {
          darwin-macbook = self.darwinConfigurations."macbook-apple-silicon".system;
          home-macbook = self.homeConfigurations."ervin@macbook-apple-silicon".activationPackage;
        }
      );

      formatter = forAllSystems (system: (pkgsFor system).nixfmt-rfc-style);
    };
}
