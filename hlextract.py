#!/usr/bin/env python

from __future__ import print_function
import argparse
import hllib as hl
import shlex
import sys
import os

args = None
progress_last = 0


def main():
    global args
    args = parse_arguments()

    hl.initialize()

    package_opened = False
    package_created = False

    try:
        set_options()

        package_type = hl.Package.get_package_type_from_file(args.package)

        if package_type == hl.HLPackageType.HL_PACKAGE_NONE:
            raise hl.HLError("Error loading {0}:\nUnsupported "
                    "package type.".format(args.package))

        package_id = hl.Package.create_package(package_type)
        package_created = True

        hl.Package.bind_package(package_id)

        hl.Package.open_file(args.package, get_file_mode())
        package_opened = True

        if package_type == hl.HLPackageType.HL_PACKAGE_NCF:
            hl.NCFFile.set_root_path(args.ncfroot)

        if not args.silent:
            print(args.package + " opened.")

        if args.extract:
            extract_items()

        if args.validate:
            validate_items()

        if args.list:
            list_items()

        if args.defragment:
            defragment()

        if args.console:
            enter_console(package_id)

    finally:
        if package_opened:
            hl.Package.close()

            if not args.silent:
                print(args.package + " closed.")

        if package_created:
            hl.Package.delete_package(package_id)

        hl.shutdown()


def get_argument_parser():
    parser = argparse.ArgumentParser()
    list_group = parser.add_mutually_exclusive_group()

    parser.add_argument('-p', '--package', required=True,
            help='Package to load.')

    parser.add_argument('-d', '--dest',
            help='Destination extraction directory.')

    parser.add_argument('-e', '--extract', action='append',
            help='Item(s) in package to extract.')

    parser.add_argument('-t', '--validate', action='append',
            help='Item(s) in package to validate.')

    list_group.add_argument('-l', '--list', nargs='?', const=True,
            help='List the contents of the package.')

    list_group.add_argument('--list-directories', nargs='?', const=True,
            help='List the contents of the package (directories only).')

    list_group.add_argument('--list-files', nargs='?', const=True,
            help='List the contents of the package (files only).')

    parser.add_argument('-f', '--defragment', action='store_true',
            help='Defragment package.')

    parser.add_argument('-c', '--console', action='store_true',
            help='Console mode.')

    parser.add_argument('-x', '--execute', action='append',
            help='Execute console command. Implies -c/--console.')

    parser.add_argument('-s', '--silent', action='store_true',
            help='Silent mode.')

    parser.add_argument('-m', '--filemapping', action='store_true',
            help='Use file mapping.')

    parser.add_argument('-q', '--quick-filemapping', action='store_true',
            help='Use quick file mapping.')

    parser.add_argument('-v', '--volatile', action='store_true',
            help='Allow volatile access.')

    parser.add_argument('-o', '--overwrite', action='store_false',
            help="Don't overwrite files.")

    parser.add_argument('-r', '--force-defragment', action='store_true',
            help='Force defragmenting on all files.')

    parser.add_argument('-n', '--ncfroot',
            help="NCF file's root path.")

    return parser


def parse_arguments():
    parser = get_argument_parser()
    args = parser.parse_args()

    if args.quick_filemapping:
        args.filemapping = True

    if args.force_defragment:
        args.defragment = True

    if not args.dest:
        args.dest = os.path.dirname(args.package)

    if args.list is not None:
        args.list_directories = True
        args.list_files = True
    elif args.list_directories is not None:
        args.list = args.list_directories
        args.list_directories = True
    elif args.list_files is not None:
        args.list = args.list_files
        args.list_files = True

    if (not args.extract and not args.validate and not args.list
            and not args.defragment and not args.console):
        args.console = True

    return args


def set_options():
    hlo = hl.HLOption
    hl.set_value(hlo.HL_OVERWRITE_FILES, args.overwrite)
    hl.set_value(hlo.HL_FORCE_DEFRAGMENT, args.force_defragment)
    hl.set_value(hlo.HL_PROC_EXTRACT_ITEM_START, extract_item_start_callback)
    hl.set_value(hlo.HL_PROC_EXTRACT_ITEM_END, extract_item_end_callback)
    hl.set_value(hlo.HL_PROC_EXTRACT_FILE_PROGRESS, file_progress_callback)
    hl.set_value(hlo.HL_PROC_VALIDATE_FILE_PROGRESS, file_progress_callback)
    hl.set_value(hlo.HL_PROC_DEFRAGMENT_PROGRESS_EX,
            defragment_progress_callback)


