#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Checks host at regular intervals and publish status information in a Kafka queue
# @see Adapt defines.py to match current Kafka installation, there's no need to edit it
#      for running this project with local containers. You may even keep defines.py as
#      it is and just change main Object constructor or Connect/Publish methods
#
import sys
import json
from time  import sleep
from kafka import KafkaProducer

import defines
import siteChecker

# Kafka producer
class Producer:
    # Constructor. Default to [host], or None
    def __init__(self, host=defines.KAFKA_HOST):
        self._producer = None
        self.Connect(host)                  # 2nd stage constructor or standalone method

    # Connect - Connect to kafka queue
    # @param host (string) Kafka location, example: 'localhost:9092'
    # @throws (Exception)
    def Connect(self, host=None):
        if host is None: return
        if defines.KAFKA_PROTOCOL=='':      # Plain/local/unencrypted kafka connection
            self._producer = KafkaProducer(
                bootstrap_servers = [host],
                value_serializer  = lambda x: json.dumps(x).encode('utf-8')
            )
        else:                               # SSL, setup some serious encrypted connection (cloud ?)
            self._producer = KafkaProducer(
                bootstrap_servers = [host],
                security_protocol = defines.KAFKA_PROTOCOL,
                ssl_check_hostname=True,
                ssl_cafile=defines.KAFKA_CA,
                ssl_certfile=defines.KAFKA_CERT,
                ssl_keyfile=defines.KAFKA_KEY,
                value_serializer  = lambda x: json.dumps(x).encode('utf-8')
            )

    # Publish - Check URL and publish information to kafka [channel]
    # @param hostname (string) URL to check, example: 'http://www.google.com'
    # @param content  (string) Optional. Regexp to check inside [hostname], bs4 compliant
    # @param channel  (string) Name of the published kafka channel
    # @throws (Exception)
    def Publish(self, hostname=None, content=None, channel=defines.CHANNEL_NAME):
        if hostname is None:
            return
        host = siteChecker.siteChecker(hostname, content)
        # print("{} [{}] Date {}, Response {}ms, hasContent {}".format(host.url, host.status, host.datetime, host.responseTime, host.contentAvailable))
        data = {
            'url': host.url,
            'status': host.status,
            'datetime': host.datetime,
            'responseTime': host.responseTime,
            'contentMatch': host.contentAvailable
        }
        self._producer.send(channel, value=data)


# MAIN # Ctrl+C to abort
if __name__ == "__main__":
    # @inputs [URL, Content]
    Arguments = sys.argv[1:]
    if len(Arguments) <= 0:
        print("{} <URL> [RegExp]\n".format(sys.argv[0]))
        sys.exit(1)
    URL     = Arguments[0] if len(Arguments)>0 else None
    Content = Arguments[1] if len(Arguments)>1 else None
    print("Ctrl+C to abort")
    Loop = True
    # never ending while loop [Ctrl+C to exit]
    Site = Producer()
    while Loop:
        try:
            Site.Publish(hostname=URL, content=Content)
            sleep(1)
            sys.stdout.write('.')           # Some silly output for debugging purposes
            sys.stdout.flush()
        except KeyboardInterrupt:
            print("\nAborted\n")
            Loop = False
        except Exception as E:
            print(str(E))
            Loop = False

# print("{} [{}] Date {}, Response {}ms, hasContent {}".format(
#     host.url, host.status, host.datetime, host.responseTime, host.contentAvailable))
# time.strftime("%B %d %Y", "1284101485")
