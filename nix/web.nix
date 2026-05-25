# nix/web.nix — Rok Web Dashboard (Vite/React) frontend build
{ pkgs, rokNpmLib, ... }:
let
  src = ../web;
  npmDeps = pkgs.fetchNpmDeps {
    inherit src;
    hash = "sha256-HWB1piIPglTXbzQHXFYHLgVZIbDb60esupXSQGa1+lI=";
  };

  npm = rokNpmLib.mkNpmPassthru { folder = "web"; attr = "web"; pname = "rok-web"; };

  packageJson = builtins.fromJSON (builtins.readFile (src + "/package.json"));
  version = packageJson.version;
in
pkgs.buildNpmPackage (npm // {
  pname = "rok-web";
  inherit src npmDeps version;

  doCheck = false;

  buildPhase = ''
    npx tsc -b
    npx vite build --outDir dist
  '';

  installPhase = ''
    runHook preInstall
    cp -r dist $out
    runHook postInstall
  '';
})