def get_file_mode():
    file_mode = hl.HLFileMode.HL_MODE_READ

    if args.defragment:
        file_mode |= hl.HLFileMode.HL_MODE_WRITE

    if not args.filemapping:
        file_mode |= hl.HLFileMode.HL_MODE_NO_FILEMAPPING

    if args.quick_filemapping:
        file_mode |= hl.HLFileMode.HL_MODE_QUICK_FILEMAPPING

    if args.volatile:
        file_mode |= hl.HLFileMode.HL_MODE_VOLATILE

    return file_mode


def extract_items():
    package_root = hl.Package.get_root()

    for item_path in args.extract:
        try:
            item = package_root.get_item_by_path(
                    item_path, hl.HLFindType.HL_FIND_ALL)
        except HLError:
            print(item_path + " not found in package.")
            continue

        if not args.silent:
            print("Extracting {0}...\n".format(item_path))

        try:
            item.extract(args.dest)
        except HLError:
            print("Failed to extract {0}.".format(item_path))

        if not args.silent:
            print("\nDone.\n")


def validate_items():
    package_root = hl.Package.get_root()

    for item_path in args.validate:
        try:
            item = package_root.get_item_by_path(
                    item_path, hl.HLFindType.HL_FIND_ALL)
        except HLError:
            print(item_path + " not found in package.")
            continue

        if not args.silent:
            print("Validating {0}...\n".format(item_path))

        validate(item)

        if not args.silent:
            print("\nDone.\n")


def validate(item):
    validation = hl.HLValidation.HL_VALIDATES_OK

    if isinstance(item, hl.HLDirectoryFolder):
        if not args.silent:
            name = item.get_name()
            print("  Validating {0}:".format(name))

        for idx in range(item.get_count()):
            sub_validation = validate(item.get_item(idx))
            validation = max(validation, sub_validation)

        if not args.silent:
            print("  Done {0}: {1}".format(name,
                    get_validation_string(validation)))

    elif isinstance(item, hl.HLDirectoryFile):
        if not args.silent:
            name = item.get_name()
            print("  Validating {0}: ".format(name), end="")
            progress_start()

        validation = item.get_validation()

        if args.silent:
            # Only print on bad validation.
            if (validation != hl.HLValidation.HL_VALIDATES_ASSUMED_OK and
                    validation != hl.HLValidation.HL_VALIDATES_OK):
                name = item.get_name()
                print("  Validating {0}: {1}".format(name,
                        get_validation_string(validation)))

        else:
            print(get_validation_string(validation))


def get_validation_string(validation):
    v = hl.HLValidation

    if validation == v.HL_VALIDATES_ASSUMED_OK:
        return "Assumed OK"
    elif validation == v.HL_VALIDATES_OK:
        return "OK"
    elif validation == v.HL_VALIDATES_INCOMPLETE:
        return "Incomplete"
    elif validation == v.HL_VALIDATES_CORRUPT:
        return "Corrupt"
    elif validation == v.HL_VALIDATES_CANCELED:
        return "Canceled"
    elif validation == v.HL_VALIDATES_ERROR:
        return "Error"
    else:
        return "Unknown"


def list_items():
    if not args.silent:
        print("Listing...\n")

    own_file = isinstance(args.list, str)
    output_file = open(args.list, 'w') if own_file else sys.stdout

    try:
        package_root = hl.Package.get_root()
        list_items_recursive(output_file, package_root)
    finally:
        if own_file:
            output_file.close()

    if not args.silent:
        print("\nDone.")


def list_items_recursive(output_file, item):
    if isinstance(item, hl.HLDirectoryFolder):
        if args.list_directories:
            output_file.write("{0}\n".format(item.get_path()))

        for idx in range(item.get_count()):
            list_items_recursive(output_file, item.get_item(idx))

    elif isinstance(item, hl.HLDirectoryFile):
        if args.list_files:
            output_file.write("{0}\n".format(item.get_path()))


def defragment():
    if not args.silent:
        print("Defragmenting...\n\n  Progress: ", end="")
        # XXX Check output this is diff from original prog.
        progress_start()

    try:
        hl.Package.defragment()
    except HLError:
        print(" " + hl.get_value(HLOption.HL_ERROR_SHORT_FORMATED), end="")

    if not args.silent:
        print("\n\nDone.\n")


