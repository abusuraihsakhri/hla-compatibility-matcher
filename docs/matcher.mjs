// Deliberately limited demonstration catalog; not a clinical HLA reference.
export const catalog = [
  "A*02:01", "A*24:02", "B*07:02", "B*44:02",
  "DRB1*15:01", "DRB1*04:01", "C*07:01", "DQB1*06:02"
];

const norm = (value) => String(value ?? "").toUpperCase().replace(/[\s*:_-]/g, "");

export function lookup(query) {
  const q = norm(query);
  const all = q ? catalog.filter((allele) =>
    norm(allele) === q || norm(allele.split(":")[0]) === q
  ).map((allele) => [10, allele]) : [];
  return {query, top_hit: all.length === 1 ? all[0][1] : "no match",
    score: all.length === 1 ? 10 : 0, all: all.length === 1 ? all : []};
}

const allelePattern = /^(A|B|C|DRB1|DQB1)\*\d{2}:\d{2}(?::\d{2}){0,2}[A-Z]?$/i;
const splitAlleles = (text) => String(text).split(/[,;\n]+/).map((s) => s.trim()).filter(Boolean);

export function compareAlleles(donorText, recipientText) {
  const donor = splitAlleles(donorText);
  const recipient = splitAlleles(recipientText);
  if (!donor.length || !recipient.length) throw new Error("Enter at least one donor and one recipient allele.");
  const invalid = [...donor, ...recipient].filter((a) => !allelePattern.test(a));
  if (invalid.length) throw new Error("Use complete allele names such as A*02:01. Unsupported: " + invalid.join(", "));
  const recipientSet = new Set(recipient.map(norm));
  const shared = donor.filter((a) => recipientSet.has(norm(a)));
  const notShared = donor.filter((a) => !recipientSet.has(norm(a)));
  return {shared, notShared, donorCount: donor.length, recipientCount: recipient.length};
}

// RFC 4180-style quoted fields (including embedded commas, newlines, double quotes).
export function parseCSV(text) {
  const data = String(text).replace(/^\uFEFF/, "");
  const rows = [], row = [];
  let cell = "", quoted = false, closed = false;
  const addCell = () => {row.push(cell); cell = ""; closed = false;};
  const addRow = () => {addCell(); rows.push([...row]); row.length = 0;};
  for (let i = 0; i < data.length; i++) {
    const c = data[i];
    if (quoted) {
      if (c === '"' && data[i + 1] === '"') {cell += '"'; i++;}
      else if (c === '"') {quoted = false; closed = true;}
      else {cell += c;}
    } else if (c === '"' && !cell && !closed) {
      quoted = true;
    } else if (c === ",") {
      addCell();
    } else if (c === "\n" || c === "\r") {
      if (c === "\r" && data[i + 1] === "\n") i++;
      addRow();
    } else {
      if (closed) throw new Error("Invalid CSV: unexpected text after a closing quote.");
      if (c === '"') throw new Error("Invalid CSV: unexpected quote.");
      cell += c;
    }
  }
  if (quoted) throw new Error("Invalid CSV: unterminated quoted field.");
  if (cell || row.length || closed) addRow();
  if (!rows.length || !rows[0].length || !rows[0][0]) throw new Error("CSV must have a header row.");
  const headers = rows.shift();
  if (headers.some((h) => !h.trim()) || new Set(headers).size !== headers.length) {
    throw new Error("CSV headers must be nonempty and unique.");
  }
  if (rows.some((r) => r.length !== headers.length)) throw new Error("CSV rows have inconsistent column counts.");
  return {headers, records: rows.map((r) => Object.fromEntries(headers.map((h, i) => [h, r[i]])))};
}

function quoteCsv(value) {
  let s = String(value ?? "");
  // Prevent CSV formula injection in common spreadsheet applications.
  if (/^\s*[=+\-@]/.test(s)) s = "'" + s;
  return '"' + s.replace(/"/g, '""') + '"';
}

export function toCSV(headers, records) {
  return [headers.map(quoteCsv).join(","),
    ...records.map((row) => headers.map((h) => quoteCsv(row[h])).join(","))
  ].join("\r\n") + "\r\n";
}

if (typeof document !== "undefined") {
  const $ = (id) => document.getElementById(id);
  const status = (message, isError = false) => {
    $("status").textContent = message;
    $("status").classList.toggle("error", isError);
  };
  $("lookup-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const r = lookup($("query").value);
    $("lookup-result").textContent = r.top_hit === "no match"
      ? "No exact match in the eight-entry demonstration catalog."
      : "Catalog entry: " + r.top_hit + (norm($("query").value) !== norm(r.top_hit)
        ? " (shorthand; not high-resolution typing)" : "");
    status("Lookup completed locally.");
  });
  $("compare-form").addEventListener("submit", (e) => {
    e.preventDefault();
    try {
      const r = compareAlleles($("donor").value, $("recipient").value);
      $("compare-result").textContent =
        "Shared donor entries (" + r.shared.length + "/" + r.donorCount + "): " +
        (r.shared.join(", ") || "none") + "\nNot shared: " + (r.notShared.join(", ") || "none") +
        "\nThis is string-level overlap, NOT a clinical mismatch grade.";
      status("Allele-overlap comparison completed locally.");
    } catch (err) { $("compare-result").textContent = ""; status(err.message, true); }
  });
  let downloadUrl;
  $("csv-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const file = $("file").files[0];
    if (!file) return status("Select a CSV file.", true);
    if (file.size > 2_000_000) return status("CSV must be 2 MB or smaller.", true);
    try {
      const {headers, records} = parseCSV(await file.text());
      if (records.length > 10_000) throw new Error("CSV is limited to 10,000 data rows.");
      const col = ["query", "hla"].map((candidate) => headers.find((h) => h.toLowerCase() === candidate)).find(Boolean) || headers[0];
      const columns = [...new Set([...headers, "top_hit", "lookup_score"])];
      const output = records.map((row) => {
        const hit = lookup(row[col]);
        return {...row, top_hit: hit.top_hit, lookup_score: hit.score};
      });
      if (downloadUrl) URL.revokeObjectURL(downloadUrl);
      downloadUrl = URL.createObjectURL(new Blob([toCSV(columns, output)], {type: "text/csv;charset=utf-8"}));
      $("download").href = downloadUrl;
      $("download").hidden = false;
      $("csv-result").textContent = records.length + " records processed; download is ready.";
      status("CSV processed in your browser; no data was uploaded.");
    } catch (err) {
      $("download").hidden = true; $("csv-result").textContent = "";
      status(err.message, true);
    }
  });
  window.addEventListener("pagehide", () => {if (downloadUrl) URL.revokeObjectURL(downloadUrl);});
}
