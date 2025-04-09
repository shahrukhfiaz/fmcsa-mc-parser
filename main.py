from flask import Flask, request, jsonify
import requests
import io
from PyPDF2 import PdfReader
import os
import re

app = Flask(__name__)

@app.route("/parse", methods=["GET"])
def parse_pdf():
    date = request.args.get('date')  # Format: YYYYMMDD
    if not date:
        return {"error": "Missing date"}, 400

    pdf_url = f"https://li-public.fmcsa.dot.gov/lihtml/rptspdf/LI_REGISTER{date}.PDF"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/pdf",
        "Referer": "https://li-public.fmcsa.dot.gov/"
    }

    res = requests.get(pdf_url, headers=headers)
    if res.status_code != 200:
        return {
            "error": "PDF not available",
            "status": res.status_code,
            "pdf_url": pdf_url
        }, 400

    # Read the PDF
    reader = PdfReader(io.BytesIO(res.content))
    full_text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            full_text += page_text + "\n"

    # Normalize text for regex matching
    normalized_text = re.sub(r'\s+', ' ', full_text)

    # Match section 1: CERTIFICATES, PERMITS & LICENSES FILED AFTER JANUARY 1, 1995
    section_1 = re.search(
        r'(CERTIFICATES.*?JANUARY 1, 1995)(.*?)(?=[A-Z][A-Z ]{10,})',
        normalized_text,
        re.IGNORECASE,
    )

    # Match section 2: CERTIFICATES OF REGISTRATION
    section_2 = re.search(
        r'(CERTIFICATES OF REGISTRATION)(.*?)(?=[A-Z][A-Z ]{10,})',
        normalized_text,
        re.IGNORECASE,
    )

    # Combine matched sections for MC number extraction
    text_to_search = ""
    if section_1:
        text_to_search += section_1.group(2)
    if section_2:
        text_to_search += section_2.group(2)

    # Extract MC numbers from the selected text
    mc_numbers = re.findall(r'MC-\d{4,6}', text_to_search)

    return jsonify({
        "mc_numbers": sorted(set(mc_numbers)),
        "total": len(set(mc_numbers)),
        "date": date,
        "pdf_url": pdf_url
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
