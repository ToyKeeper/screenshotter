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

  - A screen capture tool:
    - import (from ImageMagick)
    - xwd (in case ImageMagick has any trouble with fullscreen capture)

  - Image format conversion tool:
    - convert (from ImageMagick)

  - A dialog window tool:
    - dmenu (apt install suckless-tools)
    - yad (nicer fork of zenity)
    - zenity (basic gnome dialog window kit)

  - An image viewer / editor, to preview and/or edit pics before saving:
    - John Bradley's "xv"
    - Rasterman's "feh"
    - ... many many others

## Install

Copy `screenshotter.py` to your $PATH somewhere.  Maybe make some aliases to it
for easier typing, and install some scripts and config files.

```sh
  > mkdir -p ~/src ~/bin
  > # get the source code
  > cd ~/src
  > git clone https://github.com/ToyKeeper/screenshotter
  > # install scripts and config files
  > cd screenshotter
  > cp -av bin/p* ~/bin
  > cp -av rc ~/.screenshotter
  > cd ~/bin
  > ln -s ../src/screenshotter/screenshotter.py
  > ln -s screenshotter.py sshot
  > # configure stuff
  > cd ~/.screenshotter
  > ls -l
  > vim whatever config files you want to change
```

It would also be a good idea to add hotkeys to your window manager, to run the
program whenever you hit a particular key.  For example, in Sawfish...

```lisp
(bind-keys global-keymap   "PrintScreen" '(run-shell-command "sshot --interactive"))
(bind-keys global-keymap "S-PrintScreen" '(run-shell-command "sshot --fullscreen"))
```

Or to make things easier to customize later...

```lisp
(bind-keys global-keymap       "PrintScreen" '(run-shell-command "printscreen"))
(bind-keys global-keymap     "S-PrintScreen" '(run-shell-command "printscreen-shift"))
(bind-keys global-keymap     "C-PrintScreen" '(run-shell-command "printscreen-ctrl"))
(bind-keys global-keymap     "M-PrintScreen" '(run-shell-command "printscreen-meta"))
(bind-keys global-keymap   "S-C-PrintScreen" '(run-shell-command "printscreen-shift-ctrl"))
(bind-keys global-keymap   "S-M-PrintScreen" '(run-shell-command "printscreen-shift-meta"))
(bind-keys global-keymap   "C-M-PrintScreen" '(run-shell-command "printscreen-ctrl-meta"))
(bind-keys global-keymap "S-C-M-PrintScreen" '(run-shell-command "printscreen-shift-ctrl-meta"))
```

## Configuration

Inside `~/.screenshotter/` there are a bunch of files and directories.

Each directory is a "profile", or a collection of config settings,
which can be invoked with: `screenshotter.py --profile-name` .
For example, the "with-notes" profile is `screenshotter.py --with-notes`

There are also a variety of files.  Each file is a config setting or script.
If a file with that name exists in a profile directory, it will be used
whenever that profile is invoked.  Otherwise, it falls back to the base
config directory for default values.  Basically, profiles can override the
defaults.

Configurable files / settings:

  - `ask-title-style`: Which type of dialog or menu to use when asking the user
    for a screenshot title?  Valid options can be listed by putting an unknown
    value in this file and then trying to take a screenshot at a command line.
    The default is `dmenu`, but there are others.  Of particular note is
    `custom`, which runs a shell script instead.

  - `ask-title`: Script for the 'custom' style.  See an existing script for
    info about how to use this.  It should accept three inputs:
    - `$1`: Profile name.
    - `$2`: Preview of the filename template.
    - `stdin`: List of recent titles, one per line.

  - `capture`: Script for capturing an image of the screen.

  - `convert_jpg` / `convert_png`: Scripts to convert images from one format to
    another.  It'll use whichever one matches the destination filename's
    extension.  It doesn't have to be just jpg or png.

  - `delay-seconds`: Floating-point number.  How long to wait (in seconds)
    before running the screen-capture program.  This allows time for the user
    to remove their finger from the hotkey before anything happens, and gives a
    margin of error for any other potential timing-related issues.

  - `edit`: Script for viewing / editing the screenshot before saving it.  Can
    be used to crop, blur, annotate, or simply confirm that the image is
    correct.  Defaults to John Bradley's ancient "xv" program, which is somehow
    still one of the best programs for this sort of thing.

  - `max-titles`: Integer.  How many recent titles to remember and suggest in
    the ask-title UI?

  - `no-op`: A script which does nothing.  Symlink other scripts to this if you
    want to skip some steps in the screenshot process.

  - `path-format`: Where to save the screenshot after editing.  This is a text
    string, a template for the filename.  Supports expansion of `strftime`
    symbols and `{title}`.  This is also where you should choose a file format,
    like png or jpg.

  - `text-editor`: Script to launch your favorite text editor, for the purpose
    of adding detailed notes about the current screenshot.  See an existing
    script for an example of how to use it.  The script should accept these
    parameters:
    - `$1`: The profile name.
    - `$2`: Path to the current screenshot.

  - `titles`: Plain text list of recently used titles.  One title per line.
    Allows easy recall to avoid having to re-type old titles when you want to
    take a new picture in the same series.

... and maybe more.  I may have forgotten to document some things, but if so,
there will probably be an example somewhere in the default `rc/` config
directory.


## Usage

Almost everything is done via config files, so the command line is pretty
simple.  There are a few options though...

