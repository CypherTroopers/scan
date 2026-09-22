export const CHAIN_ID = 10101919n;
export const SAMPLE_TRANSACTION =
  "0xc376f07d78ce2eb9d3e79c4264d8d76d5814196fcaa2b887b2b0fd8d4b51c9ca";

export const FIELDS = [
  ["commonTxApprover", "Admission signer A", "address"],
  ["commonTxRewardRecipient", "Actual reward recipient B", "address"],
  ["commonTxApproverReward", "Common RPC fee reward credited to B", "amount"],
  ["commonTxBurn", "Burned remainder of the actual fee", "amount"],
  [
    "commonTxAdmissionRoot",
    "Block commitment to signed admissions and references",
    "hex",
  ],
  ["commonTxRewardRoot", "Block commitment to reward records", "hex"],
  ["commonTxAdmissionChainId", "Chain ID bound to the proof", "quantity"],
  [
    "commonTxAdmissionKeyBlockNumber",
    "Admission's key-block boundary",
    "quantity",
  ],
  ["commonTxAdmissionTimestamp", "Signed admission timestamp", "timestamp"],
  [
    "commonTxAdmissionSignature",
    "A's signature over the admission payload",
    "hex",
  ],
];

export function quantity(value) {
  return typeof value === "string" && /^0x[0-9a-f]+$/i.test(value)
    ? BigInt(value)
    : null;
}

export function validHash(value) {
  return typeof value === "string" && /^0x[0-9a-f]{64}$/i.test(value);
}

export function validAddress(value) {
  return typeof value === "string" && /^0x[0-9a-f]{40}$/i.test(value);
}

export function formatClx(wei) {
  const scale = 10n ** 18n;
  const fraction = (wei % scale)
    .toString()
    .padStart(18, "0")
    .replace(/0+$/, "");
  return `${wei / scale}${fraction ? `.${fraction}` : ""} CLX`;
}

export function analyzeAdmission(transaction, receipt) {
  const fields = Object.fromEntries(
    FIELDS.map(([key]) => [key, receipt?.[key] ?? transaction?.[key] ?? null]),
  );
  const warnings = [];
  const hasAdmission = FIELDS.some(([key]) => fields[key] !== null);
  const gasUsed = quantity(receipt?.gasUsed);
  const effectiveGasPrice = quantity(receipt?.effectiveGasPrice);
  const actualFee =
    gasUsed !== null && effectiveGasPrice !== null
      ? gasUsed * effectiveGasPrice
      : null;
  // Only a mined receipt reports a credited amount. Never infer it from a formula.
  const reward = quantity(receipt?.commonTxApproverReward);
  const burn = quantity(receipt?.commonTxBurn);
  const a = fields.commonTxApprover;
  const b = fields.commonTxRewardRecipient;
  let amountsMatch = null;

  if (!receipt)
    warnings.push("No mined receipt is available. Payouts are not confirmed.");
  if (hasAdmission) {
    if (!validAddress(a))
      warnings.push("The RPC did not return a valid admission signer A.");
    if (!validAddress(b)) {
      warnings.push(
        "Reward recipient B is missing or invalid. No payout to A is inferred.",
      );
    } else if (validAddress(a) && a.toLowerCase() === b.toLowerCase()) {
      warnings.push(
        "A and B are identical in the RPC response; the supplied rule requires distinct accounts.",
      );
    }
    if (quantity(fields.commonTxAdmissionChainId) !== CHAIN_ID) {
      warnings.push(
        "The admission chain ID is missing or differs from ColossusX (10101919).",
      );
    }
    for (const [key] of FIELDS) {
      const txValue = transaction?.[key];
      const receiptValue = receipt?.[key];
      if (
        txValue != null &&
        receiptValue != null &&
        String(txValue).toLowerCase() !== String(receiptValue).toLowerCase()
      ) {
        warnings.push(
          `${key} differs between the transaction and receipt. The receipt value is shown.`,
        );
      }
    }
    if (receipt && actualFee !== null && reward !== null && burn !== null) {
      amountsMatch = reward === actualFee / 5n && burn === actualFee - reward;
      if (!amountsMatch)
        warnings.push(
          "Reported reward and burn do not match the supplied 20% / remainder rule.",
        );
    } else if (receipt) {
      warnings.push(
        "The receipt is missing fee or reward amounts; the fee split cannot be checked.",
      );
    }
  }
  return {
    fields,
    hasAdmission,
    actualFee,
    reward,
    burn,
    amountsMatch,
    warnings,
  };
}
