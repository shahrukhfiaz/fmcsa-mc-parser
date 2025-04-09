from flask import Flask, request, jsonify
import requests
import re
from PyPDF2 import PdfReader
import io

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
        return {"error": "PDF not available", "status": res.status_code}, 400

    reader = PdfReader(io.BytesIO(res.content))
    text = ""
    for page in reader.pages:
        text += page.extract_text()

    mc_numbers = re.findall(r'MC-\\d{4,6}', text)
    return jsonify({
        "mc_numbers": list(set(mc_numbers)),
        "total": len(mc_numbers),
        "date": date
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
