# Chatbot AI Configuration Fix

## Issue
The chatbot is failing because the Google Gemini AI models are unavailable. This happens when:
1. The GOOGLE_API_KEY is missing or invalid
2. The API key doesn't have proper permissions
3. The model names are outdated

## Solution

### Step 1: Get a Google Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated API key

### Step 2: Configure the Environment Variable

1. In the `ProeduVate-main/backend/` directory, create a `.env` file (if it doesn't exist)
2. Add your API key:

```env
GOOGLE_API_KEY=your_actual_api_key_here
```

### Step 3: Restart the Backend Server

After adding the API key, restart your Flask backend:

```bash
cd ProeduVate-main/backend
python run.py
```

## Updated Model Names

The AI service has been updated to use the correct current Gemini model names:
- `gemini-1.5-flash` (fastest, recommended)
- `gemini-1.5-pro` (most capable)
- `gemini-pro` (fallback)
- `gemini-1.0-pro` (legacy fallback)

## Testing

To verify the chatbot is working:
1. Open the student page
2. Click the chat icon
3. Send a test message like "Hello"
4. You should receive a response from the AI

## Fallback Behavior

If all AI models fail, the chatbot will now display a helpful error message instead of crashing, informing users about the configuration issue.

## Additional Notes

- API keys are free for testing and development
- Check [Google's pricing](https://ai.google.dev/pricing) for rate limits
- Keep your API key secure and never commit it to version control
