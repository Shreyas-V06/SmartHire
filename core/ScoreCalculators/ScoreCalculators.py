import re
import time
from llama_index.llms.gemini import Gemini
from dotenv import load_dotenv
import os
from typing import Dict, Any

load_dotenv()
google_api_key = os.getenv('GOOGLE_API_KEY')
finetuned_api_key = os.getenv('FINETUNED_API_KEY')

def extract_number(text):
    """Extract the first number from text."""
    numbers = re.findall(r'\d*\.?\d+', str(text))
    return float(numbers[0]) if numbers else 0

def CalculateQuantitativeScore(parameter, max_value, benefit_type, query_engine):
    """Calculate score for quantitative parameters using RAG."""
    try:
        query_text = f"What is the {parameter}? Return only the numerical value."
        response = query_engine.query(query_text)
        time.sleep(1)  # Rate limiting delay
        
        if not response:
            return 0
            
        raw_value = extract_number(str(response))
        
        # Normalize the score to percentage (0-100)
        if benefit_type == "higher":
            score = min((raw_value / max_value) * 100, 100)
        else:  # Low is better
            score = max((1 - (raw_value / max_value)) * 100, 0)
        
        return score
    except Exception as e:
        print(f"Error in quantitative scoring: {e}")
        return 0
    
def CalculateBooleanScore(parameter, query_engine):
    """Calculate score for boolean parameters."""
    try:
        query_text = f"Does the candidate have {parameter}? Answer with True or False only."
        response = query_engine.query(query_text)
        time.sleep(1)  # Rate limiting delay
        answer = str(response).lower()
        return 100 if "true" in answer or "yes" in answer else 0
    except Exception as e:
        print(f"Error in boolean scoring: {e}")
        return 0
    
def CalculateTextualScore(parameter: str, resume_text: str) -> float:
    """Calculate score for textual parameters using Gemini model."""
    try:
        ft_api_key = os.getenv('FINETUNED_API_KEY')  # Get API key 
        if not ft_api_key:
            raise ValueError("FINETUNED_API_KEY not found in environment")
            
        model = Gemini(api_key=ft_api_key)
        
        # First get evaluation response
        eval_prompt = f"""
        You are an expert evaluator for an AI-powered recruitment system called SmartHire. Your task is to assess a candidate's depth of knowledge in a specific *textual parameter* based on their resume.  

### Instructions:  
1. *Analyze* the resume for detailed mentions of the evaluation parameter.  
2. *Look for indicators* of depth, such as specific projects, work experience, research, publications, or advanced-level explanations.  
3. *Assign a score from 0.0 to 100.0, allowing values **up to one decimal place*.  
4. *Provide a justification* for the assigned score, citing relevant parts of the resume.  

### Input Data:
*Candidate Resume:*  
{resume_text}  

*Evaluation Parameter:*  
{parameter}  

### Output Format:
*Score:* [1 - 100]  
*Justification:* [A brief but clear explanation based on resume content]

Now, evaluate the resume accordingly."""

        evaluation = model.complete(eval_prompt)
        
        # Then extract just the score
        score_prompt = evaluation.text + "\nBased on the given evaluation\nWhat is the score? Give the correct numerical value with no additional words"
        score_response = model.complete(score_prompt)
        
        # Convert score to float and ensure it's between 0-100
        try:
            score = float(score_response.text.strip())
            return score
        except ValueError:
            print(f"Could not convert score text to float: {score_response.text}")
            return 0.0
            
    except Exception as e:
        print(f"Error in textual scoring: {str(e)}")
        return 0.0