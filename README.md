# Food Calorie Tracker
 This is the project created in code carnage by a team of 4 members
 

---

### 1. Solution Approach:

This project addresses Healthcare Problem Statement B: "AI-powered Food Tracker with Nutrition Breakdown." The goal is to automatically detect food items in an image using an AI model and generate nutritional data for each item. The data is stored in a MySQL database, and users can view the results in a beautiful web dashboard.

**How it works:**
- Users upload a photo of their meal.
- The image is passed to a trained YOLOv8 model that identifies food items.
- For each detected item, the application maps it to pre-stored nutritional values.
- Detected foods and their nutritional info are displayed, stored in SQLite.

---

### 2. Implementation Details:

**Frontend:**
- HTML, CSS,JavaScript (for image upload, API calls, and UI updates)

**Backend:**
- Python (Flask Web Framework)
- ResNet50 object detection model from Ultralytics
- SQLite database connection 
- Nutrition info mapping via static JSON

---

### 3. Execution Steps:

#### 📦 Backend Setup:
1. Clone the repository.
2. pip install -r requirements.txt
3. cd backend--(in first terminal)
4. python app.py
#### 🌐 Frontend:
1.cd frontend--(in second terminal)
2. python -m http.server 8000

### 4.Visit Webpage
visit 127.0.0.1:8000 on your browser

### . Expected Output:
- Upload a food image → see real-time detected items.
- Each item shows its name, calories, protein, carbs, and fat.
- All entries are stored in SQLite for history tracking.


