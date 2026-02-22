# Tutor

Tutoring agent that leverages voice analysis of a student's confidence on a topic to adjust instruction & enhance the lesson plan over time.

"T-AI"

<img width="630" height="796" alt="image" src="https://github.com/user-attachments/assets/8c7d788c-c0da-445b-80f2-0a9047a4e088" />

### Student UX

<img width="682" height="615" alt="image" src="https://github.com/user-attachments/assets/9b951e34-a50c-46c4-ba6e-8e8cd940057f" />

### Instructor Dashboard

<img width="1073" height="1046" alt="image" src="https://github.com/user-attachments/assets/3767f77a-2156-43c3-badd-9aa55023e76e" />
<img width="1055" height="362" alt="image" src="https://github.com/user-attachments/assets/728808ce-7d52-41e1-9e79-55001731ea92" />


## Background
Attended a [Hackathon](https://luma.com/nychack?tk=lwTlNJ) in NYC in Feb 2024 at Datadog's office. The theme was "self-improving agents", there were a handful of corporate sponsors. 

Submitted something to the competition on [Devpost](https://devpost.com/software/tutor-woiv76).

## Inspiration
There are many other dimensions to learning besides simply answering questions correctly. Confidence vs uncertainty is a major one, but there are other elements of _how_ a student answers a question that meaningfully inform the tutor's approach. This dynamic is especially apparent when learning via the [Feynman Technique](https://fs.blog/feynman-technique/), where a student essentially tries to progressively teach a concept to a 12-year-old. 

How can the tutor of tomorrow use technology to get more signal into their students' progress through a lesson?

## What it does
An AI tutoring agent prompts the student with a question about a STEM topic. The student types their response in text (requiring concision and clarity of understanding) while speaking through their thinking out loud (evaluating their confidence and natural chain of thinking). 

The correctness of the student's answer is evaluated by a reasoning LLM looking at the text of the answer. The confidence of the student's answer is measured by an ELM (Ensemble Listening Model) that considers up to 26 elements of the student's voice. Features like language, prosody, timing, and emotion all contribute to a score that the agent can use to adjust its tutoring pattern.

The supervising human instructor can consider these 2 dimensions of learning when reviewing a student's progress. The more interaction with the tutoring agent, the more aggregate confidence there is in the student's level of understanding.

## How I built it
- FastAPI (Python) backend
- Next.js frontend
- SQLite (aiosqlite) DB
- Modulate Velma (voice analysis)
- Google Gemini API -- gemini-2.5-flash (reasoning/inference)
- Lightdash (analytics)

## Challenges
Latency, simplicity of UX

## Accomplishments
Novelty? 

## Learning
Having a clear vision for the medium and integration with tools helps shape process.

## What's next for Tutor
Deploy, expand knowledge areas, add support for instructor-level input
