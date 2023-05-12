'''This file provides editor completions while working on DFHack using ycmd:
https://github.com/Valloric/ycmd
'''

# pylint: disable=import-error,invalid-name,missing-docstring,unused-argument

import os,platform
import ycm_core

def DirectoryOfThisScript():
    return os.path.dirname(os.path.abspath(__file__))

default_flags = [
    '-I','library/include',
    '-I','library/proto',
    '-I','plugins/proto',
    '-I','depends/protobuf',
    '-I','depends/lua/include',
    '-I','depends/md5',
    '-I','depends/jsoncpp/include',
    '-I','depends/tinyxml',
    '-I','depends/tthread',
    '-I','depends/clsocket/src',
    '-x','c++',
    '-D','PROTOBUF_USE_DLLS',
    '-D','LUA_BUILD_AS_DLL',
    '-Wall','-Wextra',
]

if os.name == 'posix':
    default_flags.extend([
        '-D','LINUX_BUILD',
        '-D','_GLIBCXX_USE_C99',
    ])
    if platform.system() == 'Darwin':
        default_flags.extend(['-D','_DARWIN'])
    else:
        default_flags.extend(['-D','_LINUX'])
else:
    default_flags.extend(['-D','WIN32'])

# We need to tell YouCompleteMe how to compile this project. We do this using
# clang's "Compilation Database" system, which essentially just dumps a big
# json file into the build folder.
# More details: http://clang.llvm.org/docs/JSONCompilationDatabase.html
#
# We don't use clang, but luckily CMake supports generating a database on its
# own, using:
#     set( CMAKE_EXPORT_COMPILE_COMMANDS 1 )

for potential_build_folder in ['build', 'build-osx']:
    if os.path.exists(DirectoryOfThisScript() + os.path.sep + potential_build_folder
                      + os.path.sep + 'compile_commands.json'):
        database = ycm_core.CompilationDatabase(potential_build_folder)
        break
else:
    raise RuntimeError("Can't find dfhack build folder: not one of build, build-osx")


def MakeRelativePathsInFlagsAbsolute(flags, working_directory):
    if not working_directory:
        return list(flags)
    new_flags = []
    make_next_absolute = False
    path_flags = ['-isystem', '-I', '-iquote', '--sysroot=']
    for flag in flags:
        new_flag = flag

        if make_next_absolute:
            make_next_absolute = False
            if not flag.startswith('/'):
                new_flag = os.path.join(working_directory, flag)

        for path_flag in path_flags:
            if flag == path_flag:
                make_next_absolute = True
                break

            if flag.startswith(path_flag):
                path = flag[len(path_flag):]
                new_flag = path_flag + os.path.join(working_directory, path)
                break

        if new_flag:
            new_flags.append(new_flag)
    return new_flags


def IsHeaderFile(filename):
    extension = os.path.splitext(filename)[1]
    return extension in ['.h', '.hxx', '.hpp', '.hh']


SOURCE_EXTENSIONS = ['.cpp', '.cxx', '.cc', '.c', '.m', '.mm']

def PotentialAlternatives(header):
    dirname, filename = os.path.split(header)
    basename, _ = os.path.splitext(filename)

    source_dirs = [dirname]

    if dirname.endswith(f'{os.path.sep}include'):
        # if we're in a folder 'include', also look in its parent
        parent = os.path.abspath(os.path.join(dirname, os.path.pardir))
        source_dirs.append(parent)
        # and ../src (used by lua dependency)
        source_dirs.append(os.path.join(parent, 'src'))

    include_idx = dirname.rfind(f'{os.path.sep}include{os.path.sep}')
    if include_idx != -1:
        # we're in a subfolder of a parent '/include/'
        # .../include/subdir/path
        # look in .../subdir/path
        source_dirs.append(
            dirname[:include_idx] +
            os.path.sep +
            dirname[include_idx + len('include') + 2*len(os.path.sep):]
        )

    for source_dir in source_dirs:
        for ext in SOURCE_EXTENSIONS:
            yield source_dir + os.path.sep + basename + ext


def GetCompilationInfoForFile(filename):
    if not IsHeaderFile(filename):
        return database.GetCompilationInfoForFile(filename)
    for alternative in PotentialAlternatives(filename):
        if os.path.exists(alternative):
            compilation_info = database.GetCompilationInfoForFile(
                alternative
            )

            if compilation_info.compiler_flags_:
                return compilation_info
    return None


def FlagsForFile(filename, **kwargs):
    # Bear in mind that compilation_info.compiler_flags_ does NOT return a
    # python list, but a "list-like" StringVec object
    compilation_info = GetCompilationInfoForFile(filename)
    if not compilation_info:
        return {
            'flags':MakeRelativePathsInFlagsAbsolute(default_flags,DirectoryOfThisScript()),
            'do_cache': True,
        }

    final_flags = MakeRelativePathsInFlagsAbsolute(
        compilation_info.compiler_flags_,
        compilation_info.compiler_working_dir_
    )

    # Make sure ycm reports more suspicuous code lines
    final_flags.append('-Wextra')

    return {
        'flags': final_flags,
        'do_cache': True
    }
