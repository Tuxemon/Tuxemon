from os.path import join
import glob as _glob
import os
import shutil as _shutil
import subprocess

from pythonforandroid.logger import info
from pythonforandroid.recipe import CompiledComponentsPythonRecipe
from pythonforandroid.toolchain import current_directory

# NDK r21+ unified sysroot: lib dir uses GNU toolchain triples, not ABI names.
_ABI_TO_TRIPLE = {
    "armeabi-v7a": "arm-linux-androideabi",
    "arm64-v8a":   "aarch64-linux-android",
    "x86":         "i686-linux-android",
    "x86_64":      "x86_64-linux-android",
}


def _find_sdl_include(bootstrap_dir, jni_subdir, header_name):
    """
    Find the directory containing `header_name` under `bootstrap_dir/jni/jni_subdir`.
    Returns a string suitable for use as a -I flag (or multiple space-separated flags).
    """
    search_root = join(bootstrap_dir, "jni", jni_subdir)
    try:
        result = subprocess.run(
            ["find", search_root, "-name", header_name,
             "-not", "-path", "*/test/*", "-not", "-path", "*/tests/*"],
            capture_output=True, text=True,
        )
        found = sorted(
            [p.strip() for p in result.stdout.splitlines() if p.strip()],
            key=len,
        )
        if found:
            inc = "-I" + os.path.dirname(found[0])
            info(f"pygame: {header_name} → {inc}")
            return inc
    except Exception as e:
        info(f"pygame: find for {header_name} failed ({e})")

    # Fallback: pass root and include/ subdirectory so one of them hits.
    inc = "-I" + search_root + " -I" + join(search_root, "include")
    info(f"pygame: {header_name} not found, fallback: {inc}")
    return inc


