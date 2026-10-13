import test from "node:test";
import assert from "node:assert/strict";
import {lookup, compareAlleles, parseCSV, toCSV} from "../docs/matcher.mjs";

test("exact allele and legacy shorthand lookup", () => {
  assert.equal(lookup("A*02:01").top_hit, "A*02:01");
  assert.equal(lookup("a02").top_hit, "A*02:01");
  assert.equal(lookup("DRB115").top_hit, "DRB1*15:01");
  assert.equal(lookup("A*02:011").top_hit, "no match");
  assert.equal(lookup("xxxA02xxx").score, 0);
});

test("overlap counts only exact typed strings", () => {
  const r = compareAlleles("A*02:01, B*07:02", "a*02:01, B*44:02");
  assert.deepEqual(r.shared, ["A*02:01"]);
  assert.deepEqual(r.notShared, ["B*07:02"]);
  assert.throws(() => compareAlleles("A02", "A*02:01"), /complete allele/);
});

test("CSV parser supports BOM, quoted multiline cells, and escaped quotes", () => {
  const r = parseCSV('\uFEFFquery,note\r\n"A*02:01","text, ""quoted"""\r\n"B*07:02","two\nlines"\r\n');
  assert.equal(r.records.length, 2);
  assert.equal(r.records[0].note, 'text, "quoted"');
  assert.equal(r.records[1].note, "two\nlines");
});

test("CSV parser rejects malformed or inconsistent rows", () => {
  assert.throws(() => parseCSV('hla,note\n"A*02:01,foo'), /unterminated/);
  assert.throws(() => parseCSV("hla,note\nA*02:01\n"), /inconsistent/);
  assert.throws(() => parseCSV("hla,hla\nx,y"), /unique/);
});

test("CSV output neutralizes spreadsheet formula injection", () => {
  const csv = toCSV(["query","top_hit"], [{query:'=HYPERLINK("x")',top_hit:"no match"}]);
  assert.match(csv, /"'=HYPERLINK/);
  assert.match(csv, /"no match"/);
});
