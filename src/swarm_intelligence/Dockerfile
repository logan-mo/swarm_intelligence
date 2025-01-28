# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
# RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables if required
ENV HOST=0.0.0.0
ENV BASE_PORT=5000
ENV PORT_RANGE=10

# Create a directory for logs (this will be mapped to a volume)
RUN mkdir -p /logs

# Command to run the agent script
CMD ["python", "agent.py"]
