# Docker-compose configuration

Runs Blockscout locally in Docker containers with [docker-compose](https://github.com/docker/compose).

## Prerequisites

- Docker v20.10+
- Docker-compose 2.x.x+
- Running Ethereum JSON RPC client

## Local environment files

Before starting any Compose configuration or the Makefile, copy the templates
from the repository root. These commands preserve existing local files:

```bash
cd ./docker-compose
umask 077
test -e .env || cp example.env .env
for template in envs/*.example.env; do
  local_env="${template%.example.env}.env"
  test -e "$local_env" || cp "$template" "$local_env"
done
```

Set `DB_PASSWORD`, `STATS_DB_PASSWORD`, and `SECRET_KEY_BASE` in `.env`.
For a new installation, generate two independent passwords with
`openssl rand -hex 32` and an independent application secret with
`openssl rand -hex 64`, then save them in their corresponding fields. The example
files intentionally leave secrets blank. Existing installations must use their
current database passwords until those passwords are also changed in PostgreSQL;
editing `.env` alone does not change credentials stored in an existing database.

Compose uses these private values for the database services, backend, stats and
user-ops-indexer. Set an optional `DATABASE_URL` in `.env` for an external backend
database; stats and user-ops-indexer use it unless their service-specific URL
overrides in `.env` are set. Database URLs and `SECRET_KEY_BASE` set by Compose
take precedence over entries in `envs/common-*.env`.

Adjust the remaining service settings in `envs/common-*.env`. `.env` and these
local service files are ignored by Git; commit changes to the matching
`*.example.env` templates only, keeping secret fields empty. Use
`docker compose config --quiet` to validate configuration without printing
expanded secrets.

## Building Docker containers from source

**Note**: in all below examples, you can use `docker compose` instead of `docker-compose`, if compose v2 plugin is installed in Docker.

```bash
cd ./docker-compose
docker-compose up --build
```

**Note**: if you don't need to make backend customizations, you can run `docker-compose up` in order to launch from pre-build backend Docker image. This will be much faster.

This command uses `docker-compose.yml` by-default, which builds the backend of the explorer into the Docker image and runs 9 Docker containers:

- Postgres 14.x database, which will be available at port 7432 on the host machine.
- Redis database of the latest version.
- Blockscout backend with api at /api path.
- Nginx proxy to bind backend, frontend and microservices.
- Blockscout explorer at http://localhost.

and 5 containers for microservices (written in Rust):

- [Stats](https://github.com/blockscout/blockscout-rs/tree/main/stats) service with a separate Postgres 14 DB.
- [Sol2UML visualizer](https://github.com/blockscout/blockscout-rs/tree/main/visualizer) service.
- [Sig-provider](https://github.com/blockscout/blockscout-rs/tree/main/sig-provider) service.
- [User-ops-indexer](https://github.com/blockscout/blockscout-rs/tree/main/user-ops-indexer) service.

**Note for Linux users**: Linux users need to run the local node on http://0.0.0.0/ rather than http://127.0.0.1/

## Configs for different Ethereum clients

The repo contains built-in configs for different JSON RPC clients without need to build the image.

| __JSON RPC Client__    | __Docker compose launch command__ |
| -------- | ------- |
| Erigon  | `docker-compose -f erigon.yml up -d`    |
| Geth (suitable for Reth as well) | `docker-compose -f geth.yml up -d`     |
| Geth Clique    | `docker-compose -f geth-clique-consensus.yml up -d`    |
| Nethermind, OpenEthereum    | `docker-compose -f nethermind.yml up -d`    |
| Anvil    | `docker-compose -f anvil.yml up -d`    |
| HardHat network    | `docker-compose -f hardhat-network.yml up -d`    |

- Running only explorer without DB: set `DATABASE_URL` in `.env`, then run `docker-compose -f external-db.yml up -d`. No backend DB container is created; stats retains its own database service.
- Running explorer with external backend: `docker-compose -f external-backend.yml up -d`
- Running explorer with external frontend: `FRONT_PROXY_PASS=http://host.docker.internal:3000/ docker-compose -f external-frontend.yml up -d`
- Running all microservices: `docker-compose -f microservices.yml up -d`
- Running only explorer without microservices: `docker-compose -f no-services.yml up -d`

All of the configs assume the Ethereum JSON RPC is running at http://localhost:8545.

In order to stop launched containers, run `docker-compose -f config_file.yml down`, replacing `config_file.yml` with the file name of the config which was previously launched.

You can adjust BlockScout environment variables:

- for backend in `./envs/common-blockscout.env`
- for frontend in `./envs/common-frontend.env`
- for stats service in `./envs/common-stats.env`
- for visualizer in `./envs/common-visualizer.env`
- for user-ops-indexer in `./envs/common-user-ops-indexer.env`

Descriptions of the ENVs are available

- for [backend](https://docs.blockscout.com/setup/env-variables)
- for [frontend](https://github.com/blockscout/frontend/blob/main/docs/ENVS.md).

## Running Docker containers via Makefile

Prerequisites are the same, as for docker-compose setup. Complete the local
environment file setup above first. The Makefile loads `docker-compose/.env`
explicitly for each Compose command.

Start all containers:

```bash
cd ./docker
make start
```

Stop all containers:

```bash
cd ./docker
make stop
```

***Note***: Makefile uses the same .env files since it is running docker-compose services inside.
