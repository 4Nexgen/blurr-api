# Use the official Python image
FROM python:3.10

# Set working directory
WORKDIR /app

# Install Rust and Cargo
RUN apt-get update && apt-get install -y curl \
    && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y \
    && . "$HOME/.cargo/env" \
    && rustc --version && cargo --version

# Set environment path for Cargo
ENV PATH="/root/.cargo/bin:${PATH}"

# Copy files
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 8000

# Start the FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
