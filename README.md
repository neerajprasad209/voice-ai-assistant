# 🎙️ Voice AI Assistant

A production-ready Voice AI Assistant built with **Streamlit**, **Sarvam Speech-to-Text**, **Groq LLM**, **Tavily Search**, **ElevenLabs Text-to-Speech**, and **LangChain Message History**.

The assistant accepts voice input, intelligently decides whether internet search is required, generates conversational responses using a Large Language Model, and converts the response into natural human-like speech.

---

# Table of Contents

* Project Overview
* Features
* System Architecture
* Project Workflow
* Tech Stack
* Project Structure
* Installation
* Environment Variables
* Running the Project
* Pipeline Explanation
* LangChain Conversation History
* Search Decision Flow
* API Integrations
* Folder Description
* Future Improvements
* Troubleshooting

---

# Project Overview

This project demonstrates an end-to-end Voice AI pipeline.

Instead of acting as a simple speech-to-text application, the assistant intelligently decides whether a user's question requires live internet information.

For example,

### Example 1

**User**

> Explain Machine Learning.

Since this is general knowledge, the assistant directly asks the LLM without performing web search.

---

### Example 2

**User**

> Who won yesterday's IPL match?

Since the answer depends on recent information, the assistant automatically performs an internet search using Tavily before generating the final response.

---

The complete interaction is voice-based.

```
Voice
   ↓
Speech-to-Text
   ↓
AI Reasoning
   ↓
Voice Response
```

---

# Features

## Voice Input

* Browser microphone recording
* Audio file upload support
* Sarvam Speech-to-Text
* Multi-language transcription support

---

## Intelligent Search Routing

The assistant does **not** search the internet for every question.

A lightweight Groq model first decides whether search is required.

This reduces

* API cost
* latency
* unnecessary web searches

---

## Live Internet Search

Questions requiring current information are answered using

* Tavily Search API

Examples

* News
* Sports
* Current Affairs
* Stock Market
* Weather
* Recent Technology

---

## AI Reasoning

Uses

**Groq Llama-3.3-70B**

to generate conversational responses.

Supports

* contextual conversations
* follow-up questions
* concise answers

---

## LangChain Conversation History

Conversation history is maintained using

* HumanMessage
* AIMessage

This makes the assistant ready for

* Memory
* Agents
* RAG
* Persistent Storage

---

## Human-like Voice

Responses are converted into realistic speech using

ElevenLabs Text-to-Speech.

Only AI responses are synthesized.

User queries are never sent to Text-to-Speech.

---

## Guardrails

Unsafe prompts are blocked before reaching the LLM.

Examples include

* hacking
* malware
* bombs
* fraud
* violent requests

---

# System Architecture

```
                         User

                           │

                 🎤 Voice Recording

                           │

                           ▼

                 Sarvam Speech-to-Text

                           │

                           ▼

                   HumanMessage

                           │

                           ▼

               Chat History Manager

                           │

                           ▼

                     Guardrails

                           │

                           ▼

                Search Decision LLM

             ┌────────────────────────┐
             │                        │
             ▼                        ▼

      Direct LLM              Tavily Search

             │                        │

             └──────────┬─────────────┘

                        ▼

                 AIMessage Response

                        │

          ┌─────────────┴──────────────┐

          ▼                            ▼

   Streamlit UI              ElevenLabs Speech
```

---

# Project Workflow

## Step 1

User records audio.

↓

## Step 2

Sarvam converts speech into text.

↓

## Step 3

Text is stored as a LangChain `HumanMessage`.

↓

## Step 4

Guardrails validate the request.

↓

## Step 5

Search Decision LLM determines whether web search is required.

↓

## Step 6

If required

```
Question

↓

Tavily Search

↓

Search Context

↓

Groq LLM
```

Otherwise

```
Question

↓

Groq LLM
```

↓

## Step 7

Response is stored as an `AIMessage`.

↓

## Step 8

Only the AI response is converted into speech using ElevenLabs.

↓

## Step 9

Conversation is displayed inside Streamlit.

---

# Technology Stack

| Component             | Technology         |
| --------------------- | ------------------ |
| Frontend              | Streamlit          |
| Programming Language  | Python             |
| Speech-to-Text        | Sarvam AI          |
| LLM                   | Groq Llama-3.3-70B |
| Search Engine         | Tavily Search      |
| Text-to-Speech        | ElevenLabs         |
| Conversation History  | LangChain          |
| Environment Variables | python-dotenv      |
| Logging               | Loguru             |
| Exception Handling    | Custom Exception Framework |


# Project Structure

```
voice-ai-assistant/

│

├── app.py

├── requirements.txt

├── README.md

├── .env

│

├── logs/

│   ├── app.log

│   └── error.log

│

├── src/

│   ├── logger.py

│   ├── custom_exception.py

│   ├── chat_history.py

│   ├── speech_to_text.py

│   ├── search.py

│   ├── llm.py

│   ├── tts.py

│   ├── guardrails.py

│   └── utils.py

│

└── assets/
```

---

# Installation

Clone the repository

```bash
git clone <repository-url>

cd voice-ai-assistant
```

Create virtual environment

```bash
python -m venv .venv
```

Activate

Windows

```bash
.venv\Scripts\activate
```

Linux / macOS

```bash
source .venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

# Environment Variables

Create a `.env` file

```env
SARVAM_API_KEY=

