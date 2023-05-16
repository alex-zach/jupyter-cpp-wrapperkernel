# Jupyter C++ Wrapper Kernel

The Jupyter C++ Wrapper Kernel is a powerful tool that allows you to execute C++ code directly within Jupyter notebooks. With this wrapper kernel, you can compile and run C++ code seamlessly, with added support for input handling.

## Installation

### Docker

To install the Jupyter C++ Wrapper Kernel using Docker, follow these steps:

1. Clone the repository:

   ```shell
   git clone git@github.com:alex-zach/jupyter-cpp-wrapperkernel.git
   ```

2. Build the Docker image:

   ```shell
   docker build -t jupyter-cpp-wrapperkernel:latest .
   ```

3. Run the Docker container:

   ```shell
   docker run -p 8888:8888 --device /dev/fuse --cap-add SYS_ADMIN jupyter-cpp-wrapperkernel:latest
   ```

   The Jupyter notebook server will be accessible at `http://localhost:8888`. A security token will be provided in the Docker container's shell upon startup.

### Local Install

To install the wrapper kernel locally, your machine must be running Linux with the `fuse` kernel module enabled. Please refer to the `Dockerfile` for the detailed installation process.

## Usage

Once you have installed the kernel, you can use it just like any other Jupyter kernel. Create a new notebook and select `C++ Wrapperkernel` as the kernel, or change the kernel of an existing notebook to `C++ Wrapperkernel`.

## Magics

The Jupyter C++ Wrapper Kernel supports the use of "magics" in comments to modify the compile behavior of your code. Magics have the following format: `//%key:value`.

The currently supported magics are:

* `cppflags`: A comma-separated list of g++ compile flags.
* `ldflags`: A comma-separated list of g++ linking flags.
* `args`: A comma-separated list of command line arguments to be passed to the program.
* `file`: The filename. If it ends with `.cpp`, it is considered a library file and won't be executed. If it ends with `.hpp` or `.h`, the file is treated as a header file and saved. Saved header files can be included using `#include "name.h{pp}"`. If there is a `.cpp` file with the same name, it will be linked.

Feel free to customize the magics according to your requirements.

## Additional Output
To show additional output, just run the code `toggle_infos` as code cell.

## License

This project is licensed under the MIT License. For more information, please see the [LICENSE.txt](LICENSE.txt) file.

## Acknowledgements

This project was inspired by [XaverKlemenschits/jupyter-c-kernel](https://github.com/XaverKlemenschits/jupyter-c-kernel).

The readme has been improved with contributions from ChatGPT.