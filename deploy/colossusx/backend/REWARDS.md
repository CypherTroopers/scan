# ColossusX FHS-D rewards

Implemented on 2026-09-21 for GPL-3.0-only Blockscout v10.2.6.

## Supported protocol

This opt-in adapter targets chain ID **10101919**, genesis
`0xe69022ef43f6d238846015e0a4e7cdd190cf45e9fd98cfa0666acb482a05017e`,
and Cypher FHS-D source commit
[`64c126233459996e02cb1914a6bd73f252477c5c`](https://github.com/CypherTroopers/cypher/tree/64c126233459996e02cb1914a6bd73f252477c5c).
The branch snapshot used for review is `70862a71dfaf2b00694dc1354c6a64e9504d7db5`;
the observed node reports `Geth/v1.9.20-stable-64c12623(cypherium-v2.0.0)`.
A matching genesis is a network identity check, not automatic support for future
protocol changes. Review and version this adapter when the reward rules change.

## Payouts

All arithmetic uses integer wei (18 decimals per CLX).

- **Block production:** 100,000 CLX to the actual header coinbase for a nonempty
  FastTx/SlowTx block or a Key carrier block. Genesis and empty FastTx/SlowTx blocks
  pay zero. `eth_getHeaderByHash` supplies the real coinbase; the network's
  `eth_getBlockByNumber` miner field has different semantics.
- **Common miner (PoW):** an additional 100,000 CLX on a Key carrier when the new
  Key block has a nonempty `outAddress`. A leading `*` is removed. The carrier's
  `keyHash` names its parent signing Key block; the next Key block must have that
  parent, a sequential key number, and `TxBlockNumber = carrier height - 1`.
  No leader fallback or repeated payout on subsequent ordinary blocks is added.
- **Common RPC:** receipts identify the actual `commonTxRewardRecipient` (B),
  distinct from admission signer `commonTxApprover` (A). Its reward is
  `floor(gasUsed * effectiveGasPrice / 5)`, with the remainder burned. Failed
  transactions also pay execution fees. Receipts are aggregated by recipient.
  The protocol credits B directly; an internal-transfer trace is not required.

The adapter checks the receipt's exact reward, burn, network identity, block and
transaction identity. Ethereum gas payments are **not** added to these payouts.
No unverified committee-sharing or uncle reward formula is used.

Primary implementation references:
[consensus rewards](https://github.com/CypherTroopers/cypher/blob/64c126233459996e02cb1914a6bd73f252477c5c/consensus/colossusX/consensus.go),
[transaction fees](https://github.com/CypherTroopers/cypher/blob/64c126233459996e02cb1914a6bd73f252477c5c/core/state_transition.go),
[RPC fields](https://github.com/CypherTroopers/cypher/blob/64c126233459996e02cb1914a6bd73f252477c5c/internal/ethapi/api.go).

## Configuration and backfill

Set these backend environment variables:

```dotenv
FETCH_REWARDS_WAY=colossusx
COLOSSUSX_REWARDS_GENESIS_HASH=0xe69022ef43f6d238846015e0a4e7cdd190cf45e9fd98cfa0666acb482a05017e
INDEXER_DISABLE_BLOCK_REWARD_FETCHER=false
```

The existing geth variant remains usable for other indexing operations. Reward
backfill defaults to one block per batch and one concurrent worker in this mode.
Existing indexed blocks without a validator reward row are picked up by the
normal reward fetcher. No database reset is required. The fetcher requires the
node's historical block/header/receipt/Key-block RPC data to remain available.

A verified `validator` row, including an explicit zero, marks a complete block.
Its `colossusx_pow` and `colossusx_rpc` rows are imported in the same transaction.
Missing or inconsistent RPC results remain pending and are retried. Canonical
receipts and a final header-by-number check guard against mixed data during a
reorganization; the existing block importer removes rewards for orphaned blocks.
Imports are idempotent. Unsupported block types/uncles fail verification.

## API and interface

In this mode V2 block responses include `colossusx_rewards`:

- `status`: `complete` or `pending`.
- `rule_version`: `FHS-D/64c12623`.
- `total`, `block_reward`, `common_miner_reward`, `common_rpc_reward`: decimal
  integer-wei strings for complete data, or null while pending.
- `payouts`: positive amounts with `address_hash`, `category` (`block`,
  `common_miner`, `common_rpc`), and integer-wei `reward`.

The UI shows the combined total, category totals and actual recipient links;
it refreshes pending results. Verified zero and not-yet-indexed data are distinct.
The legacy `getblockreward` response keeps `blockReward` as block production only,
uses the real producer as `blockMiner`, and includes `colossusxRewards` for the
full distribution. It returns an indexing error while the reward is pending.
Other networks retain their upstream response shape and reward behavior.

The general indexed block miner field and address validated-blocks selection
retain the upstream RPC miner semantics. Use the explicit reward payout addresses
for the recipients of these FHS-D payments.
