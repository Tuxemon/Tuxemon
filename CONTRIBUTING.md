Contributing
============

By committing or contributing data/files to the Tuxemon project, or any sub-
projects (the "Projects"), you agree to license your code under the GNU General
Public License version 3 and any later version (the "License").
In particular, you guarantee that you have acquired all necessary legal rights
from possible other copyright holders to license the contributions.

In any case, any contributions to the Projects must be able to be
re-distributed by the maintainers or others as part of the Git repository and
cloned repositories, in compiled binaries, and any other ways permitted by the
License.

## How do I contribute?
Tuxemon uses the ["Fork &Pull"](https://help.github.com/articles/using-pull-requests#fork--pull)
method for code contributions. The *fork & pull* model lets anyone fork an
existing repository and push changes to their personal fork without requiring
access be granted to the source repository. The changes must then be pulled
into the source repository by the project maintainer. This model reduces the
amount of friction for new contributors and is popular with open source
projects because it allows people to work independently without upfront
coordination.

## What code can I contribute?
Any of the issues on the [Tuxemon issue list](https://github.com/Tuxemon/Tuxemon/issues)
are things we are looking to have implemented in Tuxemon. Feel free to fork the
project and taking a shot at anything on the list! If you have a suggestion for
a feature that's not on the current issues list, open a GitHub issue about it
or start a discussion on the discord.

Before writing any code, discuss with the team on discord or open an issue --
there may be existing work on the topic or a team member with some tips on the
problem. Sometimes we also have opinions about a feature or topic which we want
done in a particular way to fit our project goals. In some cases we will ask
for changes before merging something. Asking the team first will reduce your
effort involved with a merge.

## How do I contribute artistic content?
Artistic content is defined as image files, sound files, and maps files. This
includes sprites, tilesets, battle backgrounds, window decorations, fonts,
sound effects, and music.  All content must be under a free license, such as
CC0.  For questions about the license, open a GitHub issue.

If you are modifying existing content and making derivatives, please find the
license the original asset is released under and be mindful of any requirements
the license specifies.  For example, you must ensure attribution under the terms
of the license, if applicable.

It will be helpful if you tell the team first what you plan on doing,
especially with game artistic content.  Unlike game code, seeing the difference
between artistic content is difficult during the PR review process.  The GitHub
interface is not able to diff images, for example.  Therefore, it is ideal that
content creators get a "lock" and agree with others that they will be making
changes to binary game content.  Ask in the discord or open an issue if you
plan on making changes to existing content.

Additionally, for combat animation contributions please ensure that techniques
that move along the x-axis by default do so from left to right. There is code that
will determine the correct orientation that the animation should be displayed.

Example:

![alt text][water0]![alt text][water1]![alt text][water2]![alt text][water3]![alt text][water4]![alt text][water5]![alt text][water6]

*If a Tuxemon on the left uses the water shot technique above, the animation will*
*be displayed in its default orientation from left to right. However, if a Tuxemon*
*on the right uses that technique, the animation will be flipped horizontally to*
*display movement from right to left.*

[water0]: https://raw.githubusercontent.com/Tuxemon/Tuxemon/development/mods/tuxemon/animations/technique/watershot_00.png "watershot_00"

[water1]: https://raw.githubusercontent.com/Tuxemon/Tuxemon/development/mods/tuxemon/animations/technique/watershot_01.png "watershot_01"

[water2]: https://raw.githubusercontent.com/Tuxemon/Tuxemon/development/mods/tuxemon/animations/technique/watershot_02.png "watershot_02"

[water3]: https://raw.githubusercontent.com/Tuxemon/Tuxemon/development/mods/tuxemon/animations/technique/watershot_03.png "watershot_03"

[water4]: https://raw.githubusercontent.com/Tuxemon/Tuxemon/development/mods/tuxemon/animations/technique/watershot_04.png "watershot_04"

[water5]: https://raw.githubusercontent.com/Tuxemon/Tuxemon/development/mods/tuxemon/animations/technique/watershot_05.png "watershot_05"

[water6]: https://raw.githubusercontent.com/Tuxemon/Tuxemon/development/mods/tuxemon/animations/technique/watershot_06.png "watershot_06"

### Content File Types
- Images should be PNG format
- Animations must be one image per frame -- no animated GIFs
- Music should be OGG format -- no mp3
- Sounds can be WAV or OGG
- If possible, include a lossless version (.wav, .flac, .ape, .wv, .psd, etc)
- Add the author, source, and licence to the ATTRIBUTIONS.md file
- If you rename the asset, include the original filename in ATTRIBUTIONS.md
- If you are adding content, include the filenames and license in ATTRIBUTIONS.md

PLEASE NOTE!  All contributions must be submitted with LOWER CASE FILENAMES
only!  PRs which do not follow this format may be rejected until filenames are
renamed.

### Compressed Assets
If you are a content creator, please consider uploading your assets in a
uncompressed or lossless format.  For sounds or music this would be either a
wave (WAV) or FLAC file. Images must be PNG.  We will not accept JPG or any
variation of lossy compressed images, unless it is for a concept or some
ancillary purpose.

Note your contributions will be distributed with the game will very likely be
altered prior to distribution by compressing or packing them for a smaller
size.  However, we would ideally have the originals to allow us to target a
balance for size and quality for different platforms that we support.

### File Name and Structure Guidelines
- Must be lowercase
- No spaces or symbols
- Use letters, numbers, underscore (_) and dash (-) only
- Use only ASCII letters without accents
- Files should be placed in the most appropriate folder
- English is preferred because we have contributors who speak many languages

**WHEN MAKING NEW CONTENT, IT IS BEST TO RENAME THINGS BEFORE WORKING ON THEM**

**WE MAY ASK YOU TO RENAME ASSETS BEFORE MERGING, SO THIS WILL SAVE YOU TIME**

## Map Guidelines
We use the Tiled map editor to create the game maps and story content.  There
are a few guidelines to follow when adding new maps or modifying existing ones.

- All events and collisions must be grid-aligned.  (View -> Snap to grid)
- Like other assets, the map filename must be lowercase only
- Maps should use the "core" tilesets whenever possible
- New maps should not have embedded tilesets -- use external tilesets only
- You must use `translated_dialog` for all dialogs
- The "base64 zlib compressed" map format is preferred

### Map Tileset Guidelines
Please read and understand the following information to ensure that your new
maps can be quickly accepted into the project.

- New tilesets must be acceptable by our licence and content standards
- New files should conform to the filename/structure guidelines
- Obsolete assets should be avoided

## Code Guidelines
The majority of the codebase is Python.  There are other parts of the game
written in other languages, but the guidelines are applicable to all
contributed code.

- New files should follow PEP8 -- this includes 79 char. line limit
- use ``black`` and ``isort`` to format python files after you've made changes
- Docstrings on new functions are mandatory, unless they are overloading
- Function/method signatures should have basic typing information
- Do not change existing formatting unless you are improving it
- Avoid adding dead code: code that isn't used for anything
- Do not add print statements for debugging
- Print statements should only be used if the player is using the CLI
- Debugging or similar information should use the logging module
- Tests are not required but are encouraged on new code
- Avoid duplication of existing code
- Add TODOs: if you are introducing incomplete code paths
- Raising an exception and crashing is preferred over error handling
- Don't excessively try to cover up errors or bugs; fix the cause first
- Interactive tests go in the "scripts" folder
- Unit tests go in the "tests" folder

## General Pull Request Guidelines
- You must target the development branch
- You should work from a feature branch to avoid merge complications
- Avoid excessive commits

### Branches ##
It is highly recommended that before starting your work, create a new branch
and do not develop off the "development" branch.  Directly working off your
"development" branch can will create a headache for you later, especially if
your PR is not merged right away.  **Before you make a single change, make a
new git branch from development and work from that.**  When finished, merge
development if needed and then open a PR from your feature branch to our
development branch.

TL;DR: work from a feature branch, not the development branch.

### Pull Request Checklist
- Fix any conflicts
- Apply code formatting to changed files
- **Play test the game to confirm your changes don't break anything**

## Play testing
We currently do not have good test coverage.  Therefore, it is your
responsibility to test the game to ensure your changes 1) work and 2) don't
break anything else.  A "play test" is roughly spending 10 minutes playing the
game, catching monsters, moving between screens, interacting with NPCs,
navigating the menus, and saving and loading.  Also, you must verify your
changes work.  A play test should be conducted from a new game, not a save.

