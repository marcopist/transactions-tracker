FROM mcr.microsoft.com/vscode/devcontainers/base:ubuntu

RUN mkdir -p /db/data/transactions

RUN apt-get update -y && apt-get upgrade -y && \
    apt-get install -y python3 python3-pip && \ 
    pip3 install --upgrade pip && \
    curl --proto '=https' --tlsv1.2 https://sh.rustup.rs -sSf | sh -s -- -y