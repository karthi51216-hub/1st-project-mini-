FROM python:3.11-slim

WORKDIR /app

# install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy project
COPY . .

# expose port
EXPOSE 8000

# run app with gunicorn (production server)
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8000", "mini_crm.app:app"]