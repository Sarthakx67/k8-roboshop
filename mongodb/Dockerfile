FROM mongo:5
# Copy all .js files from the build context (this folder) into Mongo's init directory.
# The official mongo image will automatically run scripts in /docker-entrypoint-initdb.d/
# ON FIRST START only (i.e., when the database data directory is empty).
# These scripts are commonly used to create databases, users, collections, and seed data.
COPY *.js /docker-entrypoint-initdb.d/
