# Extempore-Sublime

A Sublime Text 2 and 3 plugin for
[Extempore](https://github.com/digego/extempore).  The plugin provides
syntax highlighting, as well as some commands and keybindings for
connecting to and working with a running Extempore process.

# Installation

To install the plugin, simply download or clone this repo into your
[Sublime Text packages directory](http://docs.sublimetext.info/en/latest/basic_concepts.html#the-packages-directory).

Installation instructions for Extempore can be found at
[Extempore's github page](https://github.com/digego/extempore).

# Working with Extempore in ST

The plugin provides three commands:

- `extempore_connect` will connect to a running
  (local) Extempore process on the default port. You have to start
  this Extempore process yourself, generally in another terminal.

- `extempore_disconnect` does what it says on the tin.

- `extempore_evaluate` will evaluate either the
  currently highlighted region (if applicable) or the current
  top-level def surrounding the cursor. This is how you send code to
  the Extempore process for evaluation.

You can trigger the commands either through the menu (`Tools >
Extempore`), or the command palette (`ctrl+shift+P`) or through the
shortcut keys. The default keybindings are the same as the Extempore
Emacs mode, but you can change them to whatever you like.

# Keybindings

If you want to set up your own keybindings for e.g.
`extempore_evaluate`, then you can do that in
`Default.sublime-keymap`.

# Known Issues

The syntax highlighting currently doesn't cover a few edge cases---so
if you end up tinkering with `Extempore.JSON-tmLanguage` to fix
anything then feel free to submit a patch.
