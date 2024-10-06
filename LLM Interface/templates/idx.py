<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Talk to AI</title>
    <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://unpkg.com/wavesurfer.js"></script>
    <style>
        body { padding: 20px; }
        .button-group { margin-top: 20px; }
        .recording-indicator {
            height: 20px;
            width: 20px;
            background-color: #bbb;
            border-radius: 50%;
            display: inline-block;
            opacity: 0;
            transition: opacity 0.3s;
        }
        .recording { opacity: 1; background-color: red; }
        #waveform {
            width: 100%;
            height: 100px;
            margin-top: 20px;
            background-color: #f8f9fa;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div id="receivedTitle" style="display: none;"></div>
        <input type="text" id="titleInput" class="form-control mt-3" placeholder="Enter the title">
        <button id="submitTitleBtn" onclick="submitTitle()" class="btn btn-primary mt-3">Submit Title</button>
        <div class="text-center button-group">
            <button id="clearHistoryBtn" onclick="clearHistory()" class="btn btn-danger">Create New Conversation</button>
            <button id="startRecordingBtn" onclick="startRecording()" class="btn btn-primary">Start Recording</button>
            <button id="stopRecordingBtn" onclick="stopRecording()" class="btn btn-secondary" disabled>Stop Recording</button>
            <span class="recording-indicator"></span>
        </div>
        <div id="waveform"></div>
        <audio id="responseAudio" controls class="mt-3" style="width: 100%;"></audio>
        <textarea id="conversationText" rows="10" class="form-control mt-3"></textarea>
        <input type="text" id="questionInput" class="form-control mt-3" placeholder="Type your question here">
        <button id="submitQuestionBtn" onclick="submitQuestion()" class="btn btn-primary mt-3">Submit Question</button>
        <div id="feedbackButtonsContainer"></div>
    </div>
    <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.5.2/dist/umd/popper.min.js"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
    <script>

        let mediaRecorder;
        let audioChunks = [];
        let wavesurfer = WaveSurfer.create({
            container: '#waveform',
            waveColor: 'blue',
            progressColor: '#b8c2c8'
        });

        function startRecording() {
            navigator.mediaDevices.getUserMedia({ audio: true })
                .then(stream => {
                    let options = { mimeType: 'audio/webm' };
                    mediaRecorder = new MediaRecorder(stream, options);
                    mediaRecorder.start();
                    document.querySelector('.recording-indicator').classList.add('recording');
                    document.getElementById('startRecordingBtn').disabled = true;
                    document.getElementById('stopRecordingBtn').disabled = false;

                    mediaRecorder.addEventListener("dataavailable", event => {
                        audioChunks.push(event.data);
                    });

                    mediaRecorder.addEventListener("stop", () => {
                        const audioBlob = new Blob(audioChunks, { 'type' : 'audio/webm' });
                        uploadAudio(audioBlob);
                        audioChunks = [];
                        document.querySelector('.recording-indicator').classList.remove('recording');
                    });
                }).catch(e => {
                    console.error('Error accessing the microphone', e);
                    alert('Error accessing the microphone: ' + e.message);
                });
        }

        function stopRecording() {
            mediaRecorder.stop();
            document.getElementById('startRecordingBtn').disabled = false;
            document.getElementById('stopRecordingBtn').disabled = true;
        }

        function uploadAudio(audioBlob) {
        const formData = new FormData();
        formData.append("audio", audioBlob);
        fetch("/process_audio_or_text", { method: "POST", body: formData })
            .then(response => response.json())
            .then(data => {
                const allText = data.all_text;
                document.getElementById('conversationText').value = allText; // Update the text box with all_text
                if (data.audio_url) {
                    // If audio URL is available, trigger audio loading
                    loadAudio(data.audio_url);
                }
                if (data.feedback_buttons) {
                    document.getElementById('feedbackButtonsContainer').innerHTML = data.feedback_buttons;
                }
            }).catch(e => {
                console.error('Error processing audio', e);
                alert('Error processing audio: ' + e.message);
            });
    }

        function loadAudio(audioUrl) {
            document.getElementById('responseAudio').src = audioUrl;
            wavesurfer.load(audioUrl);
            wavesurfer.on('ready', function () {
                wavesurfer.play();
            });
        }

        function clearHistory() {
            fetch("/clear_history")
                .then(response => response.json())
                .then(data => console.log(data.message))
                .catch(error => {
                    console.error('Error clearing history:', error);
                    alert('Error clearing history: ' + error.message);
                });
        }

        function submitQuestion() {
            const questionInput = document.getElementById('questionInput');
            const question = questionInput.value.trim();
            if (question !== '') {
                // Clear the question input immediately after clicking the button
                questionInput.value = '';

                fetch("/process_audio_or_text", {
                    method: "POST",
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ question: question })
                })
                .then(response => response.json())
                .then(data => {
                    const allText = data.all_text;
                    document.getElementById('conversationText').value = allText; // Update the text box with all_text
                    if (data.audio_url) {
                        // If audio URL is available, trigger audio loading
                        loadAudio(data.audio_url);
                    }
                    if (data.feedback_buttons) {
                        document.getElementById('feedbackButtonsContainer').innerHTML = data.feedback_buttons;
                    }
                }).catch(e => {
                    console.error('Error processing question', e);
                    alert('Error processing question: ' + e.message);
                });
            } else {
                alert('Please enter a question.');
            }
        }

        function sendFeedback(feedback) {
            document.getElementById('feedbackButtons').style.display = 'none'; // Hide feedback buttons
            fetch("/record_feedback", {
                method: "POST",
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ feedback: feedback })
            })
            .then(response => response.json())
            .then(data => console.log(data.message))
            .catch(e => {
                console.error('Error recording feedback:', e);
                alert('Error recording feedback: ' + e.message);
            });
            document.getElementById('feedbackButtonsContainer').innerHTML = ''; // Clear feedback buttons container after feedback is sent
        }

        function submitTitle() {
        const title = document.getElementById('titleInput').value.trim(); // Retrieve the title
        if (title !== '') {
            // Clear the title input immediately after clicking the button
            // document.getElementById('titleInput').value = '';
            // Hide the title input field and submit button
            document.getElementById('titleInput').style.display = 'none';
            document.getElementById('submitTitleBtn').style.display = 'none';

            fetch("/process_title", {
                method: "POST",
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ title: title }) // Send only the title
            })
            .then(response => response.json())
            .then(data => {
                const receivedTitleDiv = document.getElementById('receivedTitle');
                receivedTitleDiv.innerText = `Received Title: ${title}`;
                receivedTitleDiv.style.display = 'block'; // Show the received title div
                console.log(data.message);
                // You can perform additional actions here if needed
            }).catch(e => {
                console.error('Error processing title', e);
                alert('Error processing title: ' + e.message);
            });
        } else {
            alert('Please enter a title.');
        }
    }
    </script>
</body>
</html>
