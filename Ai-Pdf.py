import os
import google.generativeai as genai
import speech_recognition as sr
import pyttsx3
import fitz  # PyMuPDF

# Fetch API key from the environment variable
api_key = os.environ.get("GENERATIVE_AI_API_KEY")

if not api_key:
    raise ValueError("API key not found. Please set the 'GENERATIVE_AI_API_KEY' environment variable.")

# Configure the API key
genai.configure(api_key=api_key)

# Generation configuration for the model
generation_config = {
    "temperature": 1.2,  # Increase for more variety in responses
    "top_p": 0.9,
    "top_k": 50,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

# Initialize the GenerativeModel with your configuration
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

# Start the chat session without an initial history to avoid recalling past interactions
chat_session = model.start_chat(history=[])

# Initialize recognizer for speech recognition
recognizer = sr.Recognizer()

# Adjust recognizer settings
recognizer.energy_threshold = 4000  # Increase energy threshold for better sensitivity
recognizer.dynamic_energy_threshold = True  # Enable dynamic energy thresholding

# Initialize pyttsx3 for text-to-speech (optional, remove if not needed)
engine = pyttsx3.init()
voices = engine.getProperty('voices')

# Set voice to a female voice, if available
for voice in voices:
    if "female" in voice.name.lower() or "woman" in voice.name.lower():
        engine.setProperty('voice', voice.id)
        break

print("Welcome to the AI Assistant! Type 'exit' to quit.")

# Function to extract text from PDF
def extract_text_from_pdf(file_path):
    pdf_document = fitz.open(file_path)  # Open the PDF directly using the file path
    text = ""
    for page_num in range(pdf_document.page_count):
        page = pdf_document.load_page(page_num)
        text += page.get_text()
    return text

# Loop to continuously take queries from the user
while True:
    # Ask the user for input mode
    mode = input("Would you like to 'speak', 'type' your query, or 'upload' a PDF? (type 'exit' to quit): ").strip().lower()

    if mode == "exit":
        print("Exiting the chat. Goodbye!")
        break

    elif mode == "speak":
        print("Listening... Please say your question or command.")
        try:
            # Use the microphone to capture speech
            with sr.Microphone() as source:
                print("Adjusting for ambient noise, please wait...")
                recognizer.adjust_for_ambient_noise(source, duration=1)  # Adjust for ambient noise
                audio_data = recognizer.listen(source, timeout=5)  # Increase listen timeout
                # Convert speech to text
                input_text = recognizer.recognize_google(audio_data)
                print(f"You said: {input_text}")
        except sr.UnknownValueError:
            print("Sorry, I didn't understand what you said. Please try again.")
            continue
        except sr.RequestError:
            print("Speech service is unavailable. Please try typing instead.")
            continue
        except sr.WaitTimeoutError:
            print("Listening timed out while waiting for phrase to start. Please try again.")
            continue

    elif mode == "type":
        # Get typed input
        input_text = input("Enter your question or command: ")

    elif mode == "upload":
        # Get the PDF file path from the user
        pdf_path = input("Please provide the path to the PDF file: ")
        try:
            # Extract text from the provided PDF file path
            pdf_text = extract_text_from_pdf(pdf_path)
            print("PDF extracted successfully.")
        except FileNotFoundError:
            print("File not found. Please check the path and try again.")
            continue

        # Get the question from the user
        input_text = input("Now, enter your question about the PDF: ")

        # Combine the extracted PDF text with the user's question
        full_input_text = f"Here is the text from the PDF:\n\n{pdf_text}\n\nQuestion: {input_text}"

    else:
        print("Invalid option. Please type 'speak', 'type', or 'upload'.")
        continue

    # Send the input text (or combined query with PDF text) to the model and get a response
    response = chat_session.send_message(full_input_text if mode == "upload" else input_text)

    # Print the model's response
    response_text = response.text
    print("AI:", response_text)

    # Save conversation to history
    chat_session.history.append({"role": "user", "parts": [input_text]})
    chat_session.history.append({"role": "model", "parts": [response_text]})
