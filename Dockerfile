# Use a lightweight Python image as the base
FROM python:3.12-slim-bookworm

# Set the working directory in the container
WORKDIR /app

# Copy only the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Streamlit configuration
COPY .streamlit/config.toml /root/.streamlit/config.toml

# Copy the favicon
COPY favicon.png .

# Copy the rest of the application code
COPY . .

# Initialize the SQLite database
RUN python database_setup.py

# Expose the port Streamlit runs on
EXPOSE 8501

# Command to run the Streamlit application
CMD ["streamlit", "run", "Welcome.py", "--server.port=8501", "--server.address=0.0.0.0"]
