from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import tempfile
import random
from moviepy.editor import VideoFileClip
import google.generativeai as genai
from pydantic import BaseModel
from typing import List, Optional
import python_multipart
import uuid
import logging
from dotenv import load_dotenv
import base64
import json
import re

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Interview Analysis API",
              description="Analyzes video interviews for soft skills and integrity using Gemini API")

try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
    templates = Jinja2Templates(directory="templates")
except Exception as e:
    logger.error(f"Failed to mount static files or templates: {str(e)}")
    raise

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

# Pydantic models for structured response
class FileData(BaseModel):
    data: str
    mime_type: str

class Message(BaseModel):
    role: str
    content: str | List[FileData]

class ChatRequest(BaseModel):
    message: str
    files: List[FileData] = []
    history: List[Message] = []
    system_prompt: str

class ChatResponse(BaseModel):
    response: str
    error: Optional[str] = None

class AnalysisReport(BaseModel):
    soft_skills: dict
    integrity: dict
    quantitative_scores: dict
    summary: dict


def process_video(video_path: str) -> tuple[str, float]:
    try:
        video = VideoFileClip(video_path)
        duration = video.duration
        video.close()
        return video_path,  duration
    except Exception as e:
        logger.error(f"Error validating video: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing video: {str(e)}")

# Function to strip markdown formatting
def strip_markdown(response_text: str) -> str:
    # Remove ```json ... ``` or similar markdown
    cleaned_text = re.sub(r'```json\s*|\s*```', '', response_text, flags=re.MULTILINE)
    return cleaned_text.strip()


'''def extract_random_segment(video_path: str, segment_duration: int = 600) -> str:
    try:
        video = VideoFileClip(video_path)
        video_duration = video.duration
        if video_duration < segment_duration:
            raise HTTPException(status_code=400, detail="Video duration is less than 10 minutes")

        max_start = video_duration - segment_duration
        start_time = random.uniform(0, max_start)
        end_time = start_time + segment_duration

        output_path = f"/tmp/{uuid.uuid4()}.mp4"
        video_subclip = video.subclip(start_time, end_time)
        video_subclip.write_videofile(output_path, codec="libx264", audio_codec="aac")
        video.close()
        video_subclip.close()
        return output_path
    except Exception as e:
        logger.error(f"Error extracting video segment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing video: {str(e)}")'''

