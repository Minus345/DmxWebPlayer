# Dmx Web Player

## Development:
inti sqlite db: `flask --app app init-db`

## Deployment with gunicorn
### Ubuntu
`python -m venv /path/to/new/virtual/environment`  
`source <venv>/bin/activate`  
`pip install -r requirements.txt`  
start with:  
`gunicorn app:app`


