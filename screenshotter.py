#!/usr/bin/env python3
# Screenshotter: a screenshot tool with a modular design for unix systems
# Copyright (C) 2024 Selene ToyKeeper
# SPDX-License-Identifier: GPL-3.0-or-later


program_name = 'screenshotter'
verbose = False

import os
import random
import subprocess
import time


def main(args):
    """screenshotter: A tool to take screenshots, with extra options.
    Usage: screenshotter [--myprofile] [filename.png]
    Args in []'s are not required.

    Options:
      -h   --help     Display this help text and exit.
      -v   --verbose  Show extra detail about actions taken.
           --profile  Use settings from {profile}.
                      Default: "default-profile"

    Profiles:
      In ~/.screenshotter/, subdirs may exist which override any of the
      available configuration values.  Simply create a directory there,
      and add a file for each setting you want to override.  For example,
      if you have
        ~/.screenshotter/test/capture
      and you run
        screenshotter --test
      then it will use that "capture" script instead of the default.
      Any setting can be overridden in this way.

    Configurable options per profile:
      Plain text values:
        delay_seconds
          How long to wait before capturing.
          Default: 0.5
        path_format
          Where to save the image.
          For example:
          ~/screenshots/%Y/%m/%d/{title}.%Y-%m-%d_%H:%M:%S.png
        title
          The part of the filename where it says "{title}".
          Default: screenshot
      Scripts:
        capture
          Command to run to actually read the screen contents.
        convert_png / convert_jpg / convert_$ext
          Script which converts the raw screenshot to the destination format.
        edit
          A program to edit the image before saving.
    """

    profile = 'default-profile'
    outpath = None

    for a in args:
        if a in ('-h', '--help'):
            return help()
        elif a in ('-v', '--verbose'):
            global verbose
            verbose = True
        elif a.startswith('--'):
            profile = a[2:]
        else:
            outpath = a

    screenshot(profile, outpath)


def help():
    print(main.__doc__.replace('\n    ', '\n'))


def screenshot(profile, outpath=None):
    # delay
    try:
        delay_seconds = float(load_option(profile, 'delay_seconds'))
    except ValueError:
        delay_seconds = 0.5
    time.sleep(delay_seconds)

    # timestamp
    now = time.localtime()

    # capture
    tmpfile = tmp_filename()
    log(f'capture {tmpfile}')
    run_option(profile, 'capture', tmpfile)

    # edit
    log(f'edit {tmpfile}')
    cwd = os.getcwd()
    os.chdir('/tmp')
    run_option(profile, 'edit', tmpfile)
    os.chdir(cwd)

    # file name / title
    if not outpath:
        outpath = ask_outpath(profile, now)
        if not outpath:
            log(f'Cancelled')
            os.remove(tmpfile)  # FIXME: should only be handled in one place
            return
    log(f'outpath {outpath}')

    # move the file, ensure destination directory exists
    outpath = os.path.expanduser(outpath)
    outdir = os.path.dirname(outpath)
    if outdir and not os.path.exists(outdir):
        os.makedirs(outdir)
    #shutil.move(tmpfile, outpath)

    # convert and move
    log(f'convert {tmpfile} {outpath}')
    base, ext = os.path.splitext(outpath)
    if ext:
        ext = ext.replace('.', '')
        script = f'convert_{ext}'
        if find_option(profile, script):
            log(f'conversion script: {script}')
            run_option(profile, script, tmpfile, outpath)
    # if conversion failed for any reason,
    # just move the tmpfile to the destination
    if not os.path.exists(outpath):
        shutil.move(tmpfile, outpath)

    # clean up
    os.remove(tmpfile)

    # if the user wants to add more notes, fire up a text editor
    if find_option(profile, 'text-editor'):
        log(f'text editor: {outpath}')
        run_option(profile, 'text-editor', profile, outpath)


def log(text):
    if verbose:
        print(text)


