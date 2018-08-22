from os import close
from os import utime
from re import compile
from shutil import copystat
from shutil import move
from subprocess import call
from tempfile import mkstemp
from tempfile import NamedTemporaryFile


def sed_inplace(filename, pattern, repl):
    '''
    Perform the pure-Python equivalent of in-place `sed` substitution: e.g.,
    `sed -i -e 's/'${pattern}'/'${repl}' "${filename}"`.
    '''
    # For efficiency, precompile the passed regular expression.
    pattern_compiled = compile(pattern)

    # For portability, NamedTemporaryFile() defaults to mode "w+b" (i.e., binary
    # writing with updating). This is usually a good thing. In this case,
    # however, binary writing imposes non-trivial encoding constraints trivially
    # resolved by switching to text writing. Let's do that.
    with NamedTemporaryFile(mode='w', delete=False) as tmp_file:
        with open(filename) as src_file:
            for line in src_file:
                tmp_file.write(pattern_compiled.sub(repl, line))

    # Overwrite the original file with the munged temporary file in a
    # manner preserving file attributes (e.g., permissions).
    copystat(filename, tmp_file.name)
    move(tmp_file.name, filename)


def strip_whitespace(line):
    return "".join(line.split())


def is_line_commented(line_to_check):
    stripped_line = strip_whitespace(line_to_check)
    return stripped_line.startswith('#')


def get_commented_line(line_to_change):
    stripped_line = strip_whitespace(line_to_change)
    commented_line = "#" + stripped_line
    return commented_line


def get_uncommented_line(line_to_change):
    return line_to_change.replace("#", "")


def touch_file(fname, times=None):
    with open(fname, 'a'):
        utime(fname, times)


def create_temp_file():
    temp_file_tuple = mkstemp()
    close(temp_file_tuple[0])

    return temp_file_tuple[1]


def get_debian_version():
    version = None
    with open("/etc/os-release", 'r') as searchfile:
        for line in searchfile:
            if "VERSION_ID=" in line:
                quote_wrapped_version = line.split("=")[1]
                version = quote_wrapped_version.replace("\"", "").replace("\n", "")
                break

    try:
        return int(version)
    except:
        return None


def reboot_system():
    call(("/sbin/reboot"))
