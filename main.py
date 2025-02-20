import json

import anthropic
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# Define the request model
class PDFRequest(BaseModel):
    id: str
    pdf_base64: str

@app.get("/")
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
        print(prompt)
        client = anthropic.Anthropic(api_key="your_anthropic_api_key")
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
        return message

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