It is an honor system, so please keep that in mind as we accept your changes.

Translations
============
Tuxemon has support for several languages.  Because Tuxemon is a community
project and not all members are intimately familiar with or fluent in each
language, there are possible translation errors.  We also acknowledge that some
translations may have errors intentional or otherwise that could be offensive
or inappropriate.

### Quality
We make every effort to test using automated tools such as google translate to
test translations, but these are not perfect tools.

If you spot a translation error that is inappropriate, please open a GitHub
issue and be respectful to the team.  We do not wish for translation errors and
will do what we can to make sure the game is fun and enjoyable to everyone.

We use [Weblate](https://hosted.weblate.org/projects/tuxemon/) for
translations. It is a powerful platform, but not without issues.  Occasionally
it will have problems that an admin needs to resolve.  Please open an issue or
contact a team member in the discord if your Weblate contributions are not
being merged into the project.

### Fallback
By default, Tuxemon will display text in the default language.  If that
language is not English, then English will be the "fallback".  If some text
in the primary language is not available, then English will be used
automatically.  If English is not available either, the text slug/msgid will
be used.

There is no need to put English in the files for other languages.

### Editing PO files
It is possible to also directly edit the .po files to add or update
translations.  When adding new text, only add the messages for the target
language, unless you are also translating that content, too.

Do not add text in a PO file that is not the language of the file.  Do not
add English text to a Spanish base.po file.

For example:
- Adding English: Just add content to the en_US base.po file. No others.
- Adding English and Spanish: Only add content to their respective files.


### Translations Guidelines
- Right-to-left languages are not supported
- Only the standard latin alphabet with some accents is supported
- Our text rendering currently may not support your target language, but you
  can still submit translations anyway.  When possible, we will add support for
  your language.
- After translation, some dialogs may not look correct because they are too
  long or short... that is a limitation of our game right now and we will fix
  it sometime.  If possible, please leave the dialogs "long" or overflowing and 
  eventually a fix will be made so they fit correctly.
- Translation files can be found in `mods/tuxemon/l18n` together with a README

Content Restrictions
====================
The project is developed by and for a worldwide audience of all ages.  We ask
that any contributions which includes word in text or image format be
appropriate for people aged roughly 6-14.  Of course older players are included
in this, but the game must not include inappropriate language or images for a
younger demographic.  Examples of content which would be rejected are extreme
graphic violence, sexual imagery, and crude language.

You are welcome to create your own content that is outside this limitation, but
we cannot accept it in this repository, and we would ask that you are
respectful with the "Tuxemon" name so that we are not associated with topics
that would be covered by the paragraph above.  Thank you!
