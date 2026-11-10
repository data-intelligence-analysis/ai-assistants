# Use a slim, secure base image
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required for potential file/audio processes
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Cache Python dependencies inside image layers
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bring over codebase architectures
COPY agent.py config.json state.json* ./

# Command instructions default to text-based summary generation output 
ENV SALES_AGENT_DOCKER=1
EXPOSE 3000
ENTRYPOINT ["python", "agent.py"]
CMD ["--format", "text"]
