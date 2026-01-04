import json
import pika
import os

class Publisher:
    def __init__(self, logger):
        self._logger = logger

        self.HOST = os.getenv('AMQP_HOST')
        self.USER = os.getenv('AMQP_USER')
        self.PASS = os.getenv('AMQP_PASS')
        self.VIRTUAL_HOST = os.getenv('AMQP_VHOST', '/')

        self.EXCHANGE = os.getenv('AMQP_EXCHANGE', 'robot-shop')
        self.TYPE = os.getenv('AMQP_EXCHANGE_TYPE', 'direct')
        self.ROUTING_KEY = os.getenv('AMQP_ROUTING_KEY', 'orders')

        # 🔥 FAIL FAST (VERY IMPORTANT)
        missing = [k for k, v in {
            "AMQP_HOST": self.HOST,
            "AMQP_USER": self.USER,
            "AMQP_PASS": self.PASS
        }.items() if not v]

        if missing:
            raise RuntimeError(f"Missing RabbitMQ env vars: {', '.join(missing)}")

        self._params = pika.ConnectionParameters(
            host=self.HOST,
            virtual_host=self.VIRTUAL_HOST,
            credentials=pika.PlainCredentials(self.USER, self.PASS),
            heartbeat=30,
            blocked_connection_timeout=30
        )

        self._conn = None
        self._channel = None

    def _connect(self):
        if not self._conn or self._conn.is_closed:
            self._conn = pika.BlockingConnection(self._params)
            self._channel = self._conn.channel()
            self._channel.exchange_declare(
                exchange=self.EXCHANGE,
                exchange_type=self.TYPE,
                durable=True
            )
            self._logger.info(
                f'connected to broker {self.HOST} vhost={self.VIRTUAL_HOST}'
            )

    def publish(self, msg, headers=None):
        if not self._conn or self._conn.is_closed:
            self._connect()

        self._channel.basic_publish(
            exchange=self.EXCHANGE,
            routing_key=self.ROUTING_KEY,
            body=json.dumps(msg).encode(),
            properties=pika.BasicProperties(headers=headers or {})
        )

        self._logger.info('message sent to queue')

    def close(self):
        if self._conn and self._conn.is_open:
            self._conn.close()
