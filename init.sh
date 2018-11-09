#!/bin/bash

alembic upgrade head
hug -f app.py -c init_user