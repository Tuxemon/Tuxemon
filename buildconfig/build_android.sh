#!/bin/bash
# Android APK build script for Tuxemon
# Tested on Ubuntu 22.04 / Debian 12
#
# Prerequisites installed by this script:
#   - OpenJDK 17
#   - Android SDK (API 33) + NDK r25c
#   - Rust toolchain (for pydantic-core cross-compilation)
#   - python-for-android (p4a)
#
# Usage: bash buildconfig/build_android.sh
#   Output: dist/android/tuxemon-development.apk

set -e

# ── Android SDK / NDK versions ──────────────────────────────────────────────
export ANDROID_BUILD_TOOLS_VERSION=34.0.0
export ANDROID_TOOLS_ZIP=commandlinetools-linux-9477386_latest.zip
export ANDROID_SDK_ROOT=$HOME/android_sdk

export ANDROIDSDK="$ANDROID_SDK_ROOT"
export ANDROIDAPI=34
export NDKAPI=21
export NDKVER=25.2.9519653
export ANDROIDNDK="$ANDROID_SDK_ROOT/ndk/$NDKVER"

# ── Java 17 ──────────────────────────────────────────────────────────────────
# GitHub Actions pre-sets JAVA_HOME_17_X64; prefer that over auto-detection
# because `which javac` may resolve to an older JDK already on PATH.
if [ -n "$JAVA_HOME_17_X64" ]; then
  export JAVA_HOME="$JAVA_HOME_17_X64"
else
  sudo apt-get update -qq
  sudo apt-get -y install openjdk-17-jdk-headless
  export JAVA_HOME
  JAVA_HOME=$(dirname "$(dirname "$(readlink -f "$(which javac)")")")
fi
export PATH="$JAVA_HOME/bin:$PATH"

# ── Build dependencies ────────────────────────────────────────────────────────
sudo apt-get -y remove --purge man-db 2>/dev/null || true
sudo dpkg --add-architecture i386
sudo apt-get update -qq
sudo apt-get -y install \
  build-essential pkg-config \
  python3.11 python3.11-dev python3.11-venv python3-pip \
  autoconf automake libtool libffi-dev cmake zip unzip git \
  ccache libssl-dev curl \
  libc6:i386 libncurses5:i386 libstdc++6:i386 lib32z1 libbz2-1.0:i386

# ── Rust toolchain (required by pydantic-core recipe) ────────────────────────
if ! command -v rustup &>/dev/null; then
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \
    | sh -s -- -y --default-toolchain stable --no-modify-path
fi
export PATH="$HOME/.cargo/bin:$PATH"
rustup target add aarch64-linux-android

# ── Android command-line tools ────────────────────────────────────────────────
mkdir -p "$ANDROID_SDK_ROOT"
mkdir -p "$HOME/.android"
touch "$HOME/.android/repositories.cfg"

if [ ! -f "/tmp/$ANDROID_TOOLS_ZIP" ]; then
  wget -q -O "/tmp/$ANDROID_TOOLS_ZIP" \
    "https://dl.google.com/android/repository/$ANDROID_TOOLS_ZIP"
fi

# The zip extracts to cmdline-tools/; sdkmanager expects cmdline-tools/latest/
mkdir -p /tmp/android_cmdtools
unzip -o -q "/tmp/$ANDROID_TOOLS_ZIP" -d /tmp/android_cmdtools
mkdir -p "$ANDROID_SDK_ROOT/cmdline-tools/latest"
cp -rn /tmp/android_cmdtools/cmdline-tools/. "$ANDROID_SDK_ROOT/cmdline-tools/latest/"

export PATH="$PATH:$ANDROID_SDK_ROOT/cmdline-tools/latest/bin:$HOME/.local/bin"

yes | sdkmanager --licenses > /dev/null 2>&1 || true
sdkmanager --update
yes | sdkmanager "platform-tools"
yes | sdkmanager "platforms;android-$ANDROIDAPI"
yes | sdkmanager "build-tools;$ANDROID_BUILD_TOOLS_VERSION"
yes | sdkmanager "ndk;$NDKVER"

# ── Python build tools & p4a ──────────────────────────────────────────────────
python3.11 -m pip install -U pip setuptools wheel Cython maturin
python3.11 -m pip install -U python-for-android

# p4a looks for main.py in the private source dir
cp run_tuxemon.py main.py

# ── Clean stale build artifacts ───────────────────────────────────────────────
rm -rf ~/.local/share/python-for-android/dists/
p4a clean_recipe_build tuxemon       2>/dev/null || true
p4a clean_recipe_build pygame        2>/dev/null || true
p4a clean_recipe_build pydantic_core 2>/dev/null || true
p4a clean_recipe_build pydantic      2>/dev/null || true

# ── Two-phase build (workaround for p4a Cython isolation bug) ─────────────────
# p4a compiles its own Python 3.14 (hostpython3) and uses it to build the
# SDL2 bootstrap via `python -m build`, which creates an isolated venv
# containing only setuptools — but the setup.py needs Cython.
#
# Fix:
#   Phase 1 — run a minimal p4a build so hostpython3 gets compiled and cached.
#             It will fail on the android-sdl2 step; that is expected.
#   Phase 2 — install Cython into hostpython3, then patch p4a's recipe.py to
#             pass --no-isolation to `python -m build` so it uses hostpython3's
#             environment directly instead of a fresh isolated venv.
#   Phase 3 — full build. hostpython3 is cached and now has Cython.

