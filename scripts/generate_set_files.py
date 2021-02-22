#!/usr/bin/env python3
#
# Generate Gentoo package set files based on an YAML input file.
#
import argparse
import yaml
import os
import re
import sys


def error(msg):
    """
    Print an error message and exit.
    """
    sys.stderr.write('ERROR: ' + msg + '\n')
    sys.exit(1)


def is_supported(package, arch):
    """
    Check if a given package is supported on the given architecture.

    package: dict having at least a 'name' key, optionally 'exclude_on' (list) and 'include_on' (str)
    arch: str representing an architecture name
    """
    print(package, arch)
    return package is None \
        or not arch in package.get('exclude_on', []) \
        and arch in package.get('include_on', [arch])


def parse_args():
    """
    Parse the input arguments and return the populated namespace.
    """
    parser = argparse.ArgumentParser(description='Generate Gentoo package set files.')
    parser.add_argument('-y', '--yaml-file', dest='yamlfile', required=True,
                        help='YAML input file with architecture and set definitions.')
    parser.add_argument('-d', '--sets-dir', dest='setsdir', required=True,
                        help='Output directory for storing the set files.')
    args = parser.parse_args()
    return args


def parse_yaml_file(filename):
    """
    Parse the given YAML file, and return the specified architecture and set defintions.
    """
    archs = []
    sets = []

    if not os.path.exists(filename):
        error(f"input file {filename} does not exist!")

    with open(filename, 'r') as stream:
        try:
            y = yaml.safe_load(stream)
            archs = y['eessi_archs']
            sets = y['eessi_sets']
        except yaml.YAMLError as exc:
            error("YAML file could not be parsed.\n" + str(exc))

    return (archs, sets)


def make_atom(package_name, package_dict):
    """
    Generate a package atom that is compatible with ebuild/emerge, see:
    https://dev.gentoo.org/~zmedico/portage/doc/man/ebuild.5.html
    """
    atom = package_name
    if not package_dict:
        package_dict = {}

    if 'version' in package_dict:
        atom = '=' + atom + '-' + str(package_dict['version'])

    if 'overlay' in package_dict:
        atom += '::' + package_dict['overlay']

    return atom + '\n'


def main():
    """
    Main function.
    """
    args = parse_args()
    archs, sets = parse_yaml_file(args.yamlfile)

    if not os.path.exists(args.setsdir):
        error(f"output directory {args.setsdir} does not exist.")

    # Create a set file with the supported packages for every listed architecture and set definition
    for set_name, set in sets.items():
        for arch in archs:
            supported_packages = [
                make_atom(package_name, package_dict)
                for package_name, package_dict in set['packages'].items()
                if is_supported(package_dict, arch)
            ]
            set_filename = os.path.join(args.setsdir, f"{set_name}-{arch}")
            with open(set_filename, 'w') as setfile:
                setfile.writelines(supported_packages)
            print(f"Created set file {set_filename}.")


if __name__ == '__main__':
    main()
