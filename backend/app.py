from flask import Flask, request, jsonify
from rapidfuzz import process
from flask_cors import CORS
import wikipedia
from matplotlib.pylab import f
import torch
import torch.nn as nn
import torchvision
import torchvision.transforms as transforms
from PIL import Image
import pandas as pd
import os
import io
import base64
import re
import sqlite3
from datetime import datetime
import json
import hashlib

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})  # Allow all origins for simplicity

# Configuration
MODEL_PATH = "food101_model.pth"
NUTRITION_CSV_PATH = "ABBREV.xlsx"
DB_PATH = "food_logs.db"

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')
    # Food logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS food_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            userId INTEGER,
            timestamp TEXT,
            foodName TEXT,
            confidence REAL,
            nutrition TEXT,
            FOREIGN KEY (userId) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

# Global model and data
model = None
idx_to_class = None
nutrition_df = None

def load_model(model_path):
    try:
        model = torchvision.models.resnet50()
        model.fc = nn.Sequential(nn.Dropout(0.4), nn.Linear(model.fc.in_features, 101))
        checkpoint = torch.load(model_path, map_location=torch.device('cpu'))
        if 'model_state_dict' in checkpoint:
            model.load_state_dict(checkpoint['model_state_dict'])
        else:
            model.load_state_dict(checkpoint)
        idx_to_class = checkpoint.get('idx_to_class', {
            i: cls for i, cls in enumerate([
                'apple_pie', 'baby_back_ribs', 'baklava', 'beef_carpaccio', 'beef_tartare',
                'beet_salad', 'beignets', 'bibimbap', 'bread_pudding', 'breakfast_burrito',
                'bruschetta', 'caesar_salad', 'cannoli', 'caprese_salad', 'carrot_cake',
                'ceviche', 'cheesecake', 'cheese_plate', 'chicken_curry', 'chicken_quesadilla',
                'chicken_wings', 'chocolate_cake', 'chocolate_mousse', 'churros', 'clam_chowder',
                'club_sandwich', 'crab_cakes', 'creme_brulee', 'croque_madame', 'cup_cakes',
                'deviled_eggs', 'donuts', 'dumplings', 'edamame', 'eggs_benedict',
                'escargots', 'falafel', 'filet_mignon', 'fish_and_chips', 'foie_gras',
                'french_fries', 'french_onion_soup', 'french_toast', 'fried_calamari', 'fried_rice',
                'frozen_yogurt', 'garlic_bread', 'gnocchi', 'greek_salad', 'grilled_cheese_sandwich',
                'grilled_salmon', 'guacamole', 'gyoza', 'hamburger', 'hot_and_sour_soup',
                'hot_dog', 'huevos_rancheros', 'hummus', 'ice_cream', 'lasagna',
                'lobster_bisque', 'lobster_roll_sandwich', 'macaroni_and_cheese', 'macarons', 'miso_soup',
                'mussels', 'nachos', 'omelette', 'onion_rings', 'oysters',
                'pad_thai', 'paella', 'pancakes', 'panna_cotta', 'peking_duck',
                'pho', 'pizza', 'pork_chop', 'poutine', 'prime_rib',
                'pulled_pork_sandwich', 'ramen', 'ravioli', 'red_velvet_cake', 'risotto',
                'samosa', 'sashimi', 'scallops', 'seaweed_salad', 'shrimp_and_grits',
                'spaghetti_bolognese', 'spaghetti_carbonara', 'spring_rolls', 'steak', 'strawberry_shortcake',
                'sushi', 'tacos', 'takoyaki', 'tiramisu', 'tuna_tartare', 'waffles'
            ])
        })
        model.eval()
        return model, idx_to_class
    except Exception as e:
        print(f"❌ Model Load Error: {e}")
        return None, None

def load_nutrition_data(csv_path=None):
    try:
        if csv_path and os.path.isfile(csv_path):
            return pd.read_excel(csv_path)
        print(f"⚠ Using mock nutrition data.")
        return pd.DataFrame([
            {'label': 'pizza', 'weight': 100.0, 'calories': 266.0, 'protein': 11.0, 'carbohydrates': 33.0, 'fats': 10.0, 'fiber': 2.0, 'sugars': 3.0, 'sodium': 600.0},
            {'label': 'hamburger', 'weight': 100.0, 'calories': 295.0, 'protein': 17.0, 'carbohydrates': 29.0, 'fats': 14.0, 'fiber': 1.0, 'sugars': 5.0, 'sodium': 480.0},
            {'label': 'apple_pie', 'weight': 100.0, 'calories': 237.0, 'protein': 2.0, 'carbohydrates': 34.0, 'fats': 11.0, 'fiber': 2.0, 'sugars': 15.0, 'sodium': 320.0}
        ])
    except Exception as e:
        print(f"❌ Nutrition CSV Load Error: {e}")
        return pd.DataFrame([])

def preprocess_image(image_data):
    try:
        transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        image = Image.open(io.BytesIO(image_data)).convert('RGB')
        image_tensor = transform(image).unsqueeze(0)
        return image_tensor
    except Exception as e:
        print(f"❌ Image Processing Error: {e}")
        return None

