#!/bin/sh
gunicorn electiondashboard:flapp -w 2 --threads 2 -b 0.0.0.0:8000
