ARG  CODE_VERSION=latest
FROM python:3.12.3-bookworm

WORKDIR /cl-data-dashboard

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/curiouslearning/cl-data-dashboard.git .

RUN pip3 install -r requirements.txt

ENV PORT=8501

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
