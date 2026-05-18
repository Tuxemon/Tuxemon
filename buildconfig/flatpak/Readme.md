# Creating Flatpak Package Manually

## Steps to Build and Install

1. **Remove Previous Installations**: Before proceeding, ensure that any previous installations of the package are removed.

2. **Execute Build and Install Scripts**:
   - Run `build.sh` to build the package.
   - Run `install.sh` to install the package.

## Update Flatpak Manifest

**The manifest points to the development branch, so the source is always up to date. In case of any build problems, because of changes in the requirements.txt, the manifest and its dependencies must be updated as described below.**

1. **Update Flatpak Manifest**:
   - Open `org.tuxemon.Tuxemon.yaml`.

2. **Update PortMidi Version**:
   - If a new version of PortMidi exists, update it in the relevant section.

3. **Regenerate Requirements**:
   - **Important**: While you can use `updateRequirements.sh` to see which packages are necessary, do not replace the generated JSON with the old ones. Instead, manually find the right combination of packages needed for your build, acting only on links and SHA while keeping the same structure. Be aware that replacing links and SHA manually, as well as testing the combinations, may require multiple attempts and can be a draining process.

4. **Add Build Options for Pygame**:
   - Open `python3-requirements.json` and add the build options for `python3-pygame` again. You can reference the build options from the following link:
     - [Katawa Shoujo Pygame Build Options](https://github.com/flathub/com.katawa_shoujo.KatawaShoujo/blob/74e5f93c4a668789f6464ba13017a9737c12764b/pygame/pygame-1.9.6.json#L10-L41)

## Troubleshooting

### Pygame Build Issues

If you encounter issues with Pygame failing to build due to missing PortMidi:

- Check the `python3-requirements.json` file to ensure that the build configuration for Pygame is present. If it was removed, add it back using the reference provided above.

### Dependency Management

- When selecting packages, try to avoid generic wheels (often labeled as `py3-none-any.whl`) if the package offers manylinux wheels (for x86_64 and aarch64). Generic wheels and tar.gz files can introduce unwanted dependencies that may complicate the build process.