def enter_console(package_id):
    root = hl.Package.get_root()
    item = root

    # Python 2 / 3 compatibility.
    try:
        get_input = raw_input
    except NameError:
        get_input = input

    while True:
        if args.execute:
            input_string = args.execute.pop(0)
            print("{0}>{1}".format(item.get_name(), input_string))
        else:
            try:
                input_string = get_input("{0}>".format(item.get_name()))
            except EOFError:
                input_string = "exit"

        input_list = shlex.split(input_string)

        if len(input_list) == 0:
            continue
        elif len(input_list) == 1:
            command = input_list[0]
            argument = None
        elif len(input_list) == 2:
            command = input_list[0]
            argument = input_list[1]
        elif len(input_list) > 2:
            print("Multiple arguments aren't supported.")
            continue

        if (os.name == "nt" and command == "dir" or
                os.name != "nt" and command == "ls"):
            console_ls(item, argument)
        elif command == "cd":
            item = console_cd(item, argument)
        elif command == "root":
            item = root
        elif command == "info":
            console_info(item, argument)
        elif command == "extract":
            console_extract(item, argument)
        elif command == "validate":
            console_validate(item, argument)
        elif command == "find":
            console_find(item, argument)
        elif command == "type":
            console_type(item, argument)
        elif command == "open":
            console_open(item, argument, package_id)
        elif command == "status":
            console_status()
        elif os.name == 'nt' and command == "cls":
            os.system("cls")
        elif command == "help":
            console_help()
        elif command == "exit":
            break
        else:
            print("Unknown command: " + command)


def console_ls(item, pattern):
    print("Directory of {0}:\n".format(item.get_path()))

    folder_count = file_count = 0

    if pattern is None:
        # List all items in the current folder.
        for idx in range(item.get_count()):
            sub_item = item.get_item(idx)

            if isinstance(sub_item, hl.HLDirectoryFolder):
                print("  <{0}>".format(sub_item.get_name()))
                folder_count += 1
            elif isinstance(sub_item, hl.HLDirectoryFile):
                print("  {0}".format(sub_item.get_name()))
                file_count += 1

    else:
        # Find first item in current folder that matches pattern.
        find = hl.HLFindType.HL_FIND_ALL | hl.HLFindType.HL_FIND_NO_RECURSE
        sub_item = item.find_first(pattern, find)

        while sub_item is not None:
            if isinstance(sub_item, hl.HLDirectoryFolder):
                print("  <{0}>".format(sub_item.get_name()))
                folder_count += 1

                # Find next item in current folder that matches pattern.
                prev_sub_item = sub_item
                sub_item = item.find_next(sub_item, pattern, find)

                if sub_item is None:
                    sub_item = prev_sub_item

            elif isinstance(sub_item, hl.HLDirectoryFile):
                print("  {0}".format(sub_item.get_name()))
                file_count += 1

                # Find next item in current folder that matches pattern.
                sub_item = item.find_next(sub_item, pattern, find)

    print("\nSummary:\n")
    print("  {0} Folder{1}.".format(folder_count,
            "" if folder_count == 1 else "s"))
    print("  {0} File{1}.".format(file_count,
            "" if file_count == 1 else "s"))
    print()


def console_cd(item, directory):
    if directory is None:
        print("No directory for command cd supplied.")
        new_item = item

    elif directory == ".":
        new_item = item

    elif directory == "..":
        new_item = item.get_parent()

        if new_item is None:
            print("Folder does not have a parent.")
            new_item = item

    else:
        for idx in range(item.get_count()):
            sub_item = item.get_item(idx)

            if (isinstance(sub_item, hl.HLDirectoryFolder) and
                    directory == sub_item.get_name()):
                new_item = sub_item
                break
        else:
            print(directory + " not found.")
            new_item = item

    return new_item


def console_info(item, path):
    if path is None:
        print("No argument for command info supplied.")
        return

    sub_item = item.get_item_by_path(path, hl.HLFindType.HL_FIND_ALL)

    if sub_item is None:
        print(path + " not found.")
        return

    print("Information for {0}:\n".format(sub_item.get_path()))

    if isinstance(sub_item, hl.HLDirectoryFolder):
        print("  Type: Folder")
        print("  Size: {0} B".format(sub_item.get_size(True)))
        print("  Size On Disk: {0} B".format(sub_item.get_size_on_disk(True)))
        print("  Folders: {0}".format(sub_item.get_folder_count(True)))
        print("  Files: {0}".format(sub_item.get_file_count(True)))
    elif isinstance(sub_item, hl.HLDirectoryFile):
        print("  Type: File")
        print("  Extractable: {0}".format(sub_item.get_extractable()))
        print("  Size: {0} B".format(sub_item.get_size()))
        print("  Size On Disk: {0} B".format(sub_item.get_size_on_disk()))

    for idx in range(hl.Package.get_item_attribute_count()):
        try:
            attribute = hl.Package.get_item_attribute(sub_item, idx)
            print_attribute("  ", attribute, "")
        except hl.HLError:
            pass

    print()


