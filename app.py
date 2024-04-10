import json
from flask import Flask, render_template, request, jsonify
import random
from difflib import get_close_matches, SequenceMatcher
from datetime import datetime
from langdetect import detect
from textblob import TextBlob
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import KNeighborsClassifier
import torch
from transformers import BertTokenizer, BertForSequenceClassification

app = Flask(__name__)

# Function to load data from JSON files
def load_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Load data from JSON files
data = load_data('data/data.json')

# Function to check for forbidden words
def check_forbidden_words(input_text):
    forbidden_words = load_data('data/kata.json')
    for word in forbidden_words:
        if word in input_text.lower():
            return True
    return False

# Function to evaluate new answer before adding it to the database
def evaluate_new_answer(new_answer):
    existing_questions = [qa["pertanyaan"].lower() for qa in data["pertanyaan_respon"]]
    input_question = new_answer["pertanyaan"].lower()

    similar_questions = get_close_matches(input_question, existing_questions, cutoff=0.8)
    if similar_questions:
        input_answer = new_answer["respon"].lower()
        for similar_question in similar_questions:
            existing_answer = next((qa["respon"].lower() for qa in data["pertanyaan_respon"] if qa["pertanyaan"].lower() == similar_question), None)
            if existing_answer is not None:
                similarity_ratio = similar_ratio(input_answer, existing_answer)
                if similarity_ratio > 0.8:
                    return False
    return True

# Function to calculate similarity ratio between two strings
def similar_ratio(str1, str2):
    return SequenceMatcher(None, str1, str2).ratio()

# Function to process user input
def process_input(input_text):
    if check_forbidden_words(input_text):
        return "Maaf, input mengandung kata terlarang."

    try:
        language = detect(input_text)
        if language != 'id':
            return "Maaf, AI hanya dapat memproses teks dalam bahasa Indonesia."
    except Exception as e:
        print(f"Error detecting language: {e}")
        return "Maaf, terjadi kesalahan dalam mendeteksi bahasa."

    if any(word in input_text.lower() for word in ['waktu', 'jam', 'hari']):
        return get_current_time_and_date()

    return generate_response_combining(input_text)  # Process input using the new function

# Function to generate response by combining words or phrases from database
def generate_response_combining(input_text):
    # Analyze user input to identify relevant keywords
    keywords = analyze_input(input_text)
    
    # Retrieve relevant data from database based on keywords
    relevant_data = retrieve_relevant_data(keywords)
    
    # Combine words or phrases to generate new sentence
    new_sentence = combine_data(relevant_data)
    
    return new_sentence

# Function to analyze user input and identify relevant keywords
def analyze_input(input_text):
    keywords = input_text.lower().split()
    return keywords

# Function to retrieve relevant data from database based on keywords
def retrieve_relevant_data(keywords):
    relevant_data = []
    for keyword in keywords:
        for qa_pair in data["pertanyaan_respon"]:
            if keyword in qa_pair["pertanyaan"].lower():
                relevant_data.append(qa_pair["respon"])
    return relevant_data

# Function to combine data to generate new sentence
def combine_data(data):
    new_sentence = " ".join(data)
    return new_sentence

# Function to get current time and date
def get_current_time_and_date():
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    current_date = now.strftime("%Y-%m-%d")
    return f"Waktu saat ini adalah {current_time}, tanggal {current_date}."