def ask_outpath(profile, now):
    path_format = load_option(profile, 'path_format')
    max_titles = int(load_option(profile, 'max_titles', 16))
    # recent titles are one per non-blank line
    prev_titles = [l for l in
                   load_option(profile, 'titles').split('\n')
                   if l]
    if prev_titles: prev_title = prev_titles[0]
    else: prev_title = ''
    preview = time.strftime(path_format, now)

    # get a list of recent files in dest dir
    outdir = os.path.dirname(preview)
    outdir = os.path.expanduser(outdir)
    recent = ''
    unique = prev_titles[:]
    err, stdout, stderr = run('ls', '-t', outdir)
    if not err:
        filenames = stdout.split('\n')
        for f in filenames:
            parts = f.split('.')  # strip down to base name
            name = '.'.join(parts[:-1])  # strip only final extension
            if name and (name not in unique):
                unique.append(name)
            if len(unique) >= max_titles:
                break
        unique.reverse()
    # recall other recent titles too, if there's room
    if len(unique) < max_titles:
        for t in prev_titles:
            if t not in unique:
                unique.append(t)
    unique = [title.replace('-', ' ') for title in unique[:max_titles]]
    unique.reverse()

    # choose a UI style for the dialog window...
    dialog_style = load_option(profile, 'ask-title-style').replace('-', '_')
    try:
        dialog_func = globals()[f'dialog_{dialog_style}']
    except KeyError:
        print('Error: unrecognized dialog style name')
        print('Styles include:')
        keys = list(globals().keys())
        keys.sort()
        for k in keys:
            if k.startswith('dialog_'):
                k = k[len('dialog_'):].replace('_', '-')
                print(f'  {k}')
        return None

    # make GDK/GTK dialogs twice as big
    # FIXME: this isn't the right place to do this
    os.environ['GDK_SCALE'] = '2'

    # ask the user for a title
    err, title = dialog_func(profile, preview, unique)

    # cancelled
    if 0 != err:
        return None

    # default to last-used title
    if not title:
        title = prev_title

    # clean up the title to make it work better as a filename
    title = title.replace(' ', '-')

    # remember for next time
    #if title != prev_title:
    #    save_option(profile, 'title', title)
    if title != prev_title:
        if title in prev_titles:
            prev_titles.remove(title)
        prev_titles.insert(0, title)
        prev_titles = prev_titles[:max_titles]
        save_option(profile, 'titles', '\n'.join(prev_titles))

    # return full output path
    outpath = preview.format(title=title)
    return outpath


def dialog_zenity_entry_history(profile, preview, titles):
    prev_title = titles[0].replace('_', '__')
    titles.reverse()
    titles = titles[:20]  # FIXME: should be configurable
    recent = '\n'.join(titles).strip() + '\n\n'

    # display the actual dialog window
    # don't let gtk eat underscores
    escaped_preview = preview.replace('_', '__')
    escaped_recent = recent.replace('_', '__')
    err, stdout, stderr = run('zenity', '--entry',
                              f'--title=Enter Title [{program_name} --{profile}]',
                              f'--class={program_name}',
                              f'--name={profile}',
                              f'--text={escaped_recent}Save to: {escaped_preview}\nTitle:',
                              f'--entry-text={prev_title}',
                              )
    title = stdout.strip()

    return err, title


def dialog_zenity_2step(profile, preview, titles):
    prev_title = titles[0].replace('_', '__')
    escaped_preview = preview.replace('_', '__')
    err, stdout, stderr = run('zenity', '--entry',
                              f'--title=Enter Title [{program_name} --{profile}]',
                              f'--class={program_name}',
                              f'--name={profile}',
                              f'--text=Save to: {escaped_preview}\nTitle:',
                              f'--entry-text={prev_title}',
                              f'--cancel-label=Edit Recent',
                              )
    title = stdout.strip()

    # cancelled, choose from recent list instead
    if 0 != err:
        lengths = [(len(title), title) for title in titles]
        lengths.sort()
        longest = lengths[-1][1].replace('_', '__')
        recent = [title.replace('_', '__') for title in titles]
        err, stdout, stderr = run('zenity', '--list',
                                  f'--title=Recent Titles [{program_name} --{profile}]',
                                  f'--class={program_name}',
                                  f'--name={profile}',
                                  f'--text=Save to: {escaped_preview}\nLongest: {longest}',
                                  '--column=Title:',
                                  '--mid-search',
                                  '--hide-header',
                                  '--editable',
                                  '--height=400',  # FIXME: should be automatic
                                  *recent,
                                  )
        title = stdout.strip()
        #print(f'err: {err}')
        #print(f'stdout: {title}')
        #print(f'stderr: {stderr}')

    return err, title


def dialog_yad_form(profile, preview, titles):
    # yad --form --mouse
    #   --field='Title' 'default'
    #   --field='Recent:CBE' '^one!two!three!four'
    prev_title = titles[0]
    joined_recent = '^!' + '!'.join(titles)
    err, stdout, stderr = run('yad', '--no-markup', '--mouse',
                              '--form',
                              f'--title=Enter Title [{program_name} --{profile}]',
                              f'--class={program_name}',
                              f'--name={profile}',
                              f'--text=Save to: {preview}',
                              '--field=Title', prev_title,
                              '--field=Recent:CBE', joined_recent,
                              )
    stdout = stdout.strip()
    print(f'err: {err}')
    print(f'stdout: {stdout}')
    print(f'stderr: {stderr}')

    if not stdout:  # user cancelled the dialog window
        return 1, ''
    elif not ('|' in stdout):  # should never happen
        title = stdout
        return err, title

    # else:  # elif '|' in stdout:  # normal case
    parts = stdout.split('|')
    entry, selected = parts[:2]

    if selected not in ('', prev_title):
        title = selected
    else:  # selected == blank or prev_title
        title = entry

    if (not title) and (not err):
        err = 1

    print(f'{err}: {title}')
    #return err, title
    return 1, ''


