{ ... }:
{
  nixpkgs.config.allowUnfree = true;

  system.primaryUser = "ervin";
  system.stateVersion = 5;

  users.users.ervin.home = "/Users/ervin";
}
