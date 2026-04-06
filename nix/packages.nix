# nix/packages.nix — Rok Agent package built with uv2nix
{ inputs, ... }: {
  perSystem = { pkgs, system, ... }:
    let
      hermesVenv = pkgs.callPackage ./python.nix {
        inherit (inputs) uv2nix pyproject-nix pyproject-build-systems;
      };

      # Import bundled skills, excluding runtime caches
      bundledSkills = pkgs.lib.cleanSourceWith {
        src = ../skills;
        filter = path: _type:
          !(pkgs.lib.hasInfix "/index-cache/" path);
      };

      runtimeDeps = with pkgs; [
        nodejs_20 ripgrep git openssh ffmpeg
      ];

      runtimePath = pkgs.lib.makeBinPath runtimeDeps;
    in {
      packages.default = pkgs.stdenv.mkDerivation {
        pname = "rok-agent";
        version = "0.1.0";

        dontUnpack = true;
        dontBuild = true;
        nativeBuildInputs = [ pkgs.makeWrapper ];

        installPhase = ''
          runHook preInstall

          mkdir -p $out/share/rok-agent $out/bin
          cp -r ${bundledSkills} $out/share/rok-agent/skills

          ${pkgs.lib.concatMapStringsSep "\n" (name: ''
            makeWrapper ${hermesVenv}/bin/${name} $out/bin/${name} \
              --suffix PATH : "${runtimePath}" \
              --set ROK_BUNDLED_SKILLS $out/share/rok-agent/skills
          '') [ "rok" "rok-agent" "rok-acp" ]}

          runHook postInstall
        '';

        meta = with pkgs.lib; {
          description = "AI agent with advanced tool-calling capabilities";
          homepage = "https://github.com/RokctAI/rok-agent";
          mainProgram = "rok";
          license = licenses.mit;
          platforms = platforms.unix;
        };
      };
    };
}
