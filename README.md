# DishwasherBackend
Backend RESTful API application for the smart dishwasher project. API implemented in [Flask](https://github.com/pallets/flask) micro framework  with [SocketIO](https://github.com/socketio) functionalities.

:diamonds: In conjunction with projects [DishwasherOS](https://github.com/AmbroAnalog/DishwasherOS) and [DishwasherFrontend](https://github.com/AmbroAnalog/DishwasherFrontend)

## Mode of operation
```
                               ┌────────────────────────┐
smart dishwasher project       │ Docker Container       │
                               │  ┌───────┐             │
                               │  │MongoDB│             │
                               │  └──▲────┘             │
                               │     │                  │
┌──────────────┐  REST-API     │  ┌──▼──────────────┐   │
│ DishwasherOS ├───────────────┼─►│DishwasherBackend│   │
└────┬───▲─────┘               │  └────┬─▲──────────┘   │
     │   │                     │       │ │ REST-API     │
     │   │                     │       │ │ Socket.IO    │
┌────▼───┴─────┐               │  ┌────▼─┴────────────┐ │
│  Dishwasher  │               │  │DishwasherFrontend │ │
└──────────────┘               │  └───────────────────┘ │
                               │                        │
                               └────────────────────────┘
```
The backend application establishes a RESTful API for the interface between OS and frontend, as well as to the database. A MongoDB is used as persistent data storage.

## Installation
The application is deployed in a Docker enviroment. Installation of `docker` as well as `docker-compose` is required.
1. `git clone https://github.com/AmbroAnalog/DishwasherBackend.git`
2. add configuration file `app/configuration.yaml` for database credentials:
```yaml
database:
  server: 192.168.0.10
  port: 27017
  user: myuser
  password: mypassword
  database: SmartDeviceHub
  collection: device_g470
```
3. `docker-compose up -d --build`
4. The API is now available at port 5000.
