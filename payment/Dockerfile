FROM python:3.9-alpine
EXPOSE 8080
USER root
WORKDIR /app
COPY requirements.txt /app/
RUN apk --no-cache add build-base linux-headers
RUN pip install --upgrade setuptools
RUN pip install -r requirements.txt
COPY *.py /app/
COPY payment.ini /app/
# Sets default environment variables for AMQP (RabbitMQ) credentials; application reads these at runtime
# (these can be overridden via `docker run -e ...` or compose/k8s env vars).
CMD ["uwsgi", "--ini", "payment.ini"]