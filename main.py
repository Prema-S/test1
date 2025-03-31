from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Callable, Dict
import os
import uvicorn
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime, timedelta, timezone
import io
import zipfile
from PIL import Image
from bs4 import BeautifulSoup
import urllib3
import numpy as np
import colorsys
import httpx
import feedparser
import json
import warnings
warnings.filterwarnings("ignore")
import io
import re
from dateutil import parser
import subprocess
import shutil
from typing import Optional
from pathlib import Path
import aiohttp
import logging


load_dotenv()

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the request model
class AnswerResponse(BaseModel):
    answer: str

# Keep AIPROXY_TOKEN and NLP_API_URL without usage
AIPROXY_TOKEN = os.getenv("AIPROXY_TOKEN")
NLP_API_URL = "http://aiproxy.sanand.workers.dev/openai/v1/chat/completions"

# Function map to dynamically call the correct function based on regex patterns
function_map: Dict[str, Callable] = {}

# Function to recognise questions using regex pattern
def questions_tds(pattern: str):
    def decorator(func: Callable):
       function_map[pattern] = func
       return func
    return decorator

    
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)    
@questions_tds(r".*email set to.*")
async def ga1_q2(question: str) -> str:
    email_pattern = r"email set to\s*([\w.%+-]+@[\w.-]+\.[a-zA-Z]{2,})"
    match = re.search(email_pattern, question, re.IGNORECASE)  
    
    if match:
        email = match.group(1)
        url = "https://httpbin.org/get"
        command = f"uv run --with httpie -- https {url}?email={email}"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout
        
@app.post("/api/", response_model=AnswerResponse)
async def get_answer(question: str = Form(...), file: Optional[UploadFile] = None):
    try:
        #if file:
            #await handle_file(file)
        for pattern, func in function_map.items():
            if re.search(pattern, question, re.IGNORECASE):
                if file:
                    if 'file' in func.__code__.co_varnames and func.__code__.co_argcount == 1:
                        return AnswerResponse(answer=await func(file))
                    return AnswerResponse(answer=await func(question, file))
                else:
                    return AnswerResponse(answer=await func(question))

        return AnswerResponse(answer="No matching function found for the given question.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

#------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
