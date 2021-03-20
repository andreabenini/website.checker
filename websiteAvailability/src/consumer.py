#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Loop in a kafka queue to get hosts data/uptime and push them in a PostgreSQL table
#
# @see Adapt defines.py to match current Kafka and PostgreSQL installation, there's no 
#      need to edit it for running this project with local containers. You may even keep
#      defines.py as it is and just change main Object constructor and methods
#
import sys
import json
import psycopg2
from time  import sleep
from kafka import KafkaConsumer

import defines
import siteChecker

# Kafka consumer
class Consumer:
    # Constructor, everything is optional so this object might be fully initialized with this constructor
    #              but it can be directly connected later on with methods described below
    # @throws (Exception)
    def __init__(self, kafkaHost=defines.KAFKA_HOST, kafkaName=defines.CHANNEL_NAME, kafkaGroup=defines.CHANNEL_GROUP,
                       database=defines.DB_NAME, user=defines.DB_USERNAME, password=defines.DB_PASSWORD, host=defines.DB_HOST, port=defines.DB_PORT):
        self._db = None
        self._dbCursor = None
        self._consumer = None
        self.QueueConnect(host=kafkaHost, channelName=kafkaName, channelGroup=kafkaGroup)           # 2nd stage constructor/method
        self.DatabaseConnect(database=database, user=user, password=password, host=host, port=port) # 2nd stage constructor/method

    # QueueConnect - Connect to the kafka queue
    # @param host         (string) Kafka location, example: 'localhost:9092'
    # @param channelName  (string) Kafka channel name where information were published ['siteChecker']
    # @param channelGroup (string) GroupID for this program, use it to get queue information just once
    # @throws (Exception)
    def QueueConnect(self, host=None, channelName=None, channelGroup=None):
        try:
            if defines.KAFKA_PROTOCOL=='':      # Plain/local/unencrypted kafka connection
                self._consumer = KafkaConsumer(
                    channelName,
                    bootstrap_servers  = [host],
                    auto_offset_reset  = 'earliest',        # earliest,latest
                    enable_auto_commit = True,              # offset periodically committed in background
                    group_id=channelGroup,                  # Avoid duplicate/resending
                    value_deserializer  = lambda x: json.loads(x.decode('utf-8'))
                )
            else:                               # Cloud provider auth with SSL and CERTs
                self._consumer = KafkaConsumer(
                    channelName,
                    bootstrap_servers  = [host],
                    security_protocol  = defines.KAFKA_PROTOCOL,
                    ssl_check_hostname=True,
                    ssl_cafile=defines.KAFKA_CA,
                    ssl_certfile=defines.KAFKA_CERT,
                    ssl_keyfile=defines.KAFKA_KEY,
                    auto_offset_reset  = 'earliest',        # earliest,latest
                    enable_auto_commit = True,              # offset periodically committed in background
                    group_id=channelGroup,                  # Avoid duplicate/resending
                    client_id=defines.CHANNEL_CLIENT,
                    value_deserializer  = lambda x: json.loads(x.decode('utf-8'))
                )
        except:
            self._consumer = None

    # DatabaseConnect - Connect to PostgreSQL database, psycopg lib
    # @param database (string) Name of the database
    # @param user     (string) username for database connection, must have r/w privileges on table
    # @param password (string) password for that user
    # @param host     (string) PostgreSQL hostname (see defines.py)
    # @param port     (string) PostgreSQL port     (see defines.py)
    # @throws (Exception)
    def DatabaseConnect(self, database=None, user=None, password=None, host=None, port=None):
        try:
            self._db = psycopg2.connect(database=database, user=user, password=password, host=host, port=port)
            self._dbCursor = self._db.cursor()      # remote cursor used for db operations
        except:
            self._db = None

    # DatabaseTableCreate - Create/init the required PostgreSQL database table
    # @see this is usually not needed but on remote/cloud databases it might be a nice idea to have some sort of script
    #      to automate process creation
    def DatabaseTableCreate(self, statement=defines.DB_TABLE_CREATE):
        if self._db is None or self._dbCursor is None:
            print("Database connection error, aborting process")
            return False
        self._dbCursor.execute(statement)
        self._db.commit()
        print("Database table created")

    # LoopSubscriptions - Loops available subscriptions and publish them on PostgreSQL
    # @param  statement (string) constant [fixed] define statement for writing data to PostgreSQL
    # @return (boolean) True: subscriptions processed, False: Database error
    # @throws (Exception)
    def LoopSubscriptions(self, statement=defines.DB_TABLE_SQL):
        if self._db is None or self._dbCursor is None:
            print("Database connection error, aborting process")
            return False
        if self._consumer is None:
            print("Kafka queue not connected, aborting process")
            return False
        for event in self._consumer:
            data = event.value
            # print("{}: {}".format(data['url'], data)) # 'url', 'status', 'datetime', 'responseTime', 'contentMatch' #
            if data['url'] is not None:
                self._dbCursor.execute(statement, (data['url'], data['status'], data['datetime'], data['responseTime'], data['contentMatch']))
                self._db.commit()
                sys.stdout.write('.')       # Some silly output for debugging purposes
                sys.stdout.flush()
        return True


# MAIN # No input parameters needed
if __name__ == "__main__":
    # Some input parameters, process them
    if len(sys.argv) > 1:
        if sys.argv[1] == 'create':
            # Create a consumer object just for creating required table, abort Queue connection
            Queue = Consumer(kafkaHost=None, kafkaName=None, kafkaGroup=None)
            Queue.DatabaseTableCreate()
            sys.exit(0)
        else:
            print("Invalid parameter, required: create")
            sys.exit(1)
    # Normal operation mode
    Loop = True
    print("Ctrl+C to abort")
    # While loop [Ctrl+C to exit]
    Queue = Consumer()
    while Loop:
        try:
            Loop = Queue.LoopSubscriptions()
            sleep(1)
        except KeyboardInterrupt:
            print("\nAborted\n")
            Loop = False
        except Exception as E:
            print("\nERROR: {}\n".format(str(E)))
            Loop = False
