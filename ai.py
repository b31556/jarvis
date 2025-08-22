import openai
import edge_tts
from io import BytesIO
from pydub import AudioSegment
from pydub.playback import play
import asyncio
import time
import re
import os
import json

import tools

with open(".env") as f:
    for line in f:
        if line.startswith("OPENAI_API_KEY"):
            openaikoen = line.split("=")[1].strip().strip('"')
            break

# Initialize OpenAI client
client = openai.OpenAI(api_key=openaikoen)

with open("prompt.txt") as f:
    prompt = f.read()

if os.path.exists("memory.json"):
    with open("memory.json") as f:
        memory = json.load(f)
else:
    memory = []

if os.path.exists("long_term_memory.json"):
    with open("long_term_memory.json") as f:
        long_term_memory = json.load(f)
else:
    long_term_memory = []


def sanitize(text):
    replacements = {
        r"\bn!\b": "n factorial",
        r"\bn\^2\b": "n squared",
        r"\bn\^3\b": "n cubed",
        r"sqrt\((.*?)\)": r"square root of \1",
        r"log\((.*?)\)": r"logarithm of \1",
        r"\be\b": "Euler's number",
        r"\bpi\b": "pi",
        r"\binf\b": "infinity",
        r">=": " greater than or equal to ",
        r"<=": " less than or equal to ",
        r"!=": " not equal to ",
        r">": " greater than ",
        r"<": " less than ",
        r"\+": " plus ",
        r"-": " minus ",
        r"(?<=\b[A-Za-z]|\d)\s*\*\s*(?=[A-Za-z]\b|\d+\b)": " times ",
        r"/": " divided by ",
    }
    for pattern, repl in replacements.items():
        text = re.sub(pattern, repl, text)

    # Remove markdown-like junk
    text = re.sub(r"[#*_`~|\\.\n]", "", text)

    # Normalize spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


import pyttsx3

def speak(text):
    engine = pyttsx3.init()
    engine.setProperty('rate', 160)
    engine.say(text)
    engine.runAndWait()

# Test it
speak("Jarvis online.")


def execute_tool(name, value):
    # Replace with real action if needed
    tools.use(name, value)


def parse_tools(text):
    # Regex to match <tool name="...">VALUE</tool>
    pattern = r'<tool\s+name=(.*?)\s*>(.*?)<\/tool>'
    
    # Find all tool commands
    for name, value in re.findall(pattern, text):
        execute_tool(name, value.strip())
    
    # Remove all <tool>...</tool> tags from text
    cleaned_text = re.sub(pattern, '', text)
    
    # Normalize spaces
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    return cleaned_text


def call(input):
    global memory, long_term_memory, prompt

    memory.append({"role": "user", "content": input})

    message = memory.copy()

    message.append({"role": "system", "content": prompt})


    # Stream chat completion
    first_chunk = True
    start_time = time.time()
    with client.chat.completions.stream(
        model="gpt-4o-mini",
        messages=message,
        temperature=0.7,
        max_tokens=200
    ) as stream:
        cache = ""
        full_response = ""
        for chunk in stream:
            if chunk.type == "content.delta":
                # Access the 'choices' attribute
                content = chunk.delta
                cache += content
                full_response += content
                if ("." in cache or "\n" in cache) and len(cache) > 4:
                    cache =parse_tools(cache)
                    #print(chunk)
                    cache = sanitize(cache)
                    if content:
                        print(cache, end="", flush=True)
                    if first_chunk:
                        print(f"took {time.time() - start_time:.2f} seconds")
                        first_chunk = False
                    speak(cache)
                    cache = ""
            else:
                pass
        # Print any remaining cache
        if cache:
            cache = sanitize(cache)
            print(cache, end="", flush=True)
            speak(cache)

    if full_response:
        print("📝 Válasz:", full_response)
    memory.append({"role": "assistant", "content": full_response})
    with open("memory.json", "w") as f:
        json.dump(memory, f, indent=4)