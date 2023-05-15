from operator import is_
import grpc

from ipykernel.kernelbase import Kernel
from importlib import metadata
from os import environ, path, remove, rmdir
from tempfile import NamedTemporaryFile, mkdtemp
from threading import Thread
from copy import copy
from re import compile

from jupyter_cpp_wrapperkernel.magicparsers import last_value_parser, list_parser

from .constants import *
from .vin.vin_pb2_grpc import FuseVinStub
from .vin.vin_pb2 import StartStdinNotifyRequest, StdinContent, DestroyPuppetRequest, Empty as GRPCEmpty
from .kernelsubprocess import KernelSubprocess

_distribution = metadata.distribution('jupyter_cpp_wrapperkernel')

class CPPKernel(Kernel):
    implementation = _distribution.name
    implementation_version = _distribution.version

    banner = 'C++ Kernel.\n' \
             'Uses g++ to compile and run C++20 source code. To use realistic input the tool \'fusevin\' is used.\n' \
             'Magics enable the possibility to use multiple \'virtual\' source code files and other c++ standards.\n'
    
    language = 'C++'
    language_version = 'C++20'
    language_info = {'name': 'text/x-c',
                     'mimetype': 'text/x-c',
                     'file_extension': '.cpp'}

    def __init__(self, **kwargs):
        super(CPPKernel, self).__init__(**kwargs)
        self._allow_stdin = True

        self.print_infos = True

        self.linkMaths = True
        self.wall = True
        self.wextra = True
        self.werror = False
        self.cppstandard = 'c++20'

        self._grpc_channel = grpc.insecure_channel(environ.get('FUSEVIN_URL', 'localhost:50051'))
        self._vin_stub = FuseVinStub(self._grpc_channel)

        self._tempdir = mkdtemp()
        self._tempfiles = []

        self._libraries = {}

        self._magic_parsers = {
            'cppflags': {
                'default': [],
                'parser': list_parser
            },
            'ldflags': {
                'default': [],
                'parser': list_parser
            },
            'args': {
                'default': [],
                'parser': list_parser
            },
            'file': {
                'default': None,
                'parser': last_value_parser
            }
        }
        self._magic_pattern = compile(r'\/\/%(' + r'|'.join(self._magic_parsers.keys()) + r'):(.*)')
        self._include_pattern = compile(r'#include[^\S\n\r]*"(.*)"')

    def _print(self, contents, channel=CHANNEL_STDOUT, info=False):
        '''Prints content to juypter'''

        if channel in [CHANNEL_STDOUT, CHANNEL_STDERR]:
            if not info or self.print_infos:
                self.send_response(self.iopub_socket, 'stream', {'name': channel, 'text': contents})
        else:
            raise RuntimeError('Invalid Channel \'{}\''.format(channel))

    def _run_subprocess(self, cmd, stdin=None, print=True):
        '''Starts a subprocess'''

        if print:
            printfunc = self._print
        else:
            printfunc = lambda *args: None

        return KernelSubprocess(cmd, printfunc, stdin)

    def _start_compile(self, source_filename, binary_filename, cppflags=[]):
        '''Start a subprocess that compiles the given file'''

        cppflags = copy(cppflags)

        if self.linkMaths: cppflags += ['-lm']
        if self.wall: cppflags += ['-Wall']
        if self.wextra: cppflags += ['-Wextra']
        if self.werror: cppflags += ['-Werror']
        if not any(flag.startswith('-std=') for flag in cppflags):
            cppflags += [f'-std={self.cppstandard}']

        cppflags += [f'-I{self._tempdir}', '-c']

        self._print(f'[C++ Kernel] Compiling with flags \'{" ".join(cppflags)}\'.\n', info=True)

        cmd = ['g++', source_filename] + cppflags + ['-o', binary_filename]
        return self._run_subprocess(cmd, print=self.print_infos)

    def _start_link(self, executable_filename, binary_filename, libs, ldflags=[]):
        '''Start a subprocess that links the given binaries'''

        alllibs = set()
        todolibs = set(libs)

        while len(todolibs) > 0:
            lib = todolibs.pop()

            alllibs.add(lib)
            todolibs |= set([*self._libraries[lib]['headerdeps'], *self._libraries[lib]['binarydeps']])
            todolibs -= alllibs

        self._print(f'[C++ Kernel] Linking with flags \'{" ".join(ldflags)}\'.\n', info=True)

        cmd = ['g++', binary_filename] + list(map(lambda l: self._libraries[l]['binary'], alllibs)) + ['-o', executable_filename] + ldflags
        return self._run_subprocess(cmd, print=self.print_infos)

    def _tempfile(self, **kwargs):
        '''Create a new temp file to be deleted when the kernel shuts down'''

        kwargs['delete'] = False
        kwargs['mode'] = 'w'
        kwargs['dir'] = self._tempdir
        
        file = NamedTemporaryFile(**kwargs)
        self._tempfiles.append(file.name)
        return file

    def _cleanup_tempfiles(self):
        '''Remove all the temporary files created by the kernel'''

        for file in self._tempfiles:
            if(path.exists(file)):
                remove(file)

    def _start_virtualin_thread(self):
        '''Starts a thread that uses fusevin to create a virtual input-file'''

        puppet = self._vin_stub.CreatePuppet(GRPCEmpty())

        def handle_input_requests(vin_stub, raw_inp):
            for _ in vin_stub.StartStdinNotify(StartStdinNotifyRequest(id=puppet.id)):
                inp = raw_inp()
                vin_stub.SupplyStdinContent(StdinContent(id=puppet.id, payload=inp))

        
        input_thread = Thread(target=handle_input_requests, args=(self._vin_stub, self.raw_input))
        input_thread.daemon = True
        input_thread.start()
        
        def delete():
            self._vin_stub.DestroyPuppet(DestroyPuppetRequest(id=puppet.id))

        return puppet.vin_filename, delete

    def _preprocess_code(self, code):
        magics = {} 
        libs = []
        for key in self._magic_parsers.keys():
            magics[key] = copy(self._magic_parsers[key]['default'])

        actual_code = ''

        for line in code.splitlines():

            # filter magic
            m = self._magic_pattern.fullmatch(line)
            i = self._include_pattern.fullmatch(line)
            if m is not None:
                key, value = m.group(1), m.group(2)
                magics[key] = self._magic_parsers[key]['parser'](value, magics[key])
                actual_code += '\n'
            elif i is not None:
                header = i.group(1)
                header_name = ''.join(header.split('.')[0:-1])
                if header_name in self._libraries.keys():
                    libs.append(header_name)
                    actual_code += f'#include "{self._libraries[header_name]["header"]}"\n'
                else:
                    actual_code += line + '\n'
            else:
                actual_code += line + '\n'

        return magics, libs, actual_code

    def do_execute(self, code, silent, store_history=True, user_expressions=None, allow_stdin=True):
        '''Execute Code from Jupyter'''

        magics, libs, code = self._preprocess_code(code)

        is_lib = False
        is_header = False
        
        if magics['file'] is not None:
            split = magics['file'].split('.')
            name = ''.join(split[0:-1])
            suffix = split[-1]
            
            if suffix == 'cpp':
                is_lib = True
                self._print('[C++ Kernel] Using file as library. It will be linked, if a header with the same name is included.\n')
            elif suffix in ['h', 'hpp']:
                is_header = True
                self._print('[C++ Kernel] Using file as header.\n')
            else:
                self._print(f'[C++ Kernel] Supplied filename-suffix ({suffix}) is not one of the supported: .cpp, .h, .hpp and will be ignored.\n')

        if is_header:
            with self._tempfile(suffix='.h') as header_file:
                header_file.write(code)
                header_file.flush()
                self._libraries[name] = {
                    **self._libraries.get(name, {}),
                    'header': header_file.name,
                    'headerdeps': libs
                }

                self._print('[C++ Kernel] Saved as header', info=True)
        else:
            with self._tempfile(suffix='.cpp') as source_file, self._tempfile(suffix='.out') as binary_file:
                source_file.write(code)
                source_file.flush()
                p = self._start_compile(source_file.name, binary_file.name, magics['cppflags'])
                p.join()

                if p.returncode != 0:
                    return {'status': 'error', 'ename' : 'CompilationError', 'evalue' : 'g++ failed with code {}'.format(p.returncode)}

            if is_lib:
                self._libraries[name] = {
                    **self._libraries.get(name, {}),
                    'binary': binary_file.name,
                    'binarydeps': libs
                }

                self._print('[C++ Kernel] Saved as binary', info=True)
            else:
                with self._tempfile(suffix='.o') as executable_file:
                    p = self._start_link(executable_file.name, binary_file.name, libs, magics['ldflags'])
                    p.join()

                    if p.returncode != 0:
                        return {'status': 'error', 'ename' : 'LinkingError', 'evalue' : 'g++ failed with code {}'.format(p.returncode)}

                self._print('[C++ Kernel] Running the compiled programm.\n\n', info=True)

                virtual_stdin, delete_vin = self._start_virtualin_thread()

                with open(virtual_stdin, 'r') as vin_file:
                    p = self._run_subprocess([executable_file.name], stdin=vin_file)
                    p.join()

                delete_vin()
                
                self._print('\n[C++ Kernel] Programm exited with code {}.\n'.format(p.returncode), info=True)

        return {'status': 'ok', 'execution_count': self.execution_count, 'payload': [], 'user_expressions': {}}

    def do_shutdown(self, restart):
        '''Do a shutdown of the kernel'''
        self._cleanup_tempfiles()
        rmdir(self._tempdir)

        return super().do_shutdown(restart)
