FROM python:3.11-slim
WORKDIR /workspace
RUN pip install --no-cache-dir streamlit pandas google-api-python-client google-auth
EXPOSE 8501
COPY app.py .
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
