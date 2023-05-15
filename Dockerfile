FROM jupyter/minimal-notebook

ENV DOCKER_STACKS_JUPYTER_CMD=notebook

USER root

# Install vim, ssh, git, go fuse3 and supervisor
RUN apt-get update
RUN apt-get install -y vim openssh-client git golang-go fuse3 supervisor

WORKDIR /tmp

# install fusevin
RUN git clone https://github.com/rapgru/fusevin.git
RUN cd fusevin && go build && cd ..
RUN cp fusevin/fusevin /opt/
RUN mkdir /mnt/fusevin
RUN chmod 777 /mnt/fusevin

COPY ./ jupyter_cpp_wrapperkernel/

# install kernel
RUN pip install --no-cache-dir jupyter_cpp_wrapperkernel/ > piplog.txt
USER $NB_USER
RUN install_cpp_wrapperkernel --user > installlog.txt

# create workspace folder
WORKDIR /home/$NB_USER/
RUN mkdir workspace

# create supervisord config
WORKDIR /root
USER root
COPY ./supervisord.conf supervisord.conf
RUN sed -i "s/\${NB_USER}/$NB_USER/" supervisord.conf

# allow fuse for all users
RUN echo "user_allow_other" >> /etc/fuse.conf

CMD ["/usr/bin/supervisord", "-c", "supervisord.conf"]
