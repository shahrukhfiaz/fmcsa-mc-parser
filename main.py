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

    mc_numbers = []

    # Section 1: Between 'CERTIFICATES, PERMITS...' and 'CERTIFICATES OF REGISTRATION'
    pattern_1 = r"CERTIFICATES, PERMITS & LICENSES FILED AFTER JANUARY 1, 1995\s+NUMBER(.*?)CERTIFICATES OF REGISTRATION\s+NUMBER"
    match_1 = re.search(pattern_1, full_text, re.DOTALL | re.IGNORECASE)
    if match_1:
        text_1 = match_1.group(1)
        mc_numbers += re.findall(r'MC-\d{4,8}', text_1)

    # Section 2: Between 'CERTIFICATES OF REGISTRATION' and 'DISMISSALS'
    pattern_2 = r"CERTIFICATES OF REGISTRATION\s+NUMBER(.*?)DISMISSALS\s+Decisions"
    match_2 = re.search(pattern_2, full_text, re.DOTALL | re.IGNORECASE)
    if match_2:
        text_2 = match_2.group(1)
        mc_numbers += re.findall(r'MC-\d{4,8}', text_2)

    return jsonify({
        "mc_numbers": sorted(set(mc_numbers)),
        "total": len(set(mc_numbers)),
        "date": date,
        "pdf_url": pdf_url
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
