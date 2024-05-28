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

COPY .streamlit/secrets.toml .streamlit/secrets.toml

EXPOSE 8080

CMD ["streamlit", "run", "Engagement.py", "--server.port=8080"]