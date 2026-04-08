{
  description = "Development environment for IronSight (Standalone USB Camera Server)";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
        };
        
        # We need OpenCV Headless explicitly and our FastAPI dependencies
        pythonEnv = pkgs.python311.withPackages (ps: with ps; [
          opencv4
          numpy
          fastapi
          uvicorn
          pydantic
          python-multipart
          python-jose
        ]);
        
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pythonEnv
            pkgs.ffmpeg
            pkgs.mediamtx
            pkgs.nodejs_20 # Added Node.js for Vite frontend development
          ];

          shellHook = ''
            echo "========================================="
            echo "   IronSight Dev Environment Loaded   "
            echo "========================================="
            echo "Python, FFmpeg, and NodeJS are available."
          '';
        };
      }
    );
}