# Prompt for Gemini API (unchanged as provided)
PROMPT = """
Your Role: You are an expert talent acquisition specialist, interpersonal dynamics analyst, and forensic linguistic examiner.

Primary Objective: Your task is to conduct a focused analysis of a job candidate's soft skills and to identify any potential indicators of cheating. For this assessment, "cheating" is defined specifically as the real-time use of a generative AI tool (like ChatGPT) on a second screen to formulate answers. Your analysis must be objective and use specific examples from the interview to justify your findings and scores. You will also assess how natural and likeable the candidate is.

Assessment Instructions:
Please analyze the provided interview recording and transcript. Present your findings in a structured report that addresses the following four parts.
Part 1: Soft Skills, Naturalness & Likeability Assessment
(For your internal analysis) Evaluate the candidate's interpersonal style, professional competencies, and overall demeanor.
Authenticity and Naturalness:
How genuine and natural does the candidate sound? Do they seem to be speaking spontaneously, or do their answers feel rehearsed?
Does the candidate's personality come through, or is it masked by a guarded or artificial persona?
Rapport and Likeability:
Based on their tone of voice, use of language, and energy, how would you rate the candidate's likeability?
Do they build a positive rapport with the interviewer? Look for signs of warmth and active listening.
Communication and Interpersonal Skills:
Clarity of Thought: How well does the candidate structure their thoughts and articulate their ideas spontaneously?
Active Listening: Does the candidate actively listen and engage, or do they seem distracted?
Key Behavioral Competencies:
Collaboration: How does the candidate talk about teamwork?
Adaptability: When presented with unexpected questions, do they respond thoughtfully, or is there a distinct change in their delivery?
Confidence and Self-Awareness: Does the candidate project genuine confidence in their own abilities?
Part 2: Interview Integrity & AI Cheating Assessment
Critically analyze the interview for indicators that the candidate may be using a generative AI tool in real-time. Focus on the following patterns, which are distinct from simply being nervous or having prepared notes.
Unnatural Pauses and Delivery:
Listen for distinct, unnatural pauses before the candidate begins to speak, which could indicate they are typing a prompt and waiting for an answer to be generated.
Does the candidate's speech become suddenly monotonic and lose its natural intonation when delivering complex answers, as if they are reading text from a screen?
Overly Polished and Inhuman Speech:
Do answers sound too perfect? Look for language that is overly formal, perfectly structured, and lacks the normal conversational fillers (e.g., "um," "you know," "like") that are part of spontaneous thought.
Is there a noticeable shift between their natural, conversational style on simple questions and a robotic, encyclopedic style on more complex ones?
Physical Cues (Eye Movement & Distraction):
Does the candidate's eye movement consistently shift to a second location (away from the camera) in a steady, rhythmic way that suggests reading, rather than the natural, fleeting glances of someone thinking?
Does the candidate appear distracted or less engaged with the interviewer, as if their attention is divided between the conversation and another source of information?
Part 3: Quantitative Assessment Summary
Based on your detailed analysis in Parts 1 and 2, provide a score from 1 to 100 for each of the following metrics. A score of 1 represents an extremely poor performance, while 100 is exceptional.
Naturalness Score: (Authenticity and spontaneity of responses)
Likeability & Rapport Score: (Ability to build a positive human connection)
Communication Clarity Score: (Clarity of thought and effective expression)
Active Listening Score: (Demonstrated engagement with and understanding of the interviewer)
Confidence Score: (Balanced, genuine self-assurance)
Adaptability Score: (Positive and constructive response to unexpected questions)
Interview Integrity Score: (Overall confidence in the authenticity of the performance. A high score (e.g., 90-100) indicates high integrity with no signs of AI-cheating. A low score indicates strong evidence of real-time AI use.)
Part 4: Final Summary and Recommendation
Drawing from your qualitative analysis and the quantitative scores in Part 3, conclude your report with a concise summary.
Key Soft Skill Strengths: List the candidate's top 3 interpersonal strengths, referencing their highest scores from Part 3.
Potential Interpersonal Gaps or Concerns: List 2-3 areas for development, referencing their lowest scores from Part 3.
Integrity Assessment: Provide a summary of your findings regarding interview integrity, explicitly stating the final Interview Integrity Score and what it implies about the likelihood of real-time AI assistance.
Overall Recommendation: Based on their soft skills and the integrity of their interview performance, provide a clear recommendation. Should the hiring manager be confident in this candidate's interpersonal fit and trustworthiness? Justify your recommendation with key evidence and scores.

**Output**:
Return only a JSON object matching this structure. **Do not include any text outside the JSON, such as transcripts or introductions.**:
{
  "soft_skills": {
    "authenticity_naturalness": {
      "description": "Description of authenticity and spontaneity",
      "examples": ["Example from the video"]
    },
    "rapport_likeability": {
      "description": "Description of likeability and rapport",
      "examples": ["Example from the video"]
    },
    "communication_interpersonal": {
      "clarity": "Assessment of thought clarity",
      "active_listening": "Assessment of active listening",
      "collaboration": "Assessment of collaboration skills",
      "adaptability": "Assessment of adaptability",
      "confidence": "Assessment of confidence",
      "examples": ["Example from the video"]
    }
  },
  "integrity": {
    "pauses_delivery": {
      "description": "Analysis of pauses and delivery",
      "examples": ["Example from the video"]
    },
    "speech_patterns": {
      "description": "Analysis of speech for overly polished patterns",
      "examples": ["Example from the video"]
    },
    "physical_cues": {
      "description": "Analysis of eye movement and distraction cues",
      "examples": ["Example from the video"]
    }
  },
  "quantitative_scores": {
    "naturalness": <1-100>,
    "likeability_rapport": <1-100>,
    "communication_clarity": <1-100>,
    "active_listening": <1-100>,
    "confidence": <1-100>,
    "adaptability": <1-100>,
    "interview_integrity": <1-100>
  },
  "summary": {
    "strengths": ["Strength 1", "Strength 2", "Strength 3"],
    "gaps": ["Gap 1", "Gap 2"],
    "integrity_assessment": {
      "description": "Summary of integrity findings",
      "score": <1-100>
    },
    "recommendation": "Recommendation with justification"
  }
}
"""

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        logger.error(f"Error rendering index.html: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to render homepage")

