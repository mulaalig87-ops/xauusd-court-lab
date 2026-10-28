// Fetch a drand quicknet round from several relays and verify it locally:
// BLS signature (G1, RFC 9380 hash-to-curve) against the chain public key, and
// randomness == SHA-256(signature). No relay has to be trusted.
// usage: node verify.mjs <round|latest> <out.json>
import { bls12_381 } from "@noble/curves/bls12-381";
import { createHash } from "node:crypto";
import { writeFileSync } from "node:fs";

const CHAIN = "52db9ba70e0cc0f6eaf7803dd07447a1f5477735fd3f661792ba94600c84e971";
const RELAYS = ["https://api.drand.sh", "https://api2.drand.sh", "https://drand.cloudflare.com"];
const [arg, out] = process.argv.slice(2);

async function get(path) {
  const errs = [];
  for (const r of RELAYS) {
    try {
      const res = await fetch(`${r}/${CHAIN}/${path}`);
      if (res.ok) return { relay: r, body: await res.json() };
      errs.push(`${r}: HTTP ${res.status}`);
    } catch (e) { errs.push(`${r}: ${e}`); }
  }
  throw new Error("all relays failed: " + errs.join("; "));
}

const info = (await get("info")).body;
if (info.hash !== CHAIN) throw new Error("chain hash mismatch");
if (info.schemeID !== "bls-unchained-g1-rfc9380") throw new Error("unexpected scheme " + info.schemeID);
const { relay, body: b } = await get(arg === "latest" ? "public/latest" : `public/${arg}`);
if (arg !== "latest" && b.round !== Number(arg)) throw new Error("round mismatch");

const rb = Buffer.alloc(8); rb.writeBigUInt64BE(BigInt(b.round));
const msg = createHash("sha256").update(rb).digest();
const ok = bls12_381.verifyShortSignature(b.signature, msg, info.public_key);
const rnd = createHash("sha256").update(Buffer.from(b.signature, "hex")).digest("hex");
if (!ok) throw new Error("BLS signature INVALID");
if (rnd !== b.randomness) throw new Error("randomness != sha256(signature)");
const result = { chain: CHAIN, round: b.round, randomness: b.randomness, signature: b.signature,
  genesis_time: info.genesis_time, period: info.period,
  round_time: info.genesis_time + (b.round - 1) * info.period, relay, bls_verified: true };
console.log(JSON.stringify(result, null, 2));
if (out) writeFileSync(out, JSON.stringify(result, null, 2));