GROQ_API_KEY=

TAVILY_API_KEY=

ELEVENLABS_API_KEY=

ELEVENLABS_VOICE_ID=
```

---

# Running the Application

```bash
streamlit run app.py
```

---

# Pipeline Explanation

## Speech-to-Text

Input

```
Audio
```

↓

Output

```
Transcript
```

Technology

Sarvam Speech-to-Text

---

# Logging

The project uses **Loguru** as the centralized logging framework.

Every module imports the same logger instance.

```python
from src.logger import logger
```

The logger automatically records important events such as:

- Application startup
- Session initialization
- Speech transcription
- Guardrail validation
- Search decision
- Tavily search
- LLM generation
- Text-to-Speech synthesis
- Error handling

### Log Levels

| Level | Description |
|--------|-------------|
| DEBUG | Internal debugging information |
| INFO | Normal execution |
| SUCCESS | Successful operation |
| WARNING | Recoverable issue |
| ERROR | Operation failed |
| EXCEPTION | Unexpected exception with traceback |

### Log Files

```
logs/

├── app.log
└── error.log
```

The application automatically rotates log files to prevent unlimited growth.

Current configuration:

- App log rotation: 10 MB
- Error log rotation: 5 MB
- Compression: ZIP
- Retention: 10–30 days


# Exception Handling

The application follows a centralized exception handling strategy.

Every module raises a `VoiceAssistantException` for unexpected failures.

Example:

```python
try:

    ...

except Exception as e:

    logger.exception("Speech transcription failed.")

    raise VoiceAssistantException(e)
```

A `VoiceAssistantException` automatically reports:

- File name
- Function name
- Line number
- Original exception

Example output:

```
VoiceAssistantException

File      : speech_to_text.py

Function  : transcribe_audio

Line      : 198

Error     : Missing SARVAM_API_KEY
```

This ensures that every unexpected failure is easy to debug and trace.



## Conversation History

Every user query becomes

```python
HumanMessage(
    content="..."
)
```

Every assistant response becomes

```python
AIMessage(
    content="..."
)
```

This provides

* conversation memory
* context-aware responses
* future RAG compatibility

---

## Search Decision

Instead of searching every question,

the assistant first asks

```
Does this question require live internet search?
```

Possible outputs

```
SEARCH
```

or

```
NO_SEARCH
```

Benefits

* Lower latency
* Reduced API cost
* Faster responses

---

## Internet Search

If required,

the assistant calls Tavily.

Search results are injected into the system prompt before generating the response.

---

## LLM

Groq Llama-3.3-70B generates the final answer.

The model receives

* previous conversation
* latest user question
* search results (when available)

---

## Text-to-Speech

Only

```python
AIMessage.content
```

is sent to ElevenLabs.

This ensures user prompts are never spoken back.

---

# LangChain Conversation History

Conversation is maintained as

```
Human

↓

AI

↓

Human

↓

AI
```

Example

```
User

Who is Elon Musk?

↓

Assistant

CEO of Tesla

↓

User

Where was he born?
```

Since previous messages are preserved,

the assistant understands

```
Where was he born?
```

without the user repeating

```
Elon Musk
```

---

# Folder Description

## app.py

Main Streamlit application.

Responsible for

* UI
* session state
* orchestration

---

## chat_history.py

Maintains

* HumanMessage
* AIMessage

Acts as the single source of truth for conversations.

---

## llm.py

Responsible for

* Groq integration
* search decision
* response generation
* prompt construction

---

## search.py

Handles

* Tavily Search
* formatting search context

---

## speech_to_text.py

Handles

* Sarvam transcription
* REST API
* Batch API fallback

---

## tts.py

Handles

* ElevenLabs integration
* speech synthesis

---

## guardrails.py

Filters unsafe prompts before the LLM.

---

## utils.py

Provides

* API configuration
* connectivity checks
* environment validation

---

# Future Improvements

* Persistent Chat Memory
* Redis-backed conversation storage
* MongoDB history
* SQLite support
* RAG with Vector Database
* Tool Calling
* AI Agents
* Streaming Responses
* Streaming Text-to-Speech
* Multi-user authentication
* Docker deployment
* Kubernetes deployment
* Cloud hosting
* Avatar integration
* Voice interruption support
* Wake-word detection

---

# Troubleshooting

## Missing API Key

```
Missing GROQ_API_KEY
```

Ensure the `.env` file exists and contains all required API keys.

---

## ElevenLabs Error

```
Unauthorized
```

Verify

* API key
* Voice ID

---

## Sarvam Error

```
Missing SARVAM_API_KEY
```

Confirm the API key is configured correctly.

---

## No Audio Output

Check

* ElevenLabs API key
* Voice ID
* Internet connection

---

## Streamlit Microphone Not Working

Update Streamlit to the latest version or upload an audio file manually.

---

# Future Roadmap

* Long-term conversation memory
* Redis and PostgreSQL persistence
* Semantic search using embeddings
* RAG-based document question answering
* LangGraph integration
* Agentic workflows
* Streaming responses
* Streaming TTS
* Voice avatars
* Real-time voice conversations

---

# Author

**Neeraj Prasad**

AI / ML Engineer

Built as an end-to-end Voice AI Assistant demonstrating modern LLM application architecture using LangChain, Groq, Tavily, Sarvam AI, and ElevenLabs.