def console_extract(item, name):
    if name is None:
        print("No argument for command extract supplied.")
        return

    if name == '.':
        sub_item = item
    else:
        sub_item = item.get_item_by_name(name, hl.HLFindType.HL_FIND_ALL)

    if sub_item is None:
        print(name + " not found.")
        return

    if not args.silent:
        print("Extracting {0}...".format(sub_item.get_name()))

    sub_item.extract(args.dest)

    if not args.silent:
        print("\nDone.")


def console_validate(item, name):
    if name is None:
        print("No argument for command validate supplied.")

    if name == '.':
        sub_item = item
    else:
        sub_item = item.get_item_by_name(name, hl.HLFindType.HL_FIND_ALL)

    if sub_item is None:
        print(name + " not found.")
        return

    if not args.silent:
        print("Validating %s...\n".format(sub_item.get_name()))

    validate(sub_item)

    if not args.silent:
        print("\nDone.")


def console_find(item, pattern):
    if pattern is None:
        print("No argument for command find supplied.")
        return

    if not args.silent:
        print("Searching for {0}...".format(pattern))

    sub_item = item.find_first(pattern, hl.HLFindType.HL_FIND_ALL)
    item_count = 0

    while sub_item is not None:
        item_count += 1

        if isinstance(sub_item, hl.HLDirectoryFolder):
            type_string = "folder"
        elif isinstance(sub_item, hl.HLDirectoryFile):
            type_string = "file"

        print("Found {0}: {1}".format(sub_item.get_path(), type_string))

        sub_item = item.find_next(sub_item, pattern, hl.HLFindType.HL_FIND_ALL)

    if not args.silent:
        if item_count != 0:
            print()

        print("  {0} item{1} found.\n".format(item_count,
                "" if item_count == 0 else "s"))


def console_type(item, name):
    if name is None:
        print("No argument for command type supplied.")
        return

    sub_item = item.get_item_by_name(name, hl.HLFindType.HL_FIND_FILES)

    if sub_item is None:
        print(name + " not found.")
        return

    if not args.silent:
        print("Type for {0}:\n".format(sub_item.get_path()))

    stream_created = False
    stream_opened = False

    try:
        stream = sub_item.create_stream()
        stream_created = True
        stream.open(hl.HLFileMode.HL_MODE_READ)
        stream_opened = True

        while True:
            try:
                c = stream.read_char().decode("utf-8")

                if (c >= " " and c <= "~") or c == "\n" or c == "\t":
                    print(c, end='')

            except hl.HLError:
                break
    except hl.HLError as ex:
        print(ex)
    finally:
        if stream_opened:
            stream.close()

        if stream_created:
            sub_item.release_stream(stream)

    if not args.silent:
        print("\nDone.")


# XXX Need to find example of nested packages to test this.
def console_open(item, name, current_package_id):
    if name is None:
        print("No argument for command open supplied.")
        return

    sub_item = item.get_item_by_name(name, hl.HLFindType.HL_FIND_FILES)

    if sub_item is None:
        print(name + " not found.")
        return

    stream_created = False
    stream_opened = False
    package_created = False
    package_opened = False

    try:
        stream = sub_item.create_stream()
        stream_created = True

        stream.open(hl.HLFileMode.HL_MODE_READ)
        stream_opened = True

        package_type = hl.Package.get_package_type_from_stream(stream)
        package_id = hl.Package.create_package(package_type)
        package_created = True

        hl.Package.bind_package(package_id)
        hl.Package.open_stream(stream, hl.HLFileMode.HL_MODE_READ)
        package_opened = True

        if not args.silent:
            print(sub_item.get_name() + " opened.")

        enter_console(package_id)

        hl.Package.close()

        if not args.silent:
            print(sub_item.get_name() + " closed.")

        hl.Package.delete_package(package_id)
        hl.Package.bind_package(current_package_id)

        stream.close()
        sub_item.release_stream(stream)
    except hl.HLError as ex:
        print(ex)
    finally:
        if stream_opened:
            stream.close()

        if stream_created:
            sub_item.release_stream(stream)

        if package_opened:
            hl.Package.close()

        if package_created:
            hl.Package.delete_package(package_id)

        hl.Package.bind_package(current_package_id)


