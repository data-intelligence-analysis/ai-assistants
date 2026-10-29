FROM python:3.11-slim
WORKDIR /workspace
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8501
COPY invoice_dashboard_app.py .
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
