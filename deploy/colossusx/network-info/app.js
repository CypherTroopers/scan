import {
  CHAIN_ID,
  FIELDS,
  SAMPLE_TRANSACTION,
  analyzeAdmission,
  formatClx,
  quantity,
  validAddress,
  validHash,
} from "./admission.js";

const RPC_URL = "https://test2.make-cph-great-again.community";
const form = document.querySelector("#lookup-form");
const input = document.querySelector("#tx-hash");
const status = document.querySelector("#lookup-status");
const results = document.querySelector("#lookup-results");
let activeRequest;

function node(tag, text, className) {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  if (className) element.className = className;
  return element;
}

function addressLink(address) {
  if (!validAddress(address)) return node("code", String(address));
  const link = node("a", address);
  link.href = `/address/${address}`;
  return link;
}

async function rpcBatch(calls, signal) {
  const response = await fetch(RPC_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(
      calls.map(([method, params], index) => ({
        jsonrpc: "2.0",
        id: index + 1,
        method,
        params,
      })),
    ),
    signal,
    credentials: "omit",
  });
  if (!response.ok) throw new Error(`RPC returned HTTP ${response.status}.`);
  const body = await response.json();
  if (!Array.isArray(body))
    throw new Error("RPC returned an unexpected response.");
  return calls.map((_, index) => {
    const entry = body.find((item) => item.id === index + 1);
    if (!entry || entry.error || !Object.hasOwn(entry, "result")) {
      throw new Error(entry?.error?.message || "RPC response is incomplete.");
    }
    return entry.result;
  });
}

function amountCard(label, amount) {
  const card = node("div", undefined, "result-card");
  card.append(node("h3", label, "result-label"));
  card.append(
    node(
      "p",
      amount === null ? "Not returned by the RPC" : formatClx(amount),
      "result-value",
    ),
  );
  if (amount !== null) card.append(node("code", `${amount} wei`));
  return card;
}

function fieldValue(value, type) {
  if (value === null) return node("span", "Not returned by the RPC");
  if (type === "address") return addressLink(value);
  const parsed = quantity(value);
  const wrapper = node("div");
  if (type === "amount" && parsed !== null)
    wrapper.append(node("p", `${formatClx(parsed)} · ${parsed} wei`));
  if (type === "quantity" && parsed !== null)
    wrapper.append(node("p", parsed.toString()));
  if (type === "timestamp" && parsed !== null && parsed <= 8640000000000n) {
    wrapper.append(node("p", new Date(Number(parsed) * 1000).toISOString()));
  }
  wrapper.append(node("code", String(value)));
  return wrapper;
}