def predict_food(model, image_tensor, idx_to_class):
    if image_tensor is None:
        return None, None
    try:
        with torch.no_grad():
            outputs = model(image_tensor)
            probabilities = torch.nn.functional.softmax(outputs, dim=1)
            top_prob, top_idx = torch.max(probabilities, 1)
            return idx_to_class[top_idx.item()], top_prob.item()
    except Exception as e:
        print(f"❌ Prediction Error: {e}")
        return None, None

def find_best_match(food_name, choices):
    match = process.extractOne(food_name, choices)
    return match[0] if match else None

def get_wikipedia_summary(food_name):
    try:
        summary = wikipedia.summary(food_name, sentences=2)
        return summary
    except wikipedia.exceptions.DisambiguationError as e:
        return f"Multiple results found for '{food_name}', please be more specific."
    except wikipedia.exceptions.PageError:
        return f"No summary found for '{food_name}'."
    except Exception as e:
        return "An error occurred while fetching Wikipedia data."


def calculate_nutrition(food_name, weight, nutrition_df):
    try:
        food_name_cleaned = food_name.lower().replace('_', ' ')
        choices = nutrition_df['Shrt_Desc'].dropna().str.lower().unique().tolist()
        best_match = find_best_match(food_name_cleaned, choices)

        if not best_match:
            print(f"⚠ No nutrition match for: {food_name}")
            return {'calories': 200.0, 'protein': 10.0, 'carbs': 25.0, 'fat': 8.0}

        food_data = nutrition_df[nutrition_df['Shrt_Desc'].str.lower() == best_match]
        base = food_data.iloc[0]
        scale = weight / 100.0

        return {
            'calories': round(base['Energ_Kcal'] * scale, 1),
            'protein': round(base['Protein_(g)'] * scale, 1),
            'carbs': round(base['Carbohydrt_(g)'] * scale, 1),
            'fat': round(base['Lipid_Tot_(g)'] * scale, 1)
        }
    except Exception as e:
        print(f"❌ Nutrition Calculation Error: {e}")
        return {'calories': 200.0, 'protein': 10.0, 'carbs': 25.0, 'fat': 8.0}


        


# User Registration
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = hashlib.sha256(data.get('password', '').encode()).hexdigest()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        user_id = cursor.lastrowid
        return jsonify({'message': 'User registered', 'userId': user_id}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username already exists'}), 400
    finally:
        conn.close()

# User Login
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = hashlib.sha256(data.get('password', '').encode()).hexdigest()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE username = ? AND password = ?', (username, password))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return jsonify({'message': 'Login successful', 'userId': user[0]})
    return jsonify({'error': 'Invalid credentials'}), 401

# Recognize Food
@app.route('/api/recognize', methods=['POST'])
def recognize_food():
    global model, idx_to_class, nutrition_df
    if model is None or idx_to_class is None:
        model, idx_to_class = load_model(MODEL_PATH)
    if nutrition_df is None:
        nutrition_df = load_nutrition_data(NUTRITION_CSV_PATH)
    if model is None or idx_to_class is None:
        return jsonify({'error': 'Model initialization failed'}), 500

    user_id = request.form.get('userId')
    if not user_id:
        return jsonify({'error': 'User ID required'}), 401

    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    image_file = request.files['image']
    image_data = image_file.read()
    image_tensor = preprocess_image(image_data)
    if image_tensor is None:
        return jsonify({'error': 'Image processing failed'}), 500

    predicted_food, confidence = predict_food(model, image_tensor, idx_to_class)
    if predicted_food is None:
        return jsonify({'error': 'Food prediction failed'}), 500

    weight = float(request.form.get('weight', 100.0))
    nutrition = calculate_nutrition(predicted_food, weight, nutrition_df)
    
    # ✅ Get Wikipedia Summary
    summary = get_wikipedia_summary(predicted_food)

    # ✅ Log prediction in DB
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO food_logs (userId, timestamp, foodName, confidence, nutrition)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, datetime.utcnow().isoformat(), predicted_food, confidence, json.dumps(nutrition)))
    conn.commit()
    conn.close()

    return jsonify({
        'foodName': predicted_food,
        'confidence': confidence,
        'nutrition': nutrition,
        'summary': summary  # ✅ Include summary in response
    })

# Get Food Logs
@app.route('/api/food-logs', methods=['GET'])
def get_food_logs():
    user_id = request.args.get('userId')
    if not user_id:
        return jsonify({'error': 'User ID required'}), 401
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT timestamp, foodName, confidence, nutrition FROM food_logs WHERE userId = ? ORDER BY timestamp DESC LIMIT 15', (user_id,))
    logs = cursor.fetchall()
    conn.close()
    
    formatted_logs = [
        {'timestamp': log[0], 'foodName': log[1], 'confidence': log[2], 'nutrition': json.loads(log[3])}
        for log in logs
    ]
    return jsonify(formatted_logs)

if __name__ == '__main__':
    init_db()
    model, idx_to_class = load_model(MODEL_PATH)
    nutrition_df = load_nutrition_data(NUTRITION_CSV_PATH)
    app.run(debug=True, host='0.0.0.0', port=5000)