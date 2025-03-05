# import secrets
# print(secrets.token_hex(32))  # Generates a 64-character secure key
# # b163e67f2e8d724e71225af52baffce11557383f77c8bf3bde1f14384d59565b



# import requests

# API_KEY = "AIzaSyA7J0UfBZ9AoU-qDr9jEaR_3ZF2xs_jmsc"
# url = "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent"

# headers = {
#     "Authorization": f"Bearer {API_KEY}",
#     "Content-Type": "application/json"
# }

# response = requests.post(url, headers=headers, json={})
# print(response.json())  # Check API response

# import psycopg2

# try:
#     conn = psycopg2.connect("dbname=coco_db user=postgres password=qwerty host=localhost port=5432")
#     print("✅ Database connected successfully!")
# except Exception as e:
#     print("❌ Database connection failed:", e)




# import jwt
# print(jwt.__version__) 



# import jwt
# import passlib.context
# import deep_translator
# import langdetect
# import psycopg2.pool
# import fitz

# print("All imports successful!")