def dialog_yad_entry_combo(profile, preview, titles):
    prev_title = titles[0]
    # FIXME: showing recent titles makes the entry box HUGE
    #recent = titles[:5]  # FIXME: should be configurable
    #recent.reverse()
    #recent_joined = '\n'.join(recent).strip() + '\n\n'
    err, stdout, stderr = run('yad', '--no-markup', '--mouse',
                              '--entry',
                              '--editable',
                              '--completion',
                              '--complete=regex',
                              #'--no-buttons',
                              f'--title=Enter Title [{program_name} --{profile}]',
                              f'--class={program_name}',
                              f'--name={profile}',
                              #f'--text={recent_joined}Save to: {preview}',
                              f'--text=Save to: {preview}',
                              f'--entry-text={prev_title}',
                              *titles,
                              )
    #stdout = stdout.strip()
    #print(f'err: {err}')
    #print(f'stdout: {stdout}')
    #print(f'stderr: {stderr}')
    #return 1, ''
    title = stdout.strip()
    return err, title


def dialog_dmenu(profile, preview, titles):
    stdin = bytes('\n'.join(titles), encoding='utf-8')
    err, stdout, stderr = run('dmenu',
                              '-b',  # bottom of screen
                              '-i',  # case insensitive
                              '-l', '10',  # list, number of lines to show
                              '-fn', 'Serif:pixelsize=30',  # font
                              '-p', f'sshot --{profile}',  # prompt
                              input=stdin,
                              )
    #stdout = stdout.strip()
    #print(f'err: {err}')
    #print(f'stdout: {stdout}')
    #print(f'stderr: {stderr}')
    #return 1, ''
    title = stdout.strip()
    return err, title


def dialog_custom(profile, preview, titles):
    stdin = bytes('\n'.join(titles), encoding='utf-8')
    err, stdout, stderr = run_option(profile, 'ask-title',
                                     profile, preview,
                                     input=stdin,
                                     )
    #stdout = stdout.strip()
    #print(f'err: {err}')
    #print(f'stdout: {stdout}')
    #print(f'stderr: {stderr}')
    #return 1, ''
    title = stdout.strip()
    return err, title


def find_option(profile, opt):
    cfgdir = os.path.expanduser(f'~/.{program_name}')
    # look for both 'file-name' and 'file_name'
    opt_dash = opt.replace('_', '-')
    opt_underscore = opt.replace('-', '_')
    # try both the subdir and the root config dir
    # TODO: search recursively from subdir back to config dir,
    #       in case subdir is nested
    candidates = []
    if profile:
        candidates.append(f'{cfgdir}/{profile}/{opt_dash}')
        candidates.append(f'{cfgdir}/{profile}/{opt_underscore}')
    candidates.append(f'{cfgdir}/{opt_dash}')
    candidates.append(f'{cfgdir}/{opt_underscore}')

    for c in candidates:
        if os.path.exists(c):
            return c

    return None


def load_option(profile, opt, default=None):
    if not default:
        default = ''
    path = find_option(profile, opt)
    if not path:
        return default
    text = open(path).read().strip()
    if not text:
        return default
    return text


def save_option(profile, opt, value):
    cfgdir = os.path.expanduser(f'~/.{program_name}')
    if profile:
        path = f'{cfgdir}/{profile}/{opt}'
    else:
        path = f'{cfgdir}/{opt}'
    with open(path, 'w') as f:
        f.write(value)
        f.write('\n')


def run_option(profile, opt, *args, **kwargs):
    path = find_option(profile, opt)
    if not path:
        return '', '', ''
    return run(path, *args, **kwargs)


def run(*args, **kwargs):
    log('run(%s)' % ' '.join(args))
    proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)
    stdout = str(proc.stdout, encoding='utf-8')
    stderr = str(proc.stderr, encoding='utf-8')
    code = proc.returncode
    return code, stdout, stderr


def tmp_filename():
    rand = random.randint(100000, 999999)
    path = f'/tmp/{program_name}.{rand}.png'
    return path


if __name__ == "__main__":
    import sys
    main(sys.argv[1:])

