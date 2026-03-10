/**
 * Google Apps Script — Readability Survey Backend
 *
 * SETUP (one-time):
 *  1. Go to script.google.com → New project
 *  2. Paste this entire file
 *  3. Click Deploy → New deployment → Web app
 *     - Execute as: Me
 *     - Who has access: Anyone
 *  4. Click Deploy, copy the Web App URL
 *  5. Paste that URL into index.html as APPS_SCRIPT_URL
 *
 * Data lands in the Google Sheet specified by SHEET_ID below.
 * Create a blank Google Sheet, copy its ID from the URL:
 *   https://docs.google.com/spreadsheets/d/SHEET_ID_HERE/edit
 */

const SHEET_ID = "PASTE_YOUR_GOOGLE_SHEET_ID_HERE";

function doPost(e) {
  try {
    const payload = JSON.parse(e.postData.contents);
    const sheet   = SpreadsheetApp.openById(SHEET_ID).getActiveSheet();

    // Write header row if the sheet is empty
    if (sheet.getLastRow() === 0) {
      sheet.appendRow([
        "rater_name", "internal_id", "display_order", "tercile",
        "structural_clarity", "contextual_quality", "overall_readability",
        "submitted_at"
      ]);
    }

    // Each payload contains one rater's full set of ratings
    const rows = payload.ratings || [];
    rows.forEach(r => {
      sheet.appendRow([
        payload.rater_name,
        r.internal_id,
        r.display_order,
        r.tercile,
        r.structural_clarity,
        r.contextual_quality,
        r.overall_readability,
        payload.submitted_at
      ]);
    });

    return ContentService
      .createTextOutput(JSON.stringify({ ok: true, rows: rows.length }))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    return ContentService
      .createTextOutput(JSON.stringify({ ok: false, error: err.message }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

// GET handler (health-check — visit the URL in a browser to confirm it works)
function doGet() {
  return ContentService
    .createTextOutput(JSON.stringify({ ok: true, status: "Readability survey backend running" }))
    .setMimeType(ContentService.MimeType.JSON);
}
