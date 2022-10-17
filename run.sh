#!/bin/bash

. venv/bin/activate
FLASK_DEBUG=1 flask run --host 0.0.0.0
