ARG CODE_VERSION=latest
ARG STREAMLIT_SECRETS

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

#Update and install the Google Cloud SDK
RUN apt-get update && apt-get install -y google-cloud-sdk
RUN pip3 install --upgrade google-cloud-secret-manager

# Set environment variables for gcloud
ENV PATH $PATH:/root/google-cloud-sdk/bin
ENV PROJECT_ID="dataexploration-193817"

# Clone the repository and install dependencies
RUN git clone https://github.com/curiouslearning/cl-data-dashboard.git .
RUN pip3 install -r requirements.txt



RUN echo " S = $STREAMLIT_SECRETS"

RUN echo "$STREAMLIT_SECRETS" > .streamlit/secrets.toml
EXPOSE 8080

CMD ["streamlit", "run", "Engagement.py", "--server.port=8080"]
