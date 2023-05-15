import json
import sys
import argparse

from jupyter_client.kernelspec import KernelSpecManager
from tempfile import TemporaryDirectory
from os import path, geteuid

kernelspec = {
    'argv': [
        'python3',
        '-m',
        'jupyter_cpp_wrapperkernel',
        '-f',
        '{connection_file}'
    ],
    'display_name': 'C++ Wrapperkernel',
    'language': 'C++'
}

def do_install(user=True, prefix=None):
    with TemporaryDirectory() as td:
        with open(path.join(td, 'kernel.json'), 'w') as f:
            json.dump(kernelspec, f)

        print('Installing kernel spec...')
        KernelSpecManager().install_kernel_spec(td, 'cpp', user=user, prefix=prefix)

def _is_root():
    try:
        return geteuid() == 0
    except AttributeError:
        return False  # assume not an admin on non-Unix platforms

def main():
    parser = argparse.ArgumentParser(description='Install KernelSpec for C++ Wrapperkernel')
    
    install_location = parser.add_mutually_exclusive_group()
    install_location.add_argument('--user',
        help='Install KernelSpec in user homedirectory',
        action='store_false' if _is_root() else 'store_true'
    )
    install_location.add_argument(
        '--sys-prefix',
        help='Install KernelSpec in sys.prefix. Useful in conda / virtualenv',
        action='store_true',
        dest='sys_prefix'
    )
    install_location.add_argument(
        '--prefix',
        help='Install KernelSpec in this prefix',
        default=None
    )

    args = parser.parse_args()

    if args.sys_prefix:
        prefix = sys.prefix
        user = None
    elif args.user:
        prefix = None
        user = True
    else:
        prefix = args.prefix
        user = None

    do_install(user=user, prefix=prefix)


if __name__ == '__main__':
    main()