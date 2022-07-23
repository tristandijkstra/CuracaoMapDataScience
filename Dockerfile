# 
FROM python:3.8

WORKDIR /dash

COPY requirements.txt .
RUN pip install -r requirements.txt


COPY ./geojsondata ./geojsondata
COPY ./processed ./processed
COPY ./rawdata ./rawdata
COPY ./assets ./assets


COPY electiondashboard.py .
COPY extractElection.py .
COPY extractmap.py .
COPY misc.py .


EXPOSE 8050


CMD ["python", "electiondashboard.py"]
