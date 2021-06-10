[![Python 3.9](https://img.shields.io/badge/python-3.9-blue.svg)](https://www.python.org/)
[![License: GPL v3](https://img.shields.io/badge/license-GPLv3-purple.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Description
===========

A [kitty](https://sw.kovidgoyal.net/kitty/) kitten that aims to act like the
[native URL hints kitten](https://sw.kovidgoyal.net/kitty/kittens/hints.html)
(bound to `ctrl+shift+e` by default), while supporting WeeChat's line wrapping
for URLs.  The goal is to be able to use URL hints directly without having to
go into WeeChat's raw mode (bound to `meta+l` by default) first.

Dependencies
============

- [Python 3.9+](https://www.python.org/)

… as well as [kitty](https://sw.kovidgoyal.net/kitty/) and
[WeeChat](https://weechat.org/).

Screenshots
===========

**Before:** using kitty's native URL hints kitten, wrapped URLs are not
detected/opened correctly.  
![Before](img/before.png)

**After:** using this script, wrapped URLs are detected/opened correctly.
![After](img/after.png)

Usage instructions
==================

In WeeChat, `weechat.look.prefix_suffix` and `weechat.look.separator_vertical`
must be set to the same value. Additionally, the `WEECHAT_SEPARATOR` variable
in the `weechat_hints.py` script must be updated to reflect that value.

Download and place the script (`weechat_hints.py`) in the ~/.config/kitty/
directory, for example:

    cd ~/.config/kitty/
    wget 'https://github.com/GermainZ/kitty-weechat-hints/raw/master/weechat_hints.py'

Once that is done, kitty must be launched as such: `kitty -o 'map
kitty_mod+e kitten hints --customize-processing weechat_hints.py' weechat`.

The shortcut can be customized, for example `map f1` can be used instead to
keep the original kitten intact as a backup, and make the WeeChat-aware one
available by pressing the `F1` key.

Notes
=====

The script has to make certain assumptions, and may not work correctly if your
WeeChat layout is vastly different or for specific messages. It should,
however, provide a starting point that you can adapt.
