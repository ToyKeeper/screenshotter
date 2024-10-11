# Screenshotter

A simple tool to take screenshots in some configurable ways.  Intended for use
at a command line or from a hotkey.

Configuration options include:

  - Command to use for capturing the screen.  This allows for automatic or
    fullscreen modes, capturing all or part of the screen, a window or a
    rectangle, etc.
  - How long to delay before capture.
  - Command to use for editing the image, after capturing but before saving.
  - Commands to convert between formats, optimize pngs, etc.
  - Filename format template.
  - Title of the file, which goes into the template.
  - Any number of profiles, which each have their own settings.

Prompts the user for a title before saving, and remembers the last-used title
for each profile.  Fills in date and time automatically.

## Dependencies

Requires:

  - Python 3
  - Some sort of unixy operating system

Recommends:

  - ImageMagick (for the 'import' and 'convert' commands)
  - zenity (for prompting the user for a title)
  - John Bradley's "xv" ... or whatever other image viewer / editor you like
  - xwd (in case ImageMagick has any trouble with fullscreen capture)

## Install

Copy `screenshotter.py` to your $PATH somewhere.  Maybe make some aliases to it
for easier typing.

```sh
  > cp -av screenshotter.py ~/bin/
  > cd ~/bin
  > ln -s screenshotter.py sshot
```

It would also be a good idea to add hotkeys to your window manager, to run the
program whenever you hit a particular key.  For example, in Sawfish...

```lisp
(bind-keys global-keymap   "PrintScreen" '(run-shell-command "sshot --interactive"))
(bind-keys global-keymap "S-PrintScreen" '(run-shell-command "sshot --fullscreen"))
```

## Configuration

Copy the `rc` directory to `~/.screenshotter`, then edit the files as desired,
to change settings and behavior.

```sh
  > cd ~/src/screenshotter
  > rsync -av rc/ ~/.screenshotter
  > cd ~/.screenshotter
  > vim whatever-file
```

