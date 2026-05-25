# nix/packages.nix — Rok Agent package built with uv2nix
{ inputs, ... }:
{
  perSystem =
    { pkgs, inputs', ... }:
    let
      RokAgent = pkgs.callPackage ./rok-agent.nix {
        inherit (inputs) uv2nix pyproject-nix pyproject-build-systems;
        npm-lockfile-fix = inputs'.npm-lockfile-fix.packages.default;
        # Only embed clean revs — dirtyRev doesn't represent any upstream
        # commit, so comparing it would always claim "update available".
        rev = inputs.self.rev or null;
      };
    in
    {
      packages = {
        default = RokAgent;
        tui = RokAgent.rokTui;
        web = RokAgent.rokWeb;

        fix-lockfiles = RokAgent.rokNpmLib.mkFixLockfiles {
          packages = [ RokAgent.rokTui RokAgent.rokWeb ];
        };
      };
    };
}
