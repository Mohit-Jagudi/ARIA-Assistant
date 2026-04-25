from google import genai

API_KEY = "AIzaSyBmWZrOJdBFndWQvKH9eai9BzIfGP2aTX4"

client = genai.Client(api_key=API_KEY)

response = client.models.generate_content(
    model="gemini-1.5-flash",
    contents="Say: ARIA is online"
)

print(response.text)