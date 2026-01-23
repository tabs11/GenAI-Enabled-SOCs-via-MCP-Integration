# 1. Use a lightweight Python base image
FROM python:3.10-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Install system utilities (curl is useful for healthchecks)
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# 4. Copy the dependencies file and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy all your code into the container
COPY . .

# 6. Expose the port that Streamlit uses
EXPOSE 8501

# 7. Command to start the application
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]