@app.get("/examples", response_class=HTMLResponse)
async def examples(request: Request):
    try:
        return templates.TemplateResponse("examples.html", {"request": request})
    except Exception as e:
        logger.error(f"Error rendering examples.html: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to render examples page")

@app.get("/upload", response_class=HTMLResponse)
async def upload(request: Request):
    try:
        return templates.TemplateResponse("upload.html", {"request": request})
    except Exception as e:
        logger.error(f"Error rendering upload.html: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to render upload page")

@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    try:
        return templates.TemplateResponse("about.html", {"request": request})
    except Exception as e:
        logger.error(f"Error rendering about.html: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to render about page")

@app.post("/analyze", response_model=AnalysisReport)
async def analyze_video(file: UploadFile = File(...)):
    try:
        # Validate file type
        if not file.content_type.startswith("video/"):
            raise HTTPException(status_code=400, detail="Uploaded file must be a video")

        # Save uploaded video temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
            tmp_file.write(await file.read())
            tmp_file_path = tmp_file.name

        # Extract random 10-minute segment
        video_path, video_duration = process_video(tmp_file_path)

        # Read video segment as bytes
        with open(video_path, "rb") as f:
            video_bytes = f.read()

        # Prepare Gemini API request
        file_data = FileData(data=base64.b64encode(video_bytes).decode("utf-8"), mime_type="video/mp4")
        # chat_request = ChatRequest(
        #     files=[file_data],
        #     system_prompt=PROMPT
        # )

        # Call Gemini API
        response = model.generate_content(
            contents=[
                {
                    "role": "user",
                    "parts": [
                        {"text": PROMPT},
                        {"inline_data": {"mime_type": file_data.mime_type, "data": file_data.data}}
                    ]
                }
            ]
        )

        # Log raw response for debugging
        logger.info(f"Gemini API raw response: {response.text[:1000]}...")

        # Strip markdown and parse response
        cleaned_response = strip_markdown(response.text)
        logger.info(f"Cleaned response: {cleaned_response[:1000]}...")

        try:
            analysis = json.loads(cleaned_response)
        except json.JSONDecodeError:
            logger.warning("Non-JSON response detected after cleaning, attempting retry")
            # Retry with explicit instruction
            retry_response = model.generate_content(
                contents=[
                    {
                        "role": "user",
                        "parts": [
                            {
                                "text": f"{PROMPT}\n\nReturn only the JSON analysis as specified. Do NOT include markdown, transcripts, or any non-JSON text."
                            },
                            {"inline_data": {"mime_type": file_data.mime_type, "data": file_data.data}}
                        ]
                    }
                ]
            )

            logger.info(f"Gemini API retry response: {retry_response.text[:1000]}...")
            cleaned_retry_response = strip_markdown(retry_response.text)
            logger.info(f"Cleaned retry response: {cleaned_retry_response[:1000]}...")
            try:
                analysis = json.loads(cleaned_retry_response)
            except json.JSONDecodeError as json_err:
                logger.error(f"Failed to parse retry response as JSON: {cleaned_retry_response[:1000]}...")
                raise HTTPException(
                    status_code=500,
                    detail=f"Invalid response from Gemini API after retry: {cleaned_retry_response[:500]}"
                )

        try:
            analysis_report = AnalysisReport(**analysis)
        except ValueError as e:
            logger.error(f"Response does not match AnalysisReport model: {str(e)}")
            raise HTTPException(status_code=422, detail=f"Invalid analysis structure: {str(e)}")

        # Clean up temporary files
        os.remove(tmp_file_path)

        return AnalysisReport(**analysis)

    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)