# image-lab — Docker instructions

Build the Docker image (run from repository root):

```bash
docker build -t image-lab:latest .
```

Run the container, exposing port 5000:

```bash
docker run --rm -p 5000:5000 image-lab:latest
```

The Flask app will be available at `http://localhost:5000`.

Notes:
- The `Dockerfile` installs a small set of OS libraries commonly required by `opencv-python` wheels.
- For production, consider using a WSGI server (e.g. `gunicorn`) instead of the Flask development server.
