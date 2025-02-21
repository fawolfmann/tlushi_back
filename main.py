import json
import os

import anthropic
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# Define the request model
class PDFRequest(BaseModel):
    id: str
    pdf_base64: str

@app.get("/healthz")
async def read_root():
    return {"message": "Hello, World!"}

@app.post("/extract")
async def extract_pdf(request: PDFRequest):
    try:
        # Define the prompt and load additional JSON data from a file
        prompt = "Extract all the information and translate the fields and return a dictionary with the extracted information from this PDF file using the same structure like here: \n"
        with open("payslip-data.json", "r") as json_file:
            additional_json = json.load(json_file)

        prompt += str(additional_json)

        prompt += "\n Return a Json data only"
        print(prompt)
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": request.pdf_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
        )
        default_deducts = {
            "income_tax": 44355.04,
            "national_insurance": 2555.76,
            "health_insurance": 2037.23,
            "histadrut_214": 1648.22,
            "histadrut_662": 1011.78,
            "histadrut_154": 392.80
        },
        data = json.loads(message.content[0].text)
        gross = data["totals"]["gross_salary"]
        income_tax = gross - data.get("deductions", default_deducts).get("income_tax", 44355.04)
        rem1 = gross - income_tax
        bituach_leumi = data.get("deductions", default_deducts).get("national_insurance", 2555.76)
        rem2 = rem1 - bituach_leumi
        health_insurance = data.get("deductions", default_deducts).get("health_insurance", 2037.23)
        rem3 = rem2 - health_insurance
        pension = data.get("deductions", default_deducts).get("pension_fund_579",  773.23)
        rem4 = rem3 - pension
        study_fund = data.get("deductions", default_deducts).get("advanced_study_fund", 1283.55)
        rem5 = rem4 - study_fund


        analytics = {
            "waterfall":{
                { "item": "Total Salary", "over": 0, "deductions": 0, "total": gross},
                { "item": "Income Tax", "over": rem1, "deductions": income_tax, "total": 0 },
                { "item": "Bituach Leumi", "over": rem2, "deductions": bituach_leumi, "total": 0 },
                { "item": "Health Insurance", "over": rem3, "deductions": health_insurance, "total": 0 },
                { "item": "Pension", "over": rem4, "deductions": pension, "total": 0 },
                { "item": "Study Fund", "over": rem5, "deductions": study_fund, "total": 0 },
                { "item": "Money in pocket", "over": 0, "deductions": 0, "total": rem5 }
            },
            "base_salary": gross,
            "net_salary": rem5, 
            "vacations_days": data.get("attendance", {"vacation": {"used": 6.35,"remaining": 0},}).get("vacation", {"used": 6.35}).get("used", 6.35)
        }
        
        json_output = json.dumps(data)
        print(json_output)
        print(analytics)
        return {"response":json_output, "id":request.id, "analytics":analytics}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
