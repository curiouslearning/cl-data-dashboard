ARG  CODE_VERSION=latest
FROM python:3.12.3-bookworm

WORKDIR /cl-data-dashboard

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    apt-transport-https \
    ca-certificates

# Add the Google Cloud SDK distribution URI as a package source
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" \
    | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list

# Add Google's public key
RUN curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -

# Update and install the Google Cloud SDK
RUN apt-get update && apt-get install -y google-cloud-sdk

# Set environment variable for gcloud
ENV PATH $PATH:/root/google-cloud-sdk/bin

# Set environment variable for the secret
ENV SECRET_NAME="streamlit-secrets"

# Ensure the directory for the secrets exists
RUN mkdir -p /app/.streamlit

RUN git clone https://github.com/curiouslearning/cl-data-dashboard.git .

RUN pip3 install -r requirements.txt

#COPY dataexploration-193817-df8853d577aa.json /app/dataexploration-193817-df8853d577aa.json


#RUN  gcloud config set account streamlit-data-dash@dataexploration-193817.iam.gserviceaccount.com
RUN gcloud secrets versions access latest --project="dataexploration-193817" --secret="streamlit-secrets" > .streamlit/secrets.toml


EXPOSE 8080

CMD ["streamlit", "run", "Engagement.py", "--server.port=8080"]