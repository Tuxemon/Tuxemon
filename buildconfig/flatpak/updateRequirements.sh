TAG="development" # branch or tag

mkdir -p build

wget -P build \
  https://raw.githubusercontent.com/flatpak/flatpak-builder-tools/master/pip/flatpak-pip-generator

wget -O build/pyproject.toml \
  https://raw.githubusercontent.com/Tuxemon/Tuxemon/$TAG/pyproject.toml

python3 - <<'EOF'
import tomllib

with open("build/pyproject.toml", "rb") as f:
    pyproject = tomllib.load(f)

with open("build/requirements.txt", "w") as f:
    for dep in pyproject["project"]["dependencies"]:
        f.write(dep + "\n")
EOF

python3 build/flatpak-pip-generator \
    --requirements-file=build/requirements.txt