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
COPY gunicorn_start.sh .


EXPOSE 80


# CMD ["gunicorn"  , "-b", "0.0.0.0:8000", "electiondashboard:flapp"]
ENTRYPOINT ["./gunicorn_start.sh"]