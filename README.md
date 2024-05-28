# cl-data-dashboard
Curious Learning External Dashboard

**To run locally**

1. Install python 3.12.0 - https://www.python.org/downloads/release/python-3123/
2. git clone https://github.com/curiouslearning/cl-data-dashboard.git
3. cd to ./cl-data-dashboard
4. pip install -r requirements.txt
5. streamlit run Engagement.py

OR 
docker build --no-cache --platform linux/amd64  -t gcr.io/dataexploration-193817/cl-data-dashboard:latest .
docker push gcr.io/dataexploration-193817/cl-data-dashboard:latest