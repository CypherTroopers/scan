~~~
https://colossusx.make-cph-great-again.community
~~~

<h1 align="center">Blockscout</h1>
<p align="center">Blockchain Explorer for inspecting and analyzing EVM Chains.</p>
<div align="center">

[![Discord](https://img.shields.io/badge/chat-Blockscout-green.svg)](https://discord.gg/blockscout)

</div>


Blockscout provides a comprehensive, easy-to-use interface for users to view, confirm, and inspect transactions on EVM (Ethereum Virtual Machine) blockchains. This includes Ethereum Mainnet, Ethereum Classic, Optimism, Gnosis Chain and many other **Ethereum testnets, private networks, L2s and sidechains**.

See our [project documentation](https://docs.blockscout.com/) for detailed information and setup instructions.

For questions, comments and feature requests see the [discussions section](https://github.com/blockscout/blockscout/discussions) or via [Discord](https://discord.com/invite/blockscout).

## About Blockscout

Blockscout allows users to search transactions, view accounts and balances, verify and interact with smart contracts and view and interact with applications on the Ethereum network including many forks, sidechains, L2s and testnets.

Blockscout is an open-source alternative to centralized, closed source block explorers such as Etherscan, Etherchain and others.  As Ethereum sidechains and L2s continue to proliferate in both private and public settings, transparent, open-source tools are needed to analyze and validate all transactions.

## Supported Projects

Blockscout currently supports several hundred chains and rollups throughout the greater blockchain ecosystem. Ethereum, Cosmos, Polkadot, Avalanche, Near and many others include Blockscout integrations. A comprehensive list is available at [chains.blockscout.com](https://chains.blockscout.com). If your project is not listed, contact the team in [Discord](https://discord.com/invite/blockscout).

## ColossusX deployment

This checkout contains backend **11.3.1** under the license in [LICENSE](LICENSE).
The ColossusX deployment below builds the separately prepared **GPLv3 backend
10.2.6 and frontend 2.7.2**, including FHS-D rewards. See
[PUBLICATION.md](PUBLICATION.md) for the distinction between this checkout and
the independent GPL source release.

Requires Linux, Docker Engine with Compose v2 and Buildx, Git, Bash, curl, patch,
GNU tar/coreutils, gzip, and Python 3.12+. Elixir and Node.js are installed inside
the build images. The checked-in service limits target a 4-CPU, 8-GiB host;
allow additional memory/swap or use a separate host for builds.

1. Clone this repository and fetch the exact GPL backend build input. The fetch
   leaves your checked-out branch unchanged:

   ```bash
   git clone https://github.com/CypherTroopers/scan.git
   cd scan
   git fetch --depth=1 https://github.com/blockscout/blockscout.git \
     90f7dd8e9348123b74dfd23f69ab7da76191a820
   ```

2. Generate local secrets from the repository root. This refuses to overwrite an
   existing `.env`:

   ```bash
   python3 - <<'PY'
   import os
   import secrets

   fd = os.open('deploy/colossusx/.env', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
   with os.fdopen(fd, 'w') as env:
       env.write('PUBLIC_IP=YOUR_SERVER_IP\n')
       for name, size in [('DB_PASSWORD', 32), ('STATS_DB_PASSWORD', 32), ('SECRET_KEY_BASE', 64)]:
           env.write(f'{name}={secrets.token_hex(size)}\n')
   PY
   ```

   Set `PUBLIC_IP` in that file. Review `backend.env` and `frontend.env` under
   `deploy/colossusx` for the RPC, chain ID, currency and FHS-D genesis settings.
   For your own domain, update `compose.override.yml`, `nginx.conf` and
   `host-nginx/*.conf` under `deploy/colossusx`, then configure DNS and host
   Nginx with a valid TLS certificate. Compose automatically loads the HTTPS
   override, so changing `PUBLIC_IP` alone does not change the public domain.
   Follow the [host Nginx/HTTPS guide](deploy/colossusx/README.md#host-nginx-and-https).

3. Build the backend first, then the frontend, from the repository root:

   ```bash
   ./deploy/colossusx/backend/build.sh && ./deploy/colossusx/frontend/build.sh
   ```

   These scripts fetch/verify the pinned sources, apply the ColossusX patches,
   build both local images, and create matching source downloads in
   `deploy/colossusx/source-dist/`. Keep `/source/`, `/legal/` and the footer
   attribution available. The first build needs network access and can take time.

4. Start the stack and check synchronization:

   ```bash
   cd deploy/colossusx
   docker compose config --quiet
   docker compose up -d
   docker compose ps
   docker compose logs --tail=100 backend stats
   curl -fsS https://YOUR_DOMAIN/api/v2/main-page/indexing-status
   ```

   Open `https://YOUR_DOMAIN`. Host Nginx forwards to the container proxy on
   port `18080`; PostgreSQL, Redis and application ports stay internal. Indexing
   starts automatically. Use `docker compose stop` / `start` for normal
   maintenance; `docker compose down -v` deletes the stored explorer data.
   See the [operations guide](deploy/colossusx/README.md) for backups and updates.

## Getting Started

See the [project documentation](https://docs.blockscout.com/) for instructions:

- [Manual deployment](https://docs.blockscout.com/for-developers/deployment/manual-deployment-guide)
- [Docker-compose deployment](https://docs.blockscout.com/for-developers/deployment/docker-compose-deployment)
- [Kubernetes deployment](https://docs.blockscout.com/for-developers/deployment/kubernetes-deployment)
- [Manual deployment (backend + old UI)](https://docs.blockscout.com/for-developers/deployment/manual-old-ui)
- [Ansible deployment](https://docs.blockscout.com/for-developers/ansible-deployment)
- [ENV variables](https://docs.blockscout.com/setup/env-variables)
- [Configuration options](https://docs.blockscout.com/for-developers/configuration-options)

## Acknowledgements

We would like to thank the EthPrize foundation for their funding support.

## Contributing

See [CONTRIBUTING.md](.github/CONTRIBUTING.md) for contribution and pull request protocol. We expect contributors to follow our [code of conduct](.github/CODE_OF_CONDUCT.md) when submitting code or comments.

## License

[![License: Blockscout Software Licence](https://img.shields.io/badge/License-Blockscout%20Software%20Licence-blue.svg)](LICENSE)

This project is licensed under the Blockscout Software Licence. See the [LICENSE](LICENSE) file for full terms.

Third-party components included in this repository remain subject to their own licenses. See dependency manifests and bundled third-party notices for component-level license terms.