def console_status():
    hlo = hl.HLOption
    size = hl.get_value(hlo.HL_PACKAGE_SIZE)
    allocs = hl.get_value(hlo.HL_PACKAGE_TOTAL_ALLOCATIONS)
    allocated = hl.get_value(hlo.HL_PACKAGE_TOTAL_MEMORY_ALLOCATED)
    used = hl.get_value(hlo.HL_PACKAGE_TOTAL_MEMORY_USED)

    print("Total size: {0} B".format(size))
    print("Total mapping allocations: {0}".format(allocs))
    print("Total mapping memory allocated: {0} B".format(allocated))
    print("Total mapping memory used: {0} B".format(used))

    for idx in range(hl.Package.get_attribute_count()):
        try:
            attribute = hl.Package.get_attribute(idx)
            print_attribute("", attribute, "")
        except hl.HLError as ex:
            print(ex)


def console_help():
    print("Valid commands:")
    print()

    if os.name == 'nt':
        print("dir <filter>    (Directory list.)")
    else:
        print("ls <filter>     (Directory list.)")

    print("cd <folder>     (Change directroy.)")
    print("info <item>     (Item information.)")
    print("extract <item>  (Extract item.)")
    print("validate <item> (Validate item.)")
    print("find <filter>   (Find item.)")
    print("type <file>     (Type a file.)")
    print("open <file>     (Open a nested package.)")
    print("root            (Go to the root folder.)")
    print("status          (Package information.)")

    if os.name == 'nt':
        print("cls             (Clear the screen.)")

    print("help            (Program help.)")
    print("exit            (Quit program.)")
    print()


def print_attribute(prefix, attribute, postfix):
    value = attribute.get()
    hlat = hl.HLAttributeType

    if (attribute.get_type() == hlat.HL_ATTRIBUTE_UNSIGNED_INTEGER and
            attribute.get_hexadecimal()):
        value = format(value, "#010x")

    print("{0}{1}: {2}{3}".format(prefix,
            attribute.get_name(), value, postfix))


def extract_item_start_callback(item):
    if not args.silent:
        if isinstance(item, hl.HLDirectoryFile):
            print("  Extracting {0}: ".format(item.get_name()), end="")
            progress_start()
        elif isinstance(item, hl.HLDirectoryFolder):
            print("  Extracting {0}:".format(item.get_name()))
        else:
            assert False


def extract_item_end_callback(item, success):
    if success:
        if not args.silent:
            name = item.get_name()
            size = item.get_size()

            if isinstance(item, hl.HLDirectoryFile):
                print("OK ({0} B)".format(size))
            elif isinstance(item, hl.HLDirectoryFolder):
                print("  Done {0}: OK ({1} B)".format(name, size))
            else:
                assert False
    else:
        if not args.silent:
            if isinstance(item, hl.HLDirectoryFile):
                error = hl.get_value(hl.HLOption.HL_ERROR_SHORT_FORMATED)
                print("Errored.\n    " + error)
            elif isinstance(item, hl.HLDirectoryFolder):
                print("  Done {0}: Errored".format(name))
            else:
                assert False
        else:
            path = item.get_path()

            if isinstance(item, hl.HLDirectoryFile):
                error = hl.get_value(HLOption.HL_ERROR_SHORT_FORMATED)
                print("  Error extracting {0}:\n    {1}".format(path, error))
            elif isinstance(item, hl.HLDirectoryFolder):
                print("  Error extracting {0}.".format(path))
            else:
                assert False


def file_progress_callback(item, bytes_extracted, bytes_total):
    progress_update(bytes_extracted, bytes_total)


def defragment_progress_callback(item, files_defragmented,
        files_total, bytes_defragmented, bytes_total, cancel):
    progress_update(bytes_extracted, bytes_total)


def progress_start():
    global progress_last
    progress_last = 0
    print("0%", end="")


def progress_update(bytes_extracted, bytes_total):
    global progress_last

    if not args.silent:
        if bytes_total == 0:
            progress = 100
        else:
            progress = bytes_extracted * 100 / bytes_total

        while progress >= progress_last + 10:
            progress_last += 10

            if progress_last == 100:
                print("100% ", end="")
            elif progress_last == 50:
                print("50%", end="")
            else:
                print(".", end="")


if __name__ == '__main__':
    main()
