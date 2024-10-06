from flask import Flask, request, jsonify, send_file, render_template, url_for
import openai
import os
from tempfile import NamedTemporaryFile
from datetime import datetime

os.environ["OPENAI_API_KEY"] = 'Put Your Open-AI API Key Here'
#response_file_path = f"/static/{title}/response_audio.mp3"
history_file_path = ""
current_path = os.path.dirname(os.path.abspath(__file__))

title = 'new_folder'
if not os.path.exists(f"static\\{title}"):
    os.makedirs(f"static\\{title}")

## suggested initial question is “What are the top 10 most likely diagnoses and why (be precise)?” ##
## Create a starting differential diagnosis that includes, in descending order, the most likely unifying diagnoses that best explain the patients current presentation. Please list up to ten diagnoses. ##
## Identify the most important next diagnostic steps you would do. ##
## Identify the most important next treatment steps for patient given the current information within the case. ##

app = Flask(__name__)

@app.route('/')
def index():
    """Serve the main page."""
    return render_template('idx.html')


@app.route('/clear_history', methods=['GET'])
def clear_history():
    global history_file_path

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_history_file = f"static\\{title}\\{title}_history_{timestamp}.txt"
    history_file_path = os.path.join(current_path, new_history_file)
    print(f'history file path = {history_file_path}')
    return jsonify({'message': 'History cleared and new file created.'}), 200

@app.route('/process_audio_or_text', methods=['POST'])
def process_audio_or_text():
    client = openai.OpenAI()
    if not os.path.exists(f"static\\{title}"):
        os.makedirs(f"static\\{title}")

    if 'audio' in request.files:
        audio_file = request.files['audio']
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        input_audio_filename = f"{title}_input_audio_{timestamp}.wav"
        input_audio_file_path = os.path.join('static', title, input_audio_filename)

        audio_file.save(input_audio_file_path)
        print("Input audio saved successfully.")

        try:
            text_from_audio = client.audio.transcriptions.create(
                model="whisper-1",
                file=open(input_audio_file_path, "rb"),
            )
            print("successfully convert audio to text..........")
            print(text_from_audio)

        except Exception as e:
            print(e)
            return jsonify({'error': 'Failed to transcribe audio.', 'details': str(e)}), 500

        question_text = text_from_audio.text.strip()
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        question_text = request.json.get('question', '')

    history = ''
    if os.path.exists(history_file_path):
        with open(history_file_path, "r", encoding="utf-8") as f:
            history = f.read()

    all_text = history + "\nHuman: " + question_text + "\nAI: "

    response = client.chat.completions.create(
        model="gpt-4-0125-preview",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."}, #You are a helpful medical knowledge assistant.
            {"role": "user", "content": all_text}
        ]
    )
    print(response)
    gpt_text = response.choices[0].message.content
    print("successfully receive GPT response..........")
    print(gpt_text)

    all_text = all_text + gpt_text
    with open(history_file_path, "w", encoding="utf-8") as f:
        f.write(all_text)

    with NamedTemporaryFile(delete=False, suffix='.mp3') as tmp:
        response_audio = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=gpt_text
        )
        response_audio_file_name = f"{title}_response_{timestamp}.mp3"
        response_audio_file_path = os.path.join(current_path, 'static', title, response_audio_file_name)
        with open(response_audio_file_path, "wb") as audio_file:
            audio_file.write(response_audio.content)

        audio_url = url_for('static', filename=f"{title}/{response_audio_file_name}", _external=True)

        # Generate feedback buttons HTML
        feedback_buttons_html = """
            <div class="text-center button-group" id="feedbackButtons">
                <button class="btn btn-success" onclick="sendFeedback('useful')">Useful</button>
                <button class="btn btn-danger" onclick="sendFeedback('not_useful')">Not Useful</button>
            </div>
            """

        return jsonify({
            #'input_audio_url': url_for('static', filename=input_audio_filename, _external=True),
            #'title': title,
            'input_text': question_text,
            'audio_url': audio_url,
            'all_text': all_text,
            'feedback_buttons': feedback_buttons_html
        })

@app.route('/record_feedback', methods=['POST'])
def record_feedback():
    feedback = request.json.get('feedback')

    # Append feedback to history file
    with open(history_file_path, "a", encoding="utf-8") as f:
        if feedback == 'useful':
            f.write("\nUser Feedback: Useful\n")
        else:
            f.write("\nUser Feedback: Not Useful\n")

    # Here you can handle the feedback as per your requirements, such as logging it or performing any actions
    return jsonify({'message': f'Feedback recorded: {feedback}'}), 200

@app.route('/process_title', methods=['POST'])
def process_title():
    global title
    # Retrieve the title from the request
    received_title = request.json.get('title', 'default_title')

    title = received_title

    # Do something with the title if needed
    print(f"Received title: {title}")

    return jsonify({'message': f'Title received: {title}'}), 200

if __name__ == '__main__':
    app.run(debug=True)
