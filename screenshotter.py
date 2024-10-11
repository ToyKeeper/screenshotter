#!/usr/bin/env python3

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

    profile = ''
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


def log(text):
    if verbose:
        print(text)


def ask_outpath(profile, now):
    path_format = load_option(profile, 'path_format')
    prev_title = load_option(profile, 'title')
    preview = time.strftime(path_format, now)

    # get a list of recent files in dest dir
    outdir = os.path.dirname(preview)
    outdir = os.path.expanduser(outdir)
    recent = ''
    err, stdout, stderr = run('ls', '-t', outdir)
    if not err:
        unique = []
        filenames = stdout.split('\n')
        for f in filenames:
            parts = f.split('.')  # strip down to base name
            name = parts[0]
            if name not in unique:
                unique.append(name)
            if len(unique) >= 10:
                break
        unique.reverse()
        recent = 'Recent files:' + '\n'.join(unique) + '\n\n'

    # display the actual dialog window
    # make the dialog twice as big
    os.environ['GDK_SCALE'] = '2'
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

    # cancelled
    if not title:
        return None

    # remember for next time
    if title != prev_title:
        save_option(profile, 'title', title)

    # return full output path
    outpath = preview.format(title=title)
    return outpath


def find_option(profile, opt):
    cfgdir = os.path.expanduser(f'~/.{program_name}')
    candidates = []
    if profile:
        candidates.append(f'{cfgdir}/{profile}/{opt}')
    candidates.append(f'{cfgdir}/{opt}')

    for c in candidates:
        if os.path.exists(c):
            return c

    return None


def load_option(profile, opt):
    path = find_option(profile, opt)
    if not path:
        return ''
    text = open(path).read().strip()
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


def run_option(profile, opt, *args):
    path = find_option(profile, opt)
    if not path:
        return '', '', ''
    return run(path, *args)


def run(*args):
    log('run(%s)' % ' '.join(args))
    proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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

