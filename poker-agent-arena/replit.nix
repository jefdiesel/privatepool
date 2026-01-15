{ pkgs }: {
  deps = [
    pkgs.nodejs_20
    pkgs.nodePackages.typescript-language-server
    pkgs.yarn
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.postgresql
  ];
}
