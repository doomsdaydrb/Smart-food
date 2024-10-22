import cv2
from pyzbar.pyzbar import decode
from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)

# Create the database if not exists
def create_database():
    conn = sqlite3.connect('food_storage.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            product_code TEXT,
            product_name TEXT,
            quantity INTEGER,
            date_of_entry TEXT,
            expiry_date TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Route to scan the QR code / Barcode
@app.route('/scan', methods=['GET'])
def scan_code():
    # Open the camera to capture an image
    cap = cv2.VideoCapture(0)
    product_code = None

    while True:
        ret, frame = cap.read()  # Capture the frame from the webcam
        if not ret:
            break

        # Use pyzbar to decode the QR codes / Barcodes in the frame
        decoded_objects = decode(frame)

        for obj in decoded_objects:
            product_code = obj.data.decode('utf-8')  # Decode the product code
            print(f"Scanned Product Code: {product_code}")

            # Once a product code is found, break the loop and stop scanning
            cap.release()
            cv2.destroyAllWindows()
            return jsonify({"product_code": product_code})

        # Show the video feed (useful for testing/debugging)
        cv2.imshow('Barcode/QR Code Scanner', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to quit
            break

    cap.release()
    cv2.destroyAllWindows()
    return jsonify({"product_code": None})

# Home page route
@app.route('/')
def index():
    # Check for expiring products (within the next 7 days)
    conn = sqlite3.connect('food_storage.db')
    cursor = conn.cursor()

    today = datetime.now().strftime('%Y-%m-%d')
    expiry_threshold = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')

    cursor.execute('''
        SELECT product_name, expiry_date FROM products
        WHERE expiry_date BETWEEN ? AND ?
    ''', (today, expiry_threshold))

    expiring_soon = cursor.fetchall()
    conn.close()

    return render_template('index.html', expiring_soon=expiring_soon)

# Add Product route
@app.route('/add', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        product_code = request.form['product_code']
        product_name = request.form['product_name']
        quantity = request.form['quantity']
        expiry_date = request.form['expiry_date']
        date_of_entry = datetime.now().strftime('%Y-%m-%d')

        conn = sqlite3.connect('food_storage.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO products (product_code, product_name, quantity, date_of_entry, expiry_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (product_code, product_name, quantity, date_of_entry, expiry_date))
        conn.commit()
        conn.close()

        return redirect(url_for('index'))
    
    return render_template('add_product.html')

# Inventory route
@app.route('/inventory')
def view_inventory():
    conn = sqlite3.connect('food_storage.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()

    return render_template('inventory.html', products=products)

# Run the Flask app
if __name__ == '__main__':
    create_database()
    app.run(debug=True)
