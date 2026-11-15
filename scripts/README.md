## Tools & Scripts Directory

This folder contains optional utilities for manipulating game files and configurations related to Tuxemon. These are **not required** to run or play the game.

### General Guidelines
- **Documentation:** All scripts should include a description and usage instructions at the top of the file.
- **Language:** New scripts must be written in Python **3.10+**.
- **Dependencies:** Do **not** add script-specific dependencies to `requirements.txt`.
- **Testing:** Unit tests are **not required** for scripts in this folder.
- **External Runtimes:** Scripts should not depend on other languages or runtimes. If they do, they must remain isolated and not alter the project itself.

### Gameplay Rule
If you're creating functionality that is required to **play** the game, it should be built into the game—not left as a separate script.