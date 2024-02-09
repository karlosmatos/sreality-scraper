# Use the official Docker Hub Postgres image
# See https://hub.docker.com/_/postgres/
FROM postgres:latest

# Set environment variables
ENV POSTGRES_USER yourusername
ENV POSTGRES_PASSWORD yourpassword
ENV POSTGRES_DB yourdatabase

# Expose the PostgreSQL port
EXPOSE 5432

# Add a VOLUME to allow backup of config, logs and databases
VOLUME  ["/etc/postgresql", "/var/log/postgresql", "/var/lib/postgresql"]

# Set the default command to run when starting the container
CMD ["postgres"]