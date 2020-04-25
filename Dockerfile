FROM debian:buster

RUN apt-get update && apt-get install -y \
  python3 \
  python3-pip \
  apt-transport-https \
  ca-certificates \
  curl \
  gnupg-agent \
  software-properties-common && \
  curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add - && \
  add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian  $(lsb_release -cs) stable" && \
  apt-get update && \
  apt-get install docker-ce-cli && \
  pip3 install pexpect

# Set the entry point
ENTRYPOINT ["/init"]

# Install services
COPY services /etc/services.d

# Install init.sh as init script
COPY init.sh /etc/cont-init.d/

# Install backup script
COPY backup.py /backup.py

# Download and extract s6 init
ADD https://github.com/just-containers/s6-overlay/releases/download/v1.21.8.0/s6-overlay-amd64.tar.gz /tmp/
RUN tar xzf /tmp/s6-overlay-amd64.tar.gz -C /


