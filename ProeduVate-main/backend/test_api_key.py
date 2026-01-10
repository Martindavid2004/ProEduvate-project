import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

print(f"API Key found: {GOOGLE_API_KEY[:20]}..." if GOOGLE_API_KEY else "No API key found")

if GOOGLE_API_KEY:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        
        # First, list all available models
        print("\n=== Available Models ===")
        try:
            for model in genai.list_models():
                if 'generateContent' in model.supported_generation_methods:
                    print(f"✓ {model.name}")
        except Exception as e:
            print(f"Error listing models: {e}")
        
        print("\n=== Testing Models ===")
        # Try different model names
        models_to_test = [
            'models/gemini-2.5-flash',
            'models/gemini-2.5-pro',
            'models/gemini-flash-latest',
            'models/gemini-pro-latest',
        ]
        
        for model_name in models_to_test:
            try:
                print(f"\nTesting model: {model_name}")
                model = genai.GenerativeModel(model_name)
                response = model.generate_content("Say 'Hello, I am working!'")
                print(f"✓ {model_name} works!")
                print(f"Response: {response.text}")
                break
            except Exception as e:
                print(f"✗ {model_name} failed: {str(e)}")
        
    except Exception as e:
        print(f"\nError configuring API: {str(e)}")
else:
    print("ERROR: GOOGLE_API_KEY not found in .env file")
