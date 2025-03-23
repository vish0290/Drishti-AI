FROM python:3.11.slim

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY ,/backend /app

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 8282


# Start the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8282"]


