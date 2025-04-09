from flask import Flask, request, jsonify
import requests
import re
from PyPDF2 import PdfReader
import io
import os

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
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text

    mc_numbers = re.findall(r'MC-\d{4,6}', text)

    return jsonify({
        "mc_numbers": sorted(set(mc_numbers)),
        "total": len(set(mc_numbers)),
        "date": date,
        "source": pdf_url
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
