# jupyter-cpp-wrapperkernel

## Use with Docker

* `git clone git@github.com:alex-zach/jupyter-cpp-wrapperkernel.git`
* `docker build -t jupyter-cpp-wrapperkernel:latest .`
* `docker run -p 8888:8888 --device /dev/fuse --cap-add SYS_ADMIN jupyter-cpp-wrapperkernel:latest`

## Magics
TODO

## Licence
[MIT](LICENSE.txt)

inspired by [XaverKlemenschits/jupyter-c-kernel](https://github.com/XaverKlemenschits/jupyter-c-kernel)