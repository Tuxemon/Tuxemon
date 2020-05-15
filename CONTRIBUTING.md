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

## How do I contribute artistic content?
Artistic content is defined as image files or sound files.  This includes sprites, tilesets,
window decorations, fonts, sound effects, music, and anything similar.  All content must
be under a free license, such as CC0.  For questions about the license, open a github issue.

PLEASE NOTE!  All contributions must be submitted with LOWER CASE FILENAMES only!  PRs which
do not follow this format may be rejected until filenames are renamed.

Additionally, for combat animation contributions please ensure that techniques that move along the x-axis by default do so from left to right. There is code that will determine the correct orientation that the animation should be displayed.

Example:

![alt text][water0]![alt text][water1]![alt text][water2]![alt text][water3]![alt text][water4]![alt text][water5]![alt text][water6]

*If a Tuxemon on the left uses the water shot technique above then the animation will display in its default orientation from left to right. However, if a Tuxemon on the right uses the water shot technique then the animation will be flipped horizontally to display movement from right to left.*

[water0]: https://raw.githubusercontent.com/Tuxemon/Tuxemon/development/mods/tuxemon/animations/technique/water_shot00.png "water_shot00"

[water1]: https://raw.githubusercontent.com/Tuxemon/Tuxemon/development/mods/tuxemon/animations/technique/water_shot01.png "water_shot01"

[water2]: https://raw.githubusercontent.com/Tuxemon/Tuxemon/development/mods/tuxemon/animations/technique/water_shot02.png "water_shot02"

[water3]: https://raw.githubusercontent.com/Tuxemon/Tuxemon/development/mods/tuxemon/animations/technique/water_shot03.png "water_shot03"

[water4]: https://raw.githubusercontent.com/Tuxemon/Tuxemon/development/mods/tuxemon/animations/technique/water_shot04.png "water_shot04"

[water5]: https://raw.githubusercontent.com/Tuxemon/Tuxemon/development/mods/tuxemon/animations/technique/water_shot05.png "water_shot05"

[water6]: https://raw.githubusercontent.com/Tuxemon/Tuxemon/development/mods/tuxemon/animations/technique/water_shot06.png "water_shot06"

## Making a Pull Request
**When you're ready to make a pull request, submit your pull to the "development" branch.**
The "master" branch is used for releases.

Translations
------------

Tuxemon has support for several languages.  Because Tuxemon is a community project
and not all members are intimately familiar with or fluent in each language, there
are possible translation errors.  We also acknowledge that some translations may
have errors intentional or otherwise that could be offensive or inappropriate.

We make every effort to test using automated tools such as google translate to test
translations, but these are not perfect tools.

If you spot a translation error that is inappropriate, please open a github issue
and be respectful to the team.  We do not wish for translation errors and will do
what we can to make sure the game is fun and enjoyable to everyone.
