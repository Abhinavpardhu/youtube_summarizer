import json
import os
import re
from urllib.parse import parse_qs, urlparse

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise RuntimeError(
        "GOOGLE_API_KEY is missing. Add it to your .env file."
    )


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="YouTube Video Summarizer",
    description="Summarize YouTube videos using transcripts and Gemini",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REQUEST / RESPONSE MODELS
# ============================================================

class SummarizeRequest(BaseModel):
    youtube_url: str


class SummaryResponse(BaseModel):
    summary: str
    key_points: list[str]
    important_concepts: list[str]
    takeaway: str


# ============================================================
# EXTRACT YOUTUBE VIDEO ID
# ============================================================

def extract_video_id(youtube_url: str) -> str:

    if not youtube_url or not youtube_url.strip():
        raise ValueError("YouTube URL cannot be empty.")

    youtube_url = youtube_url.strip()

    try:
        parsed_url = urlparse(youtube_url)
        hostname = parsed_url.hostname

        if hostname:
            hostname = hostname.lower().replace("www.", "")

        # ----------------------------------------------------
        # youtu.be/VIDEO_ID
        # ----------------------------------------------------

        if hostname == "youtu.be":

            video_id = parsed_url.path.strip("/").split("/")[0]

            if video_id:
                return video_id

        # ----------------------------------------------------
        # youtube.com
        # ----------------------------------------------------

        if hostname in ["youtube.com", "m.youtube.com"]:

            # youtube.com/watch?v=VIDEO_ID
            if parsed_url.path == "/watch":

                query_params = parse_qs(parsed_url.query)

                video_id = query_params.get("v", [None])[0]

                if video_id:
                    return video_id

            # youtube.com/shorts/VIDEO_ID
            if parsed_url.path.startswith("/shorts/"):

                parts = parsed_url.path.strip("/").split("/")

                if len(parts) >= 2:
                    return parts[1]

            # youtube.com/embed/VIDEO_ID
            if parsed_url.path.startswith("/embed/"):

                parts = parsed_url.path.strip("/").split("/")

                if len(parts) >= 2:
                    return parts[1]

    except Exception:
        pass

    # --------------------------------------------------------
    # Fallback regex
    # --------------------------------------------------------

    match = re.search(
        r"(?:v=|youtu\.be/|/shorts/|/embed/)([A-Za-z0-9_-]{11})",
        youtube_url,
    )

    if match:
        return match.group(1)

    raise ValueError(
        "Invalid YouTube URL. Please provide a valid YouTube video URL."
    )


# ============================================================
# GET YOUTUBE TRANSCRIPT
# ============================================================

def get_transcript(video_id: str) -> str:

    try:

        print("\nFetching transcript...")
        print("Video ID:", video_id)

        api = YouTubeTranscriptApi()

        # This is the same method that worked in your test file
        transcript = api.fetch(
            video_id,
            languages=["en", "hi"]
        )

        transcript_text = " ".join(
            snippet.text
            for snippet in transcript
            if snippet.text
        )

        if not transcript_text.strip():
            raise ValueError("The transcript is empty.")

        print("Transcript fetched successfully.")
        print("Transcript length:", len(transcript_text))

        return transcript_text

    except Exception as error:

        print("\nTRANSCRIPT ERROR:")
        print(repr(error))

        raise ValueError(
            f"Unable to fetch transcript: {str(error)}"
        ) from error


# ============================================================
# GEMINI MODEL
# ============================================================

model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.2,
    google_api_key=GOOGLE_API_KEY,
)


# ============================================================
# PROMPT
# ============================================================

prompt = ChatPromptTemplate.from_template(
    """
You are an expert YouTube video summarizer.

Analyze the following YouTube transcript.

Return the result as valid JSON with exactly these keys:

{{
    "summary": "A concise summary of the entire video",
    "key_points": [
        "Important point 1",
        "Important point 2",
        "Important point 3",
        "Important point 4",
        "Important point 5"
    ],
    "important_concepts": [
        "Important concept 1",
        "Important concept 2",
        "Important concept 3"
    ],
    "takeaway": "The main takeaway from the video"
}}

Rules:

1. Use ONLY information present in the transcript.
2. Do not invent information.
3. Keep the summary clear and concise.
4. Give exactly 5 key points when possible.
5. Give 2-5 important concepts.
6. The response must be valid JSON.
7. Do not use Markdown code fences.
8. Do not add any text before or after the JSON.

Transcript:

{transcript}
"""
)


