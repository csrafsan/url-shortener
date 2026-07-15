# 1. Use a lightweight Python base image
FROM python:3.11-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy our dependencies and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy your local database.py and main.py files inside
COPY . .

# 5. Expose the default port FastAPI runs on
EXPOSE 8080

# 6. Command to start the app using uvicorn inside the container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]