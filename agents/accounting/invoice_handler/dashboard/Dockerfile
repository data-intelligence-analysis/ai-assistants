FROM python:3.11-slim
WORKDIR /workspace
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8501
COPY dashboard/invoice_dashboard_app.py .
COPY dashboard/invoice_sample.csv /workspace/invoice_sample.csv
ENTRYPOINT ["streamlit", "run", "/workspace/invoice_dashboard_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