# ============================================================
# LANGCHAIN CHAIN
# ============================================================

chain = prompt | model


# ============================================================
# GENERATE SUMMARY
# ============================================================

def generate_summary(transcript: str) -> dict:

    try:

        print("\nSending transcript to Gemini...")

        response = chain.invoke(
            {
                "transcript": transcript
            }
        )

        # ----------------------------------------------------
        # Get response content
        # ----------------------------------------------------

        response_text = response.content

        # Sometimes content can be a list
        if isinstance(response_text, list):

            parts = []

            for item in response_text:

                if isinstance(item, str):
                    parts.append(item)

                elif isinstance(item, dict):
                    if "text" in item:
                        parts.append(str(item["text"]))

            response_text = "".join(parts)

        else:
            response_text = str(response_text)

        response_text = response_text.strip()

        print("\nGemini response received.")

        # ----------------------------------------------------
        # Remove Markdown code fences if Gemini adds them
        # ----------------------------------------------------

        if response_text.startswith("```"):

            response_text = re.sub(
                r"^```(?:json)?\s*",
                "",
                response_text,
                flags=re.IGNORECASE,
            )

            response_text = re.sub(
                r"\s*```$",
                "",
                response_text,
            ).strip()

        # ----------------------------------------------------
        # Parse JSON
        # ----------------------------------------------------

        parsed = json.loads(response_text)

        # ----------------------------------------------------
        # Validate required fields
        # ----------------------------------------------------

        required_fields = [
            "summary",
            "key_points",
            "important_concepts",
            "takeaway",
        ]

        for field in required_fields:

            if field not in parsed:
                raise ValueError(
                    f"Gemini response is missing field: {field}"
                )

        if not isinstance(parsed["key_points"], list):
            raise ValueError(
                "key_points must be a list."
            )

        if not isinstance(parsed["important_concepts"], list):
            raise ValueError(
                "important_concepts must be a list."
            )

        print("Summary generated successfully.")

        return {
            "summary": str(parsed["summary"]),
            "key_points": [
                str(point)
                for point in parsed["key_points"]
            ],
            "important_concepts": [
                str(concept)
                for concept in parsed["important_concepts"]
            ],
            "takeaway": str(parsed["takeaway"]),
        }

    except json.JSONDecodeError as error:

        print("\nJSON ERROR:")
        print(repr(error))

        raise ValueError(
            "Gemini returned an invalid JSON response."
        ) from error

    except Exception as error:

        print("\nGEMINI ERROR:")
        print(repr(error))

        raise ValueError(
            f"Unable to generate summary: {str(error)}"
        ) from error


# ============================================================
# HOME ROUTE
# ============================================================

@app.get("/")
def home():

    return {
        "message": "YouTube Video Summarizer API is running"
    }


# ============================================================
# SUMMARIZE ROUTE
# ============================================================

@app.post(
    "/summarize",
    response_model=SummaryResponse
)
def summarize_video(
    request: SummarizeRequest
):

    try:

        print("\n" + "=" * 60)
        print("NEW SUMMARIZATION REQUEST")
        print("=" * 60)

        print("YouTube URL:")
        print(request.youtube_url)

        # ----------------------------------------------------
        # Step 1: Extract video ID
        # ----------------------------------------------------

        video_id = extract_video_id(
            request.youtube_url
        )

        print("\nVideo ID:")
        print(video_id)

        # ----------------------------------------------------
        # Step 2: Get transcript
        # ----------------------------------------------------

        transcript = get_transcript(
            video_id
        )

        # ----------------------------------------------------
        # Step 3: Generate summary
        # ----------------------------------------------------

        result = generate_summary(
            transcript
        )

        print("\nRequest completed successfully.")
        print("=" * 60)

        return SummaryResponse(
            **result
        )

    except ValueError as error:

        print("\nVALUE ERROR:")
        print(str(error))

        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error

    except Exception as error:

        print("\nSERVER ERROR:")
        print(repr(error))

        raise HTTPException(
            status_code=500,
            detail=f"Server error: {str(error)}"
        ) from error