class PygameCERecipe(CompiledComponentsPythonRecipe):
    # pygame-ce (Community Edition) — drop-in replacement for pygame,
    # installs into site-packages as "pygame".
    version = "2.5.7"
    url = "https://github.com/pygame-community/pygame-ce/archive/refs/tags/{version}.tar.gz"

    site_packages_name = "pygame"
    name = "pygame"

    depends = [
        "sdl2",
        "sdl2_image",
        "sdl2_mixer",
        "sdl2_ttf",
        "setuptools",
        "jpeg",
        "png",
    ]
    call_hostpython_via_targetpython = False
    install_in_hostpython = False

    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)
        with current_directory(self.get_build_dir(arch.arch)):
            # Python 3.14 / setuptools 77+: CCompiler.dry_run was removed from
            # the Compiler base class. Pygame's setup.py overrides spawn() and
            # accesses self.dry_run unconditionally, which raises AttributeError.
            try:
                with open("setup.py") as _f:
                    _src = _f.read()
                _patched = _src.replace(
                    "distutils.ccompiler.spawn(cmd, dry_run=self.dry_run, **kwargs)",
                    "distutils.ccompiler.spawn(cmd, dry_run=getattr(self, 'dry_run', False), **kwargs)",
                )
                if _patched != _src:
                    with open("setup.py", "w") as _f:
                        _f.write(_patched)
                    info("pygame: patched setup.py for Python 3.14 dry_run removal")
            except OSError:
                pass

            setup_template = open(
                join("buildconfig", "Setup.Android.SDL2.in")
            ).read()
            env = self.get_recipe_env(arch)

            # NDK r21+ replaced per-platform dirs with a unified sysroot.
            ndk_sysroot = join(
                self.ctx.ndk_dir,
                "toolchains", "llvm", "prebuilt", "linux-x86_64", "sysroot",
            )
            env["ANDROID_ROOT"] = join(ndk_sysroot, "usr")

            # API-versioned lib dir, e.g. sysroot/usr/lib/arm-linux-androideabi/21/
            ndk_lib_dir = join(
                ndk_sysroot, "usr", "lib",
                _ABI_TO_TRIPLE[arch.arch],
                str(self.ctx.ndk_api),
            )

            png = self.get_recipe("png", self.ctx)
            png_lib_dir = join(png.get_build_dir(arch.arch), ".libs")
            png_inc_dir = png.get_build_dir(arch)

            jpeg = self.get_recipe("jpeg", self.ctx)
            jpeg_inc_dir = jpeg_lib_dir = jpeg.get_build_dir(arch.arch)

            # Locate SDL sub-library headers dynamically — newer SDL_image/
            # SDL_mixer/SDL_ttf releases put headers in include/ not the root.
            _bd = self.ctx.bootstrap.build_dir
            sdl_image_inc = _find_sdl_include(_bd, "SDL2_image", "SDL_image.h")
            sdl_mixer_inc = _find_sdl_include(_bd, "SDL2_mixer", "SDL_mixer.h")
            sdl_ttf_inc   = _find_sdl_include(_bd, "SDL2_ttf",   "SDL_ttf.h")

            setup_file = setup_template.format(
                sdl_includes=(
                    " -I"
                    + join(_bd, "jni", "SDL", "include")
                    + " -L"
                    + join(_bd, "libs", str(arch))
                    + " -L"
                    + png_lib_dir
                    + " -L"
                    + jpeg_lib_dir
                    + " -L"
                    + ndk_lib_dir
                ),
                sdl_ttf_includes=sdl_ttf_inc,
                sdl_image_includes=sdl_image_inc,
                sdl_mixer_includes=sdl_mixer_inc,
                jpeg_includes="-I" + jpeg_inc_dir,
                png_includes="-I" + png_inc_dir,
                freetype_includes="",
            )
            open("Setup", "w").write(setup_file)

    def install_python_package(self, arch, name=None, env=None, is_dir=True):
        """
        Manually install pygame by copying the pre-built .so files and Python
        source into site-packages.

        The default pip install . triggers pyproject.toml → meson, which runs
        a compiler sanity-check binary compiled for ARM on the x86_64 host and
        immediately fails. Since setup.py build_ext already produced the ARM
        .so files we just copy them directly.
        """
        site_packages = self.ctx.get_site_packages_dir(arch)
        build_dir = self.get_build_dir(arch.arch)

        # setup.py build_ext writes compiled modules to build/lib.<platform>/
        lib_roots = sorted(_glob.glob(join(build_dir, "build", "lib.*")))
        if not lib_roots:
            raise RuntimeError(
                "pygame: no build/lib.* directory found — did build_ext succeed?"
            )
        compiled_root = lib_roots[-1]
        info(f"pygame: compiled_root = {compiled_root}")

        dst = join(site_packages, "pygame")

        # pygame-ce stores Python source in src_py/; classic pygame uses pygame/
        src_pkg = join(build_dir, "pygame")
        if not os.path.isdir(src_pkg):
            src_pkg = join(build_dir, "src_py")
        if not os.path.isdir(src_pkg):
            raise RuntimeError(
                f"pygame: Python source not found (tried pygame/ and src_py/ under {build_dir})"
            )
        info(f"pygame: Python source = {src_pkg}")

        # Start with the pure-Python package source
        if os.path.isdir(dst):
            _shutil.rmtree(dst)
        _shutil.copytree(src_pkg, dst)
        info(f"pygame: copied Python source to {dst}")

        # Overlay the compiled .so files — they may be directly in
        # compiled_root/ or nested one level deeper in a pygame/ subdir.
        so_count = 0
        for candidate in (compiled_root, join(compiled_root, "pygame")):
            if os.path.isdir(candidate):
                for fn in os.listdir(candidate):
                    if fn.endswith(".so"):
                        _shutil.copy2(join(candidate, fn), join(dst, fn))
                        so_count += 1
        info(f"pygame: installed {so_count} compiled modules to {dst}")

    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        env["USE_SDL2"] = "1"
        env["PYGAME_CROSS_COMPILE"] = "TRUE"
        env["PYGAME_ANDROID"] = "TRUE"
        return env


recipe = PygameCERecipe()