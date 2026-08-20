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

  outputs = inputs@{
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

      pkgsFor = system:
        import nixpkgs {
          inherit system;
          config.allowUnfree = true;
        };

      # Every fixed-path host declares its home path explicitly. Cloudtop instead
      # reads the activating account's existing HOME under --impure.
      mkHome = {
        system,
        profile,
        username ? "ervin",
        homeDirectory,
      }:
        home-manager.lib.homeManagerConfiguration {
          pkgs = pkgsFor system;
          extraSpecialArgs = { inherit profile self; };
          modules = [
            sops-nix.homeManagerModules.sops
            ./nix/home/profiles/common.nix
            ./nix/home/profiles/development.nix
            ./nix/home/profiles/${profile}.nix
            {
              home.username = username;
              home.homeDirectory = homeDirectory;
            }
          ];
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
            let home = builtins.getEnv "HOME";
            in if home == "" then "/nonexistent/cloudtop-home" else home;
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
            {
              home-manager.useGlobalPkgs = true;
              home-manager.useUserPackages = true;
              home-manager.extraSpecialArgs = {
                profile = "macbook";
                inherit self;
              };
              home-manager.users.ervin = {
                imports = [
                  ./nix/home/profiles/common.nix
                  ./nix/home/profiles/development.nix
                  ./nix/home/profiles/macbook.nix
                ];
              };
            }
          ];
        };
      };


      formatter = forAllSystems (system: (pkgsFor system).nixfmt-rfc-style);
    };
}
