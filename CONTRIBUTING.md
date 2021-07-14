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

## What code can I contribute?
Any of the issues on the [Tuxemon issue list](https://github.com/Tuxemon/Tuxemon/issues)
are things we are looking to have implemented in Tuxemon. Feel free to fork the project
and taking a shot at anything on the list! If you have a suggestion for a feature
that's not on the current issues list, post a topic on the Programming section of the
[Tuxemon Forums](https://forum.tuxemon.org/index.php) and discuss ways we might implement
it in the game.

## How do I contribute code?
Tuxemon uses the ["Fork & Pull"](https://help.github.com/articles/using-pull-requests#fork--pull)
method for code contributions. The *fork & pull* model lets anyone fork an existing
repository and push changes to their personal fork without requiring access be
granted to the source repository. The changes must then be pulled into the source
repository by the project maintainer. This model reduces the amount of friction for new
contributors and is popular with open source projects because it allows people to work
independently without upfront coordination.

Before writing any code, discuss with the team on discord or open an issue -- there may be
existing work on the topic or a team member with some tips on the problem. Sometimes we
also have opinions about a feature or topic which we want done in a particular way to fit our
project goals. In some cases we will ask for changes or reject something.  Asking the team
first will reduce your effort involved with a merge.

## How do I contribute artistic content?
Artistic content is defined as image files or sound files.  This includes sprites, tilesets,
window decorations, fonts, sound effects, music, and anything similar.  All content must
be under a free license, such as CC0.  For questions about the license, open a github issue.

If you are modifying existing content and making dirivatives, please find the license the
original asset is released under and me mindful of any requirements the license specifies.

It will be helpful if you tell the team first what you plan on doing, especially with game
content like art, sounds, and music.  Seeing the difference between these files is difficult
and unlike game code, changes cannot be automatically merged.  Therefore, it is ideal that
content creators get a "lock" and agree with others that they will be making changes to
binary game content.

- Images should be PNG format
- Animations must be one image per frame -- no animated GIFs
- Music should be OGG format -- no mp3
- Sounds can be WAV or OGG
- Add the author, source, and licence to the CREDITS.md file
- If you rename the asset, include the original file name in the CREDITS.md file
- If you are adding content, include the filenames and license in the CREDITS.md file

PLEASE NOTE!  All contributions must be submitted with LOWER CASE FILENAMES only!  PRs which
do not follow this format may be rejected until filenames are renamed.

## Map Files
We use the Tiled map editor to create the game maps and story content.  There are a few
guidelines to follow when adding new maps or modifiying existing ones.

- All events and collisions must be grid-aligned.  (View -> Snap to grid)
- Like other assets, the filename must be lower case only
- You must use `translated_dialog` for all dialogs
- The "base64 zlib compressed" map format is preferred

## Map Tileset Guidelines
Please read and understand the following information to ensure that your new maps can be
quickly accepted into the project.

- Maps should use the "core" tilesets whenever possible, and the "external tileset" .TSX file must be used
- New maps should not have embedded tilesets -- use external tilesets only
- New tilesets must be acceptable by our licence and content standards
- New files should conform to the filename/structure guidelines
- Obsolete assets should be avoided

## Compressed Assets
If you are a content creator, please consider uploading your assets in a uncompressed or
lossless format.  For sounds or music this would be either a wave (WAV) or FLAC file.
Images must be PNG.  We will not accept JPG or any variation of lossy compressed images,
unless it is for a concept or some ancillary purpose.

Note your contributions will be distributed with the game will very likely be altered prior
to distribution by compressing or packing them for a smaller size.  However, we would ideally
have the originals to allow us to target a balance for size and quality for different platforms
that we support.

## Pull Request Guidelines
- !important!: we use use "git squash -- you should make your PR from your own branch (see below)
- You must target the development branch
- Merge the development branch before opening a pr
- If you make changes after opening a PR, merge again
- Rebasing is not needed -- we squash all commits before merging
- Code should follow PEP-8, but we are not strict
- Its strongly suggested to use the black code formatter with the defaults

## Branches ##
We use git squash as a convenience for developers when making PRs.  Before merging your changes
git squash will combine them all into a single commit.  This keeps our history simple and a developer
doesn't need to rebase, squash, or merge anything on their own, and we don't worry about having 1 or 
1000 new commits.

In order for this to work well though, you the developer should not be making a PR from your
development branch into our development branch.  It will create a headache for you later.  Before you
make a single change, make a new git branch from development and work from that.  When finished, merge
development if needed and then open a PR from your feature branch to our development branch.

TL;DR: work from a feature branch, not the development branch

## File Name and Structure Guidelines
- Must be lower case
- No spaces
- No special characters
- Use letters, numbers, underscore (_) and dash (-) only
- Files should be placed in the most appropriate folder
- English is preferred because we have contributors who speak many languages

**WHEN MAKING NEW CONTENT, IT IS BEST TO RENAME THINGS BEFORE WORKING ON THEM**

**WE MAY ASK YOU TO RENAME ASSETS BEFORE MERGING, SO THIS WILL SAVE YOU TIME**

### Pull Request Checklist
- Merge the development branch into your branch
- Fix any conflicts
- Play test the game to confirm your changes don't break anything

## Play testing
We currently do not have good test coverage.  Therefore, it is your responsibility to test the
game to ensure your changes 1) work and 2) don't break anything else.  A "play test" is roughly
spending 10 minutes playing the game, catching monsters, moving between screens, interacting with
NPCs, navigating the menus, and saving and loading.  Also, you must verify your changes work.

A play test should be conducted from a new game.

It is an honor system, so please keep that in mind as we accept your changes.

Translations
============

Tuxemon has support for several languages.  Because Tuxemon is a community project
and not all members are intimately familiar with or fluent in each language, there
are possible translation errors.  We also acknowledge that some translations may
have errors intentional or otherwise that could be offensive or inappropriate.

We make every effort to test using automated tools such as google translate to test
translations, but these are not perfect tools.

If you spot a translation error that is inappropriate, please open a github issue
and be respectful to the team.  We do not wish for translation errors and will do
what we can to make sure the game is fun and enjoyable to everyone.

We use [Weblate](https://hosted.weblate.org/projects/tuxemon/) for translations.
It is a powerful platform, but not without issues.  Occasionally it will have problems
that an admin needs to resolve.  Please open an issue or contact a team member in the
discord.

## Translations Guidelines
- Right-to-left langauges are not supported
- Only the standard latin alphabet with some accents is supported
- Our text rendering currently may not support your target language, but you can still
  submit translations anyway.  When possible, we will add support for your lanaguage.
- After translation, some dialogs may not look correct because they are too long or short...
  that is a limitation of our game right now and we will fix it sometime.  If possible, 
  please leave the dialogs "long" or overflowing and eventually a fix will be made so they
  fit correctly.

Content Restrictions
====================

The project is developed by and for a worldwide audience of all ages.  We ask that any
contributions which includes word in text or image format be appropriate for people
aged roughly 6-14.  Of course older players are included in this, but the game must not
include inappropriate language or images for a younger demographic.  Examples of content
which would be rejected are extreme graphic violence, sexual imagery, and crude language.

You are welcome to create your own content that is outside this limitation, but we cannot
accept it in this repository and we would ask that you are respectful with the "Tuxemon"
name so that we are not associated with topics that would be covered by the paragraph
above.  Thank you!
