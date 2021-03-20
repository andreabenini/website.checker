# Dummy defines file

# Kafka information
KAFKA_HOST='localhost:9092'
KAFKA_PROTOCOL=''
# These are mandatory when KAFKA_PROTOCOL='SSL', unneeded when KAFKA_PROTOCOL=''
KAFKA_CA='ca.pem'
KAFKA_CERT='service.cert'
KAFKA_KEY='service.key'
CHANNEL_NAME='siteChecker'
CHANNEL_CLIENT='consumerClientID'
CHANNEL_GROUP='consumerGroupID'

# Database information
DB_HOST='localhost'
DB_PORT='5432'
DB_NAME='pythonDatabase'
DB_TABLE=CHANNEL_NAME
DB_USERNAME='pythonUser'
DB_PASSWORD='pythonPassword'

DB_TABLE_SQL='INSERT INTO '+DB_TABLE+' (url, status, datetime, responseTime, contentMatch)' \
                              ' VALUES (%s, %s,  to_timestamp(%s),  %s,      %s)'
DB_TABLE_CREATE="""CREATE TABLE IF NOT EXISTS sitechecker(
    url             VARCHAR(100)    NOT NULL DEFAULT '',
    status          INT             DEFAULT 0,
    datetime        TIMESTAMP       DEFAULT now(),
    responseTime    NUMERIC(6,3)    DEFAULT 0,
    contentMatch    BOOLEAN
);
"""