# Function to add new data
def add_new_data(input_text, input_answer):
    try:
        new_data = {"pertanyaan": input_text, "respon": input_answer, "topik": "topik_baru"}
        with open('data/data.json', 'r+', encoding='utf-8') as f:
            existing_data = json.load(f)
            existing_data['pertanyaan_respon'].append(new_data)
            f.seek(0)
            json.dump(existing_data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

# Function to process user input and update database if needed
def process_and_update_database(input_text, input_answer):
    output_text = process_input(input_text)
    if output_text == "Maaf, AI tidak dapat memahami pertanyaan Anda.":
        if add_new_data(input_text, input_answer):
            return "Terima kasih, data baru telah ditambahkan ke database."
        else:
            return "Maaf, terjadi kesalahan saat menambahkan data baru ke database."
    return output_text

# Function to get AI response
def get_response(input_text):
    pertanyaan_respon = data.get("pertanyaan_respon", [])
    matched_responses = []

    for qa_pair in pertanyaan_respon:
        pertanyaan = qa_pair.get("pertanyaan", "")
        if pertanyaan.lower() in input_text.lower():
            matched_responses.append(qa_pair.get("respon", ""))

    if matched_responses:
        return random.choice(matched_responses)

    similar_questions = []
    for qa_pair in pertanyaan_respon:
        pertanyaan = qa_pair.get("pertanyaan", "")
        if get_close_matches(pertanyaan.lower(), [input_text.lower()], cutoff=0.8):
            similar_questions.append(pertanyaan)

    if similar_questions:
        return f"Maaf, AI tidak dapat memahami pertanyaan Anda. Apakah Anda maksud: {', '.join(similar_questions)}?"

    return "Maaf, AI tidak dapat memahami pertanyaan Anda."

# Function to group user questions based on topics
def group_questions_by_topic():
    topics = {}
    for qa_pair in data["pertanyaan_respon"]:
        question = qa_pair["pertanyaan"]
        topic = detect_topic(question)
        if topic in topics:
            topics[topic].append(question)
        else:
            topics[topic] = [question]
    return topics

data = load_data('data/data.json')
questions = [qa_pair["pertanyaan"] for qa_pair in data["pertanyaan_respon"]]
topics = [qa_pair["topik"] for qa_pair in data["pertanyaan_respon"]]

vectorizer = TfidfVectorizer()
question_vectors = vectorizer.fit_transform(questions)

knn_classifier = KNeighborsClassifier(n_neighbors=5)
knn_classifier.fit(question_vectors, topics)

def detect_topic(question):
    question_vector = vectorizer.transform([question])
    predicted_topic = knn_classifier.predict(question_vector)[0]
    return predicted_topic

def analyze_sentiment(input_text):
    blob = TextBlob(input_text)
    sentiment_score = blob.sentiment.polarity
    if sentiment_score > 0:
        return "positive"
    elif sentiment_score < 0:
        return "negative"
    else:
        return "neutral"

def generate_response_ml(input_text):
    questions = [qa_pair["pertanyaan"] for qa_pair in data["pertanyaan_respon"]]
    responses = [qa_pair["respon"] for qa_pair in data["pertanyaan_respon"]]
    vectorizer = TfidfVectorizer()
    question_vectors = vectorizer.fit_transform(questions)
    
    input_vector = vectorizer.transform([input_text])
    
    similarities = cosine_similarity(input_vector, question_vectors)
    
    most_similar_index = similarities.argmax()
    
    return responses[most_similar_index]

tokenizer = BertTokenizer.from_pretrained('bert-base-multilingual-cased')
model = BertForSequenceClassification.from_pretrained('bert-base-multilingual-cased', num_labels=2)
model.eval()

def analyze_sentiment_bert(input_text):
    inputs = preprocess_text(input_text)
    with torch.no_grad():
        outputs = model(**inputs)
    logits = outputs.logits
    probabilities = torch.softmax(logits, dim=1).tolist()[0]
    positive_probability = probabilities[1]
    return positive_probability

def process_input(input_text):
    if check_forbidden_words(input_text):
        return "Maaf, input mengandung kata terlarang."

    try:
        language = detect(input_text)
        if language != 'id':
            return "Maaf, AI hanya dapat memproses teks dalam bahasa Indonesia."
    except Exception as e:
        print(f"Error detecting language: {e}")
        return "Maaf, terjadi kesalahan dalam mendeteksi bahasa."

    if any(word in input_text.lower() for word in ['waktu', 'jam', 'hari']):
        return get_current_time_and_date()

    # Sentiment analysis using BERT
    sentiment_score = analyze_sentiment_bert(input_text)
    if sentiment_score > 0.5:
        return "Terima kasih atas umpan balik positif Anda!"
    
    # Additional processing based on sentiment
    topic_questions = group_questions_by_topic()
    sentiment = analyze_sentiment(input_text)
    if sentiment == "positive":
        if update_database_with_feedback(input_text, sentiment):
            return "Terima kasih atas umpan balik positif Anda!"
        else:
            return "Maaf, terjadi kesalahan saat memproses umpan balik Anda."
    elif sentiment == "negative":
        if update_database_with_feedback(input_text, sentiment):
            return "Maaf atas pengalaman yang tidak memuaskan. Bagaimana kami bisa membantu?"
        else:
            return "Maaf, terjadi kesalahan saat memproses umpan balik Anda."
    
    response_ml = generate_response_ml(input_text)
    if update_database_with_feedback(input_text, sentiment):
        return response_ml
    else:
        return "Maaf, terjadi kesalahan saat memproses umpan balik Anda."


def update_database_with_feedback(input_text, sentiment):
    try:
        with open('data/feedback.json', 'r+', encoding='utf-8') as f:
            feedback_data = json.load(f)
            feedback_data.append({"pertanyaan": input_text, "sentimen": sentiment})
            f.seek(0)
            json.dump(feedback_data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    try:
        input_text = request.form['input_text']
        output_text = process_and_update_database(input_text, "")
    except KeyError:
        error_message = "Maaf, terjadi kesalahan dalam pemrosesan input. Mohon coba lagi."
        return render_template('index.html', error_message=error_message)

    return render_template('index.html', input_text=input_text, output_text=output_text)

@app.route('/api/process_input', methods=['POST'])
def process_input_api():
    try:
        input_text = request.json['input_text']
        output_text = process_and_update_database(input_text, "")
        return jsonify({'output_text': output_text})
    except KeyError:
        return jsonify({'error_message': "Maaf, terjadi kesalahan dalam pemrosesan input. Mohon coba lagi."})

if __name__ == '__main__':
    app.run(debug=True)
