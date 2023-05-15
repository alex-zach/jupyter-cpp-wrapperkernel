from ipykernel.kernelapp import IPKernelApp
from .cppkernel import CPPKernel

IPKernelApp.launch_instance(kernel_class=CPPKernel)