async function lookup(hash) {
  activeRequest?.abort();
  const controller = new AbortController();
  activeRequest = controller;
  const timeout = setTimeout(() => controller.abort(), 20000);
  results.replaceChildren();
  results.hidden = true;
  if (!validHash(hash)) {
    clearTimeout(timeout);
    status.textContent =
      "Enter a transaction hash: 0x followed by 64 hexadecimal characters.";
    return;
  }
  status.textContent = "Reading the ColossusX transaction and receipt…";
  const url = new URL(location.href);
  url.searchParams.set("tx", hash);
  history.replaceState(null, "", url);
  try {
    const [chainId, transaction, receipt] = await rpcBatch(
      [
        ["eth_chainId", []],
        ["eth_getTransactionByHash", [hash]],
        ["eth_getTransactionReceipt", [hash]],
      ],
      controller.signal,
    );
    if (quantity(chainId) !== CHAIN_ID)
      throw new Error("RPC chain ID does not match ColossusX (10101919).");
    if (!transaction && !receipt) {
      status.textContent =
        "Transaction not found on ColossusX. Check the hash or try again later.";
      return;
    }
    if (
      (transaction && transaction.hash?.toLowerCase() !== hash.toLowerCase()) ||
      (receipt && receipt.transactionHash?.toLowerCase() !== hash.toLowerCase())
    ) {
      throw new Error("RPC returned a different transaction hash.");
    }
    const model = analyzeAdmission(transaction, receipt);
    const fragment = document.createDocumentFragment();
    const link = node("a", "Open transaction in explorer →");
    link.href = `/tx/${hash}`;
    fragment.append(link);
    if (!model.hasAdmission) {
      fragment.append(
        node(
          "p",
          "Common RPC admission data is not available for this transaction. Missing fields are not treated as zero rewards.",
          "notice",
        ),
      );
    } else {
      const roles = node("div", undefined, "result-grid");
      for (const [label, value] of [
        ["Admission signer A", model.fields.commonTxApprover],
        ["Reward recipient B", model.fields.commonTxRewardRecipient],
      ]) {
        const card = node("div", undefined, "result-card");
        card.append(node("h3", label, "result-label"));
        card.append(
          value === null
            ? node("p", "Not returned by the RPC")
            : addressLink(value),
        );
        roles.append(card);
      }
      fragment.append(roles);
      const amounts = node("div", undefined, "result-grid");
      amounts.append(
        amountCard("Actual transaction fee", model.actualFee),
        amountCard("Reported reward to B", model.reward),
        amountCard("Reported burn", model.burn),
      );
      fragment.append(amounts);
      if (model.amountsMatch === true) {
        fragment.append(
          node(
            "p",
            "Reported amounts match floor(actualTxFee / 5) and its remainder. This arithmetic check does not verify the signature, roots, or consensus.",
            "notice success",
          ),
        );
      }
      fragment.append(
        node(
          "p",
          "Under the network rule, commonTxApproverReward denotes a direct credit to B, not a transfer from A. The RPC retains the existing field name.",
          "notice",
        ),
      );
    }
    for (const message of model.warnings)
      fragment.append(node("p", message, "notice warning"));
    const table = node("table");
    const caption = node(
      "caption",
      "RPC fields · receipt values take precedence when available",
    );
    const tbody = node("tbody");
    for (const [key, meaning, type] of FIELDS) {
      const row = node("tr");
      const heading = node("th");
      heading.scope = "row";
      heading.append(node("code", key), node("p", meaning));
      const cell = node("td");
      cell.append(fieldValue(model.fields[key], type));
      row.append(heading, cell);
      tbody.append(row);
    }
    table.append(caption, tbody);
    fragment.append(table);
    const balance = node("p", undefined, "notice");
    fragment.append(balance);
    if (controller.signal.aborted) return;
    results.append(fragment);
    results.hidden = false;
    status.textContent = receipt
      ? "Mined transaction loaded from the public RPC."
      : "Pending transaction loaded from the public RPC.";
    const recipient = model.fields.commonTxRewardRecipient;
    if (validAddress(recipient)) {
      balance.textContent = "Reading B's current balance…";
      try {
        const [rawBalance] = await rpcBatch(
          [["eth_getBalance", [recipient, "latest"]]],
          controller.signal,
        );
        const wei = quantity(rawBalance);
        if (wei === null) throw new Error("Missing balance");
        balance.textContent = `B's current balance: ${formatClx(wei)} (${wei} wei). This includes its initial balance, ordinary transfers and any other credits; it is not a Common RPC rewards total.`;
      } catch {
        balance.textContent =
          "B's current balance could not be read. The transaction fields above remain available.";
      }
    } else {
      balance.remove();
    }
  } catch (error) {
    if (activeRequest !== controller) return;
    status.textContent = controller.signal.aborted
      ? "The RPC request timed out. Please try again."
      : `Unable to load transaction: ${error.message}`;
  } finally {
    clearTimeout(timeout);
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  lookup(input.value.trim());
});
document.querySelector("#sample-transaction").addEventListener("click", () => {
  input.value = SAMPLE_TRANSACTION;
  lookup(SAMPLE_TRANSACTION);
});
const initialHash = new URL(location.href).searchParams.get("tx");
if (initialHash) {
  input.value = initialHash;
  lookup(initialHash);
}
