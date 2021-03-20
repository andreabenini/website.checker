# website.checker
Python website checker with consumer/producer sync


**development notes**  
This project has been built on a common linux desktop but requirements are minimal so highly
portable to other OSes too (Linux, MacOS but even Windows)
- OS: whatever. Now using Arch linux (rolling stable) AMD64.  Linux 5.11.7-arch1-1
- Editor: whatever. Now using Visual Studio Code (1.54.3). Optional but nice to have it
- Python3 required [3.9.2 tested but every Python3 is fine]
- python pip, virtualenv
- git, binutils

# Virtual networking and workspace
- python source code might be run on a common machine as well as a container or virtualenv.
VirtualEnv is now used in order to avoid unneeded packages and keep the solution separated
from other environments.
- Kafka and PostgreSQL are required services for this project, they might be run on separate
virtual machines, inside a Kubernetes Pod or Docker container. For development purposes I've
used docker container in the same machine where this code has been written.
```sh
# differences between distros exist, 
#    install those packages with your favorite package manager

# Arch Linux basic installation
pacman -S docker docker-compose
# Gentoo
# emerge docker docker-compose
# RHEL based distros
# yum install docker docker-compose
# Debian based distros
# apt install docker docker-compose
```

# Python environment and requirements
I'm using python without too many deps, it could be easily packageable or embeddable in a
virtual machine/container/installation
```sh
# Create and activate virtual environment and work dir
python3 -m venv websiteAvailability
cd websiteAvailability
mkdir src
source ./bin/activate
# Install required tools
pip install --upgrade pip     # ...just to be sure to get an up to date env
pip install requests          # HTTP GET/POST request lib
pip install bs4               # Beautiful Soup (regexps html parser)
pip install kafka-python      # kafka libraries
pip install psycopg2          # PostgreSQL libs
```

# Environment Setup
**NOTE:** This is just a simple installation for local development purposes, docker is 
quick to install and good enough for basic tests. That's why I've used it. 
This project will work with or without these docker images but these services are needed
for evaluation, feel free to supply them with: a Cloud Provider, a Virtual Machine or a
locally installed daemon. Required services:
- Kafka
- PostgreSQL
- Python environment (virtualenv) [barebone, virtual machine, container]

## Kafka Setup
Kafka installed in a container, skip it if you already have it,
feel free to use this script to automate the whole process:
```sh
git clone https://github.com/wurstmeister/kafka-docker docker-kafka
cd docker-kafka
cat << EOF > docker-compose-expose.yml
version: '2'
services:
  zookeeper:
    image: wurstmeister/zookeeper:3.4.6
    ports:
     - "2181:2181"
  kafka:
    build: .
    ports:
     - "9092:9092"
    expose:
     - "9093"
    environment:
      KAFKA_ADVERTISED_LISTENERS: INSIDE://kafka:9093,OUTSIDE://localhost:9092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: INSIDE:PLAINTEXT,OUTSIDE:PLAINTEXT
      KAFKA_LISTENERS: INSIDE://0.0.0.0:9093,OUTSIDE://0.0.0.0:9092
      KAFKA_INTER_BROKER_LISTENER_NAME: INSIDE
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_CREATE_TOPICS: "topic_test:1:1"
    volumes:
     - /var/run/docker.sock:/var/run/docker.sock
EOF
cd -
cat << EOF > start.kafka.sh
#!/usr/bin/env bash
#
DIR=docker-kafka
cd \$DIR
docker-compose -f docker-compose-expose.yml up
cd -
EOF
chmod +x start.kafka.sh
echo -e "\n\nKafka Installation Completed"
echo "Use ./start.kafka.sh to start Kafka service in a terminal"
echo "[docker-compose stop] to terminate the service"
```

## PostgreSQL setup
Dummy PostgreSQL docker container with just the database for this project,
skip it if you already have it.  
```sh
mkdir docker-postgresql; cd docker-postgresql
cat << EOF > docker-compose.yml
version: '3'
services:
  database:
    image: "postgres"   # use latest official postgres version
    ports:
      - "5432:5432"
    env_file:
      - database.env    # configure postgres
    volumes:
      - database-data:/var/lib/postgresql/data/                 # persist data even if container shuts down
      - ./postgresInit.sql:/docker-entrypoint-initdb.d/init.sql # SQL init script
volumes:
  database-data: # named volumes can be managed easier using docker-compose
EOF
cat << EOF > database.env
POSTGRES_USER=pythonUser
POSTGRES_PASSWORD=pythonPassword
POSTGRES_DB=pythonDatabase
EOF
cat << EOF > postgresInit.sql
CREATE TABLE IF NOT EXISTS sitechecker(
    url             VARCHAR(100)    NOT NULL DEFAULT '',
    status          INT             DEFAULT 0,
    datetime        TIMESTAMP       DEFAULT now(),
    responseTime    NUMERIC(6,3)    DEFAULT 0,
    contentMatch    BOOLEAN
);
EOF
cd -
cat << EOF > start.postgresql.sh
#!/usr/bin/env bash
#
DIR=docker-postgresql
cd \$DIR
docker-compose up
cd -
#
# PostgreSQL console
#   docker-compose run database bash
#   psql  --user=pythonUser --dbname=pythonDatabase --host=database
EOF
chmod +x start.postgresql.sh
echo -e "\n\nKafka Installation Completed"
echo "Use ./start.postgresql.sh to start Kafka service in a terminal"
echo "[docker-compose stop] to terminate the service"
```
## PostgreSQL setup (Cloud Mode)
When using external cloud providers you cannot always create a container from scratch and
you need to rely on provider web tools. In that case you cannot (always) create a database
structure for this project. In this case you can always:
- Restore a previously created db with the table `sitechecker` listed above
- Create `sitechecker` table manually with provider's tools, see `postgresInit.sql` for details
- Create `sitechecker` table with provider's web tools and follow `postgresInit.sql` specs
- Install these python programs and use `consumer.py` to create that table for you. Database
configuration required as usual but just exec:
```sh
./consumer.py create
```


# Running this code
directory `websiteAvailability/src`, two different utilities:
- `producer.py`. Requires _defines.py_ and _siteChecker.py_ (module).
Adapt _defines.py_ to your needs if Kafka is not running locally in a container.
Feel free to use `siteChecker.py` as a standalone utility to understand what it does.
- `consumer.py`. Requires _defines.py_, you can use the same but feel free to copy or
adapt it to your needs if you separate **consumer** and **producer** on different
machines. Also please note you need to take care of PostgreSQL daemon location, 
there's no need to change things if you're running locally in a container.


# Resources/Links
Images and quick hints already exists on Internet, I've not created machines from
scratch so I've used these resources:  

**Kafka**  
I've never used Kafka before so I've used these information to deal with it:
- Docker image:  https://github.com/wurstmeister/kafka-docker  
    Installation and configuration notes are taken from supplied README.md
- Basic reference and startup instruction for the docker image  
    https://towardsdatascience.com/kafka-docker-python-408baf0e1088
- Kafka-Python basic library as a reference for package docs  
    https://kafka-python.readthedocs.io/en/master/usage.html
- Locally was easy, but at the end I had problems with the cloud provider. This helped a lot:  
    https://help.aiven.io/en/articles/489572-getting-started-with-aiven-for-apache-kafka

**PostgreSQL**
- Docker compose reference for database and table creation, official PostgreSQL
 image used here:
    https://medium.com/analytics-vidhya/getting-started-with-postgresql-using-docker-compose-34d6b808c47c

