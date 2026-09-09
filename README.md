# YouTube Video Summarizer

A simple beginner-friendly project that takes a YouTube video URL, extracts the transcript, sends it to Google Gemini using LangChain, and returns a short summary, key points, important concepts, and a final takeaway.

## What the project does

The app works like this:

1. The user enters a YouTube link.
2. The backend extracts the video ID.
3. It fetches the transcript from YouTube.
4. The transcript is sent to Gemini through LangChain.
5. Gemini returns a structured summary.
6. The result is shown in the browser without refreshing the page.

## Technologies used

- Python
- FastAPI
- LangChain
- Google Gemini API
- YouTube Transcript API
- HTML, CSS, JavaScript
- python-dotenv

## Project structure

```text
youtube-summarizer/
├── main.py
├── .env
├── .gitignore
├── requirements.txt
├── README.md
└── frontend/
    ├── index.html
    ├── style.css
    └── script.js
```

## Install dependencies

Create a virtual environment if you want, then install the packages:

```bash
pip install -r requirements.txt
```

## Create the .env file

Create a `.env` file in the project root with your Google API key:

```env
GOOGLE_API_KEY=your_api_key_here
```

Important:
- Do not hardcode the API key in the code.
- Do not commit the `.env` file to Git.

## Run the FastAPI server

From the project folder, run:

```bash
uvicorn main:app --reload
```

The app will run at:

```text
http://127.0.0.1:8000
```

## How to use the app

1. Open the frontend in a browser.
2. Paste a valid YouTube URL.
3. Click the "Summarize" button.
4. Wait for the result.
5. Read the summary, key points, concepts, and takeaway.

Example URL formats supported:

```text
https://www.youtube.com/watch?v=VIDEO_ID
https://youtu.be/VIDEO_ID
```

## How the LangChain pipeline works

The workflow is simple:

```text
YouTube URL
   ↓
FastAPI
   ↓
Extract video ID
   ↓
Get transcript
   ↓
Create prompt
   ↓
ChatGoogleGenerativeAI
   ↓
Return summary as JSON
```

### Important parts

- `ChatPromptTemplate` creates the instruction text for Gemini.
- `ChatGoogleGenerativeAI` is the model that generates the answer.
- `prompt | model` creates a basic LangChain chain.
- The transcript is passed into the prompt as a variable.

## Basic interview explanation

### Why FastAPI?
FastAPI is fast, simple, and beginner-friendly. It helps create API endpoints quickly and handle request/response validation cleanly.

### Why LangChain?
LangChain makes it easy to work with LLMs using prompt templates and model chains. It keeps the code cleaner and easier to understand.

### Why Gemini?
Gemini is a powerful generative AI model. It can understand long text like a YouTube transcript and generate a summary.

### How is the transcript obtained?
The project uses `youtube-transcript-api` to fetch the subtitle text for the given video ID.

### How is the prompt sent to Gemini?
The transcript is inserted into a `ChatPromptTemplate`, then the template is sent to the Gemini model through a LangChain chain.

### What does `ChatPromptTemplate` do?
It creates a prompt with placeholders like `{transcript}` and makes it easier to reuse and manage instructions.

### What does `chain = prompt | model` mean?
This is a basic LangChain pipeline. The prompt is passed into the model, and the model generates a result.

### How does the frontend communicate with FastAPI?
The frontend uses JavaScript `fetch()` to send a POST request to `http://127.0.0.1:8000/summarize`.

### What happens when the user clicks "Summarize"?
- The URL is read from the input box.
- It is sent to the backend.
- The backend extracts the video ID.
- The transcript is fetched.
- The transcript is sent to Gemini.
- The result is returned to the browser and rendered on the page.

## Future improvements

- Add support for videos without transcripts.
- Show loading animations.
- Improve UI styling.
- Add error messages for invalid URLs more clearly.
- Add support for multiple languages.
- Save summary history on the frontend.

## Run instructions summary

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Then open the frontend page and paste a YouTube URL.
