import assert from "node:assert/strict";
import { test } from "node:test";
import {
  analyzeAdmission,
  formatClx,
  quantity,
  validAddress,
  validHash,
} from "../network-info/admission.js";

const signer = "0xeb8c07def4c5a2541de730b027376e1068aa861a";
const recipient = "0xed2772838f7a7aec042a972084998cb30d63b660";
const receipt = {
  commonTxApprover: signer,
  commonTxRewardRecipient: recipient,
  commonTxAdmissionChainId: "0x9a249f",
  gasUsed: "0x5208",
  effectiveGasPrice: "0x3b9aca00",
  commonTxApproverReward: "0x3d1e3821000",
  commonTxBurn: "0xf478e084000",
};

test("sample fee split uses exact wei and a distinct recipient", () => {
  const result = analyzeAdmission({}, receipt);
  assert.equal(result.actualFee, 21000000000000n);
  assert.equal(result.reward, 4200000000000n);
  assert.equal(result.burn, 16800000000000n);
  assert.equal(result.amountsMatch, true);
  assert.deepEqual(result.warnings, []);
  assert.equal(formatClx(result.reward), "0.0000042 CLX");
  assert.equal(formatClx(result.burn), "0.0000168 CLX");
});

test("rounding retains all remaining wei in burn above Number precision", () => {
  const fee = 90071992547409939n;
  const result = analyzeAdmission(
    {},
    {
      ...receipt,
      gasUsed: "0x1",
      effectiveGasPrice: `0x${fee.toString(16)}`,
      commonTxApproverReward: `0x${(fee / 5n).toString(16)}`,
      commonTxBurn: `0x${(fee - fee / 5n).toString(16)}`,
    },
  );
  assert.equal(result.amountsMatch, true);
  assert.equal(result.reward + result.burn, fee);
  assert.equal(formatClx(1n), "0.000000000000000001 CLX");
  assert.equal(formatClx(10n ** 18n), "1 CLX");
});

test("missing B never falls back to A", () => {
  const { commonTxRewardRecipient, ...missingRecipient } = receipt;
  const result = analyzeAdmission({}, missingRecipient);
  assert.equal(result.fields.commonTxRewardRecipient, null);
  assert.ok(
    result.warnings.some((message) => message.includes("No payout to A")),
  );
});

test("mismatched identities and fields are visible", () => {
  const result = analyzeAdmission(
    { ...receipt, commonTxRewardRecipient: signer },
    receipt,
  );
  assert.equal(result.fields.commonTxRewardRecipient, recipient);
  assert.ok(
    result.warnings.some((message) => message.includes("differs between")),
  );
  assert.ok(
    analyzeAdmission(
      {},
      { ...receipt, commonTxRewardRecipient: signer },
    ).warnings.some((message) => message.includes("identical")),
  );
  assert.ok(
    analyzeAdmission(
      {},
      { ...receipt, commonTxAdmissionChainId: "0x1" },
    ).warnings.some((message) => message.includes("chain ID")),
  );
});

test("pending transactions never imply a credited reward", () => {
  const result = analyzeAdmission(receipt, null);
  assert.equal(result.reward, null);
  assert.equal(result.burn, null);
  assert.equal(result.amountsMatch, null);
  assert.ok(
    result.warnings.some((message) => message.includes("not confirmed")),
  );
});

test("missing, zero and inconsistent reported amounts remain distinct", () => {
  assert.equal(analyzeAdmission({}, {}).hasAdmission, false);
  const missing = analyzeAdmission({}, { ...receipt, commonTxBurn: null });
  assert.equal(missing.burn, null);
  assert.equal(missing.amountsMatch, null);
  assert.equal(
    analyzeAdmission({}, { ...receipt, commonTxBurn: "0x0" }).amountsMatch,
    false,
  );
  const zero = analyzeAdmission(
    {},
    {
      ...receipt,
      gasUsed: "0x0",
      commonTxApproverReward: "0x0",
      commonTxBurn: "0x0",
    },
  );
  assert.equal(zero.amountsMatch, true);
});

test("rejects malformed hashes, addresses and RPC quantities", () => {
  assert.equal(validHash("0x" + "a".repeat(64)), true);
  assert.equal(validHash("0x<script>"), false);
  assert.equal(validAddress(signer), true);
  assert.equal(validAddress("javascript:alert(1)"), false);
  for (const value of [null, undefined, 123, "1.2", "-1", "0xz"]) {
    assert.equal(quantity(value), null);
  }
});
