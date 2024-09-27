#! /home/peko1112poko/miniconda3/envs/flaskpredict/bin/python
from wsgiref.handlers import CGIHandler
from app import app

CGIHandler().run(app)