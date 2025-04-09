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

    reader = PdfReader(io.BytesIO(res.content))
    full_text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            full_text += page_text + "\n"

    # Extract only the text between the two specific headings
    pattern = r"CERTIFICATES, PERMITS & LICENSES FILED AFTER JANUARY 1, 1995\s+NUMBER(.*?)CERTIFICATES OF REGISTRATION\s+NUMBER"
    match = re.search(pattern, full_text, re.DOTALL | re.IGNORECASE)

    if match:
        target_text = match.group(1)
    else:
        return {
            "error": "Section not found",
            "pdf_url": pdf_url,
            "date": date
        }, 404

    # Extract MC numbers only from the targeted section
    mc_numbers = re.findall(r'MC-\d{4,8}', target_text)

    return jsonify({
        "mc_numbers": sorted(set(mc_numbers)),
        "total": len(set(mc_numbers)),
        "date": date,
        "pdf_url": pdf_url
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
