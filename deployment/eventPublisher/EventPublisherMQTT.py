# ========================LICENSE_START=================================
# Event Publisher MQTT version
# %% 
# Copyright (C) 2024 - 2025 Vodafone
# %%
# Licensed under the MIT License;
# =========================LICENSE_END==================================

from flask import Flask, jsonify, request
from binascii import hexlify
from prometheus_client import start_http_server, Counter
from waitress import serve
import asn1tools
import os
import config
import time
import random
import logging
import paho.mqtt.client as mqtt

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s',
                    handlers=[
                        logging.FileHandler('app.log'),
                        logging.StreamHandler()
                    ])

# MQTT client configuration
mqtt_client = mqtt.Client()
if hasattr(config, 'MQTT_USERNAME'):
    mqtt_client.username_pw_set(config.MQTT_USERNAME, config.MQTT_PASSWORD)
mqtt_client.connect("localhost", 1883, keepalive=60)
mqtt_client.loop_start()  # start background network thread

# ASN.1 setup
DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'asn')
asn1_files = [os.path.join(DATA_FOLDER, f) for f in os.listdir(DATA_FOLDER) if f.endswith('.asn')]
encoder = asn1tools.compile_files(
    asn1_files, codec='uper', any_defined_by_choices=None, encoding='utf-8', numeric_enums=False
)

# Prometheus metric
REQUEST_COUNT = Counter(config.MESSAGES_COUNT_METRICS, 'Number of messages processed', ['sub_service'])

# Define a POST route with path variable
@app.route('/api/publish/<string:sub_service>/<string:sub_service_group>/<string:geohash>', methods=['POST'])
def publish_message(sub_service, sub_service_group, geohash):

    app.logger.info('Publishing endpoint reached')
    app.logger.info(' - Inputs: %s, %s, %s', sub_service, sub_service_group, geohash)

    geo_level = str(len(geohash))
    geohash_topic = '/'.join(list(geohash))
    key = f'v2x/{sub_service}/{sub_service_group}/g{geo_level}/{geohash_topic}'
    app.logger.info("MQTT topic: %s", key)

    # Get JSON data from the request body
    data = request.get_json()
    sub_service_upper = sub_service.upper()
    encoded = encoder.encode(sub_service_upper, data)
    message = hexlify(encoded).decode('ascii')

    app.logger.debug('Encoded: %s', message)
    app.logger.debug('Decoded: %s', encoder.decode(sub_service_upper, encoded, check_constraints=False))

    time.sleep(random.uniform(0.5, 1.5))
    REQUEST_COUNT.labels(sub_service=sub_service_upper).inc()

    # Send the message to MQTT
    send_message(message, key)

    # Create a response
    response = {
        'sub_service': sub_service_upper,
        'key': key,
        'topic': key,
        'message': 'Message processed successfully'
    }

    return jsonify(response)


def send_message(data, key):
    """Publish message to MQTT broker"""
    result = mqtt_client.publish(topic=key, payload=data, qos=1)
    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        app.logger.info("Message sent successfully to MQTT topic %s", key)
    else:
        app.logger.error("Failed to send message to MQTT topic %s: %s", key, result.rc)
    return jsonify({'status': 'Message sent successfully'})


if __name__ == '__main__':

    # Start Prometheus metrics server
#    start_http_server(config.PROMETHEUS_SERVER)
    
    # Start Waitress server
    serve(app, host="0.0.0.0", port=5005)