- `screenshotter.py --help`: Display info about command line options and usage.
  Will probably be more accurate and up-to-date than what this readme file
  says.

- `screenshotter.py --verbose`: Show more info about what's happening, on
  stdout.

- `screenshotter.py example.png`: Save the pic to `example.png` instead of
  using the usual path template system, recent title memory system, or asking
  the user interactively for a title.

- `screenshotter.py --some-profile-name`: Use the profile called
  `some-profile-name` instead of `default-profile`.


## X11 / Wayland

This program is designed for X11, built on the principles of the unix design
philosophy.  Build and customize things by combining small programs which each
do one thing well.

It might be possible to get this working in Wayland, but I wouldn't count on
it.  Wayland is designed in precisely the opposite way, one big monolith which
does everything, not designed for users to glue parts together for custom
solutions.  And instead of having standard ways to do things, which work
universally in any setup, Wayland is heavily fragmented so each desktop
environment has totally different and incompatible ways of doing things.  So
"supporting Wayland" isn't very realistic; you'd instead have to "support
Weston" and "support Sway" and "support Plasma" and "support Hyprland" and ...
etc.  Wayland categorically refuses to provide universal solutions for common
user needs, and thus lacks huge categories of basic functionality which must
then be implemented by the compositors... which are all separate projects which
don't agree with each other or cooperate consistently on standardization
efforts.  And some of these common needs require bypassing Wayland and creating
entirely different foundations, because those things are missing or forbidden
in Wayland itself.

More specifically, Wayland forbids user programs from reading the contents of
the screen, especially if they want just an arbitrary rectangular section.
This is forbidden for "security" reasons, and it's a pretty deep architectural
issue.  So, common screen capture programs don't work in Wayland.

As some Arch Linux forum users said in late 2024 while trying to figure out how
to take screenshots in Wayland, which was 16 years old at the time and yet
somehow still lacks this type of basic functionality...

    > ... restricted, so you'll have to write your own screenshot tool, resp.
    > create a .desktop file (in a privileged path) that allows eg. qdbus6 to
    > use the screenshot protocol (what of course completely undermines the
    > restriction)
    >
    > Welcome to the wonderful world of wayland.
    >
    > ...
    >
    > There is a KDE-specific public protocol.  So it's possible for
    > third-party tools to be written to use that protocol.  But if it's new
    > and apparently still not well known, it's less likely that any haven been
    > written.  Also - why are they using dbus rather than wayland for that?? 
    > *headdesk*
    >
    > KDE HQ: "Hey, there are two common methods we could use to do this
    > screenshot thing, but both kinda suck.  So lets do it yet another
    > completely different way that sucks a lot more."
    >
    > ...
    >
    > because of the highly fragmented feature API of the wayland ecosystem to
    > fill in hte gaps of a skeleton protocol - resulting in the most basic
    > stuff being ridiculously hard to come by and everything's incompatible
    > with everything else. 15 [sic, 16] years in... (I'm pretty sure when X11
    > was 15 years old, the first one or two attempts to replace it had already
    > failed...)
    >
    > "qdbus6 org.kde.KWin.ScreenShot2 /org/kde/KWin/ScreenShot2", but the API
    > uses a QVariantMap which (iirc) mean's you'll have to use
    > https://man.archlinux.org/man/core/dbus/dbus-send.1.en to pass the array
    > and it returns the image on a pipe and I'M not sure any of the diagnostic
    > tools are capable of that
    >
    > ...
    >
    > I recently switched back to X11 from wayland.  I had some unresolved
    > graphical issues, but I realized running an X11 compositor was sufficient
    > to avoid them (picom in my case).  I avoided these compositors like the
    > plague when I originally used X11, but running picom as a background
    > process is definitely the lesser of two evils compared to running a
    > wayland compositor that gets the graphics right but doesn't do anything
    > else I want.

In other words, KDE had to *completely bypass* Wayland in order to get their
screenshot function to work.  And the method for getting screenshot data is
completely different for each flavor of Wayland (i.e. the compositor / window
manager / desktop environment).

Wayland also doesn't allow global hotkeys, or allow programs to set their
window location, or allow input capture.  So heavily keyboard-reliant menu /
dialog programs like `dmenu` are basically forbidden.  You may be able to get
by with zenity or yad though, at the cost of reduced usability.

X11 was 21 years old when Wayland was first created to replace it.  Wayland is,
as of this writing, now 16 years old and is still literally unusable for a lot
of people because of the essential functions it lacks.  Like, a standard way of
taking screenshots.  Global hotkeys.  *Accessibility.*  Network transparency.
A permissions system so users can choose which programs are allowed to do what.
A way for programs to hint what their position should be onscreen.  Network
transparency.  Input monitoring / capture, for programs like a typing monitor
to remind you to take breaks.  Virtual inputs.  A display server which is
separate from the window manager.  Guaranteed server-side decorations provided
by the window manager, in accordance with the user's preferences, so clients
are *never* required to draw client-side decorations.  Session management.
Network transparency.  Ability to swap or restart the window manager without
logging out and back in.  And did I mention network transparency?  But hey, at
least it reduces dropped and torn frames.  They really optimized for that one
specific thing at the expense of a ton of important other stuff.

Maybe in 5 more years, in 2029 when Wayland is 21 years old, it'll be time for
a new thing to be invented and replace the obsolete old Wayland system.

