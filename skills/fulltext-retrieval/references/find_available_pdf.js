/*
 * Find Available PDF — batch trigger for Zotero (user-run snippet)
 * ----------------------------------------------------------------
 * Attaches full-text PDFs to library items using Zotero's OWN
 * "Find Available PDF" resolver. This reuses whatever OpenURL resolver,
 * institutional proxy, or library configuration YOU have already set in
 * Zotero — so it typically retrieves far more than open-access-only resolvers,
 * yet no credentials, proxy hosts, or institutional identifiers ever leave
 * your Zotero client. Nothing here is hard-coded to any institution.
 *
 * HOW TO RUN
 *   1. In Zotero, select the items (or open the collection) you want PDFs for.
 *   2. Tools → Developer → Run JavaScript.
 *   3. Paste this whole snippet and click Run.
 *   4. The result panel prints a JSON summary: considered / attached /
 *      alreadyHadPDF / missing (DOIs still without a PDF).
 *
 * NO-CODE FALLBACK
 *   Select items → right-click → "Find Available PDF" does the same thing
 *   interactively. Use it if you prefer not to run a script.
 *
 * VERSION NOTE
 *   Zotero 7 exposes a batch Zotero.Attachments.addAvailablePDFs(items);
 *   Zotero 6 only has the per-item Zotero.Attachments.addAvailablePDF(item).
 *   This snippet prefers the batch call and falls back to per-item.
 *
 * NOTE: results are user-initiated and depend on your live Zotero session;
 * they are NOT reproducible CI evidence. Record retrieved/not-retrieved
 * outcomes from the printed summary into your retrieval report manually.
 */

var pane = Zotero.getActiveZoteroPane();
var items = pane.getSelectedItems().filter(function (it) { return it.isRegularItem(); });

// Fall back to the whole selected collection if nothing is selected.
if (!items.length) {
  var collection = pane.getSelectedCollection();
  if (collection) {
    items = collection.getChildItems().filter(function (it) { return it.isRegularItem(); });
  }
}

function hasPDF(item) {
  return item.getAttachments().some(function (id) {
    var att = Zotero.Items.get(id);
    if (!att) return false;
    if (typeof att.isPDFAttachment === "function") return att.isPDFAttachment();
    return att.attachmentContentType === "application/pdf";
  });
}

var todo = items.filter(function (it) { return !hasPDF(it); });
var alreadyHadPDF = items.length - todo.length;

if (typeof Zotero.Attachments.addAvailablePDFs === "function") {
  await Zotero.Attachments.addAvailablePDFs(todo);   // Zotero 7 batch
} else {
  for (let it of todo) {                              // Zotero 6 per-item
    try {
      await Zotero.Attachments.addAvailablePDF(it);
    } catch (e) {
      Zotero.debug("addAvailablePDF failed for item " + it.id + ": " + e);
    }
  }
}

var attached = 0;
var missing = [];
for (let it of todo) {
  if (hasPDF(it)) {
    attached++;
  } else {
    missing.push(it.getField("DOI") || it.getField("title") || ("itemID:" + it.id));
  }
}

return JSON.stringify({
  considered: items.length,
  attached: attached,
  alreadyHadPDF: alreadyHadPDF,
  missing: missing
}, null, 2);