P4A_FLAGS=(
  --name Tuxemon
  --version 0.4
  --package=org.tuxemon.tuxemon
  --bootstrap=sdl2
  --private .
  --local-recipes buildconfig/buildozer/recipes
  --orientation=landscape
  --icon=buildconfig/buildozer/icon.png
  --permission READ_EXTERNAL_STORAGE
  --permission WRITE_EXTERNAL_STORAGE
  --arch=arm64-v8a
)
P4A_REQS="python3,openssl,libffi,setuptools,pygame,pydantic_core,pydantic,annotated_types,typing_inspection,typing_extensions,babel,pytmx,pyscroll,natsort,requests,pillow,pyyaml,packaging,pygame_menu_ce,websockets,android"

echo "=== Phase 1: compile hostpython3 (expected to fail at android-sdl2) ==="
# --ignore-setup-py prevents p4a from trying to install the Tuxemon project
# itself during the minimal phase-1 build (which would fail because the
# python-installs directory doesn't exist yet for a partial build).
p4a apk "${P4A_FLAGS[@]}" --requirements=python3 --ignore-setup-py 2>&1 || true

# Phase 2 ─────────────────────────────────────────────────────────────────────
# The binary is named 'python' (not 'python3') in hostpython3's bin dir.
HOSTPYTHON=$(find ~/.local/share/python-for-android \
  -path "*/hostpython3/*/native-build/root/usr/local/bin/python" \
  -type f 2>/dev/null | sort | tail -1)
# Fallback in case the version uses python3 or python3.x naming
if [ -z "$HOSTPYTHON" ]; then
  HOSTPYTHON=$(find ~/.local/share/python-for-android \
    -path "*/hostpython3/*/native-build/root/usr/local/bin/python3*" \
    -not -name "*-config" -type f 2>/dev/null | sort | tail -1)
fi

if [ -z "$HOSTPYTHON" ]; then
  echo "ERROR: hostpython3 not found after phase 1. Listing other_builds:"
  ls ~/.local/share/python-for-android/build/other_builds/ 2>/dev/null || true
  exit 1
fi

echo "=== Phase 2: installing Cython into hostpython3 ($HOSTPYTHON) ==="
"$HOSTPYTHON" -m pip install Cython wheel

# Install a sitecustomize.py into hostpython3's site-packages.
# Python always executes sitecustomize.py at startup — including inside
# isolated venvs created by `python -m build` — so Cython auto-installs
# itself the moment the isolated build env's Python first starts up.
HOSTPYTHON_SITE=$("$HOSTPYTHON" -c "import site; print(site.getsitepackages()[0])")
cat > "$HOSTPYTHON_SITE/sitecustomize.py" << 'SITEFIX'
try:
    import Cython
except ImportError:
    import subprocess, sys
    subprocess.run(
        [sys.executable, '-m', 'pip', 'install', '--quiet', 'Cython'],
        check=False, stderr=subprocess.DEVNULL,
    )

# Python 3.14 + setuptools 77+: distutils.ccompiler no longer re-exports
# spawn().  Pygame's setup.py calls distutils.ccompiler.spawn() directly,
# so restore it with a wrapper that accepts the full legacy signature.
# (distutils.spawn.spawn also dropped the dry_run kwarg in setuptools 77+,
# so we don't forward to it — we use subprocess directly.)
try:
    import distutils.ccompiler
    if not hasattr(distutils.ccompiler, 'spawn'):
        import subprocess as _sp
        def _spawn_compat(cmd, search_path=True, verbose=False, dry_run=False, env=None, **_kw):
            if not dry_run:
                _sp.run(cmd, env=env, check=True)
        distutils.ccompiler.spawn = _spawn_compat
except Exception:
    pass
SITEFIX
echo "Installed Cython auto-install hook: $HOSTPYTHON_SITE/sitecustomize.py"

# Also attempt recipe.py patch; print surrounding lines to diagnose on failure.
python3.11 - <<'PATCHPY'
import pathlib, pythonforandroid
recipe_py = pathlib.Path(pythonforandroid.__file__).parent / "recipe.py"
text = recipe_py.read_text()
lines = text.splitlines()

print("recipe.py lines 1395-1415 (for diagnosis):")
for i, line in enumerate(lines[1394:1415], start=1395):
    print(f"  {i}: {line}")

if "'--no-isolation'" in text or '"--no-isolation"' in text:
    print("recipe.py already has --no-isolation")
else:
    needles = [
        ("'-m', 'build', '--wheel',", "'-m', 'build', '--wheel', '--no-isolation',"),
        ('"-m", "build", "--wheel",', '"-m", "build", "--wheel", "--no-isolation",'),
        ("'--wheel',",               "'--wheel', '--no-isolation',"),
        ('"--wheel",',               '"--wheel", "--no-isolation",'),
    ]
    for needle, replacement in needles:
        if needle in text:
            recipe_py.write_text(text.replace(needle, replacement, 1))
            print(f"Patched recipe.py with needle: {needle!r}")
            break
    else:
        print("WARNING: no needle matched — relying on sitecustomize.py only")
PATCHPY

echo "=== Phase 3: full APK build ==="
p4a apk "${P4A_FLAGS[@]}" --requirements="$P4A_REQS"

mkdir -p dist/android
# Use the most recently modified .apk (guards against leftover files from phase 1)
latest_apk=$(ls -t ./*.apk 2>/dev/null | head -1)
if [ -z "$latest_apk" ]; then
    echo "ERROR: No APK file found after build"
    exit 1
fi
mv "$latest_apk" dist/android/tuxemon-development.apk
echo "APK written to dist/android/tuxemon-development.apk"