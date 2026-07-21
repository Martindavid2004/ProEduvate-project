# gd_service.py - Group Discussion Service with AI Integration

import openai
import os
from datetime import datetime
import json
import random

class GDService:
    """Service for handling GD Round AI operations"""
    
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
    
    def generate_ai_agent_response(self, topic, context, agent_personality, agent_gender):
        """
        Generate AI agent response for GD
        
        Args:
            topic: GD topic
            context: Previous conversation context
            agent_personality: Personality trait (e.g., 'analytical', 'creative', 'diplomatic')
            agent_gender: 'male' or 'female'
        
        Returns:
            AI agent's response text
        """
        try:
            personality_prompts = {
                'analytical': 'You are analytical and data-driven. Focus on facts, statistics, and logical arguments.',
                'creative': 'You are creative and innovative. Bring fresh perspectives and out-of-the-box ideas.',
                'diplomatic': 'You are diplomatic and balanced. Consider multiple viewpoints and seek common ground.',
                'aggressive': 'You are assertive and confident. Make strong arguments and challenge others politely.',
                'supportive': 'You are supportive and collaborative. Build on others\' points and encourage dialogue.'
            }
            
            personality = personality_prompts.get(agent_personality, personality_prompts['analytical'])
            
            prompt = f"""You are participating in a Group Discussion on the topic: "{topic}".
            
{personality}

Previous discussion context:
{context}

Provide a thoughtful contribution (2-3 sentences) that:
1. Addresses the topic directly
2. Adds value to the discussion
3. Is professional and articulate
4. Stays within 30-40 words

Your response:"""
            
            if self.openai_api_key:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a professional participant in a group discussion."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=100,
                    temperature=0.7
                )
                return response.choices[0].message.content.strip()
            else:
                # Fallback mock responses
                return self._generate_mock_response(topic, agent_personality)
        
        except Exception as e:
            print(f"Error generating AI response: {e}")
            return self._generate_mock_response(topic, agent_personality)
    
    def _generate_mock_response(self, topic, personality):
        """Generate mock response when OpenAI is not available"""
        responses = {
            'analytical': [
                f"Looking at {topic} from a data perspective, studies show significant trends that we should consider.",
                f"The empirical evidence regarding {topic} suggests we need a systematic approach.",
                f"Statistical analysis of {topic} reveals some interesting patterns we can't ignore."
            ],
            'creative': [
                f"What if we approached {topic} from a completely different angle?",
                f"I think {topic} presents a unique opportunity for innovation.",
                f"Let me share an unconventional perspective on {topic}."
            ],
            'diplomatic': [
                f"I appreciate the various viewpoints on {topic}. Perhaps we can find common ground.",
                f"While there are different opinions on {topic}, I believe both sides have merit.",
                f"Considering all perspectives on {topic}, we might reach a balanced conclusion."
            ],
            'aggressive': [
                f"I strongly believe that {topic} requires immediate and decisive action.",
                f"The facts clearly support a particular stance on {topic}.",
                f"Let's be honest about {topic} - the evidence is compelling."
            ],
            'supportive': [
                f"That's an excellent point about {topic}. Let me build on that.",
                f"I agree with the previous observation on {topic} and would like to add...",
                f"Great insights on {topic}. This reminds me of related aspects we should consider."
            ]
        }
        
        return random.choice(responses.get(personality, responses['analytical']))
    
    def evaluate_participant_response(self, response_text, evaluation_criteria, topic):
        """
        Evaluate a participant's response using AI
        
        Args:
            response_text: The participant's spoken/written response
            evaluation_criteria: Dict of criteria with weights
            topic: GD topic
        
        Returns:
            Dict with scores for each criterion
        """
        try:
            if not self.openai_api_key:
                return self._generate_mock_evaluation(evaluation_criteria)
            
            criteria_descriptions = "\n".join([
                f"- {key}: {value['description']} (Weight: {value['weight']}%)"
                for key, value in evaluation_criteria.items()
            ])
            
            prompt = f"""Evaluate the following Group Discussion response on the topic "{topic}":

Response: "{response_text}"

Evaluation Criteria:
{criteria_descriptions}

Provide a JSON response with scores (0-100) for each criterion. Example:
{{
    "communication_skills": 85,
    "leadership": 75,
    "logical_reasoning": 80,
    "content_relevance": 90,
    "listening_team_dynamics": 70
}}

Evaluation:"""
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert evaluator for group discussions."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.3
            )
            
            result = response.choices[0].message.content.strip()
            scores = json.loads(result)
            
            return scores
        
        except Exception as e:
            print(f"Error evaluating response: {e}")
            return self._generate_mock_evaluation(evaluation_criteria)
    
    def _generate_mock_evaluation(self, criteria):
        """Generate mock evaluation scores"""
        scores = {}
        for key in criteria.keys():
            scores[key] = random.randint(65, 95)
        return scores
    
    def generate_gd_summary(self, topic, all_responses, participants):
        """
        Generate a comprehensive summary of the GD round
        
        Args:
            topic: GD topic
            all_responses: List of all responses from participants
            participants: List of participant data with scores
        
        Returns:
            Summary text
        """
        try:
            if not self.openai_api_key:
                return self._generate_mock_summary(topic, participants)
            
            responses_text = "\n".join([
                f"{r['participant_name']}: {r['text']}"
                for r in all_responses
            ])
            
            prompt = f"""Summarize this Group Discussion on the topic: "{topic}"

Participants and their key contributions:
{responses_text}

Provide a concise summary (150-200 words) that:
1. Highlights the main points discussed
2. Notes standout contributions
3. Identifies key insights emerged
4. Mentions the quality of the discussion

Summary:"""
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert at summarizing group discussions."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.5
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"Error generating summary: {e}")
            return self._generate_mock_summary(topic, participants)
    
    def _generate_mock_summary(self, topic, participants):
        """Generate mock summary"""
        top_performer = max(participants, key=lambda x: x['total_score'])
        
        return f"""The group discussion on "{topic}" featured engaging contributions from all participants. 
The discussion covered multiple perspectives including technical, social, and economic aspects of the topic. 
{top_performer['name']} demonstrated exceptional communication skills and provided well-structured arguments. 
Overall, the discussion maintained a professional tone with participants actively listening and building 
on each other's points. Key takeaways included the importance of balanced viewpoints and the need for 
practical solutions. The collaborative atmosphere encouraged healthy debate while maintaining respect 
for diverse opinions."""
    
    def get_ai_agent_personality(self):
        """Get a random personality for AI agent"""
        personalities = ['analytical', 'creative', 'diplomatic', 'aggressive', 'supportive']
        return random.choice(personalities)
    
    def text_to_speech_config(self, gender='male'):
        """
        Get configuration for text-to-speech
        
        Args:
            gender: 'male' or 'female'
        
        Returns:
            Configuration dict for TTS
        """
        # For Web Speech API or similar
        voices = {
            'male': {
                'rate': 1.0,
                'pitch': 0.9,
                'volume': 1.0,
                'voice_name': 'Microsoft David Desktop - English (United States)'
            },
            'female': {
                'rate': 1.0,
                'pitch': 1.1,
                'volume': 1.0,
                'voice_name': 'Microsoft Zira Desktop - English (United States)'
            }
        }
        
        return voices.get(gender, voices['male'])
    
    def speech_to_text(self, audio_data):
        """
        Convert speech to text
        
        Args:
            audio_data: Audio data to transcribe
        
        Returns:
            Transcribed text
        """
        # This would integrate with speech recognition API
        # For now, return placeholder
        return "Speech transcription would happen here with Web Speech API or similar service"
    
    def moderate_gd_content(self, text):
        """
        Moderate GD content for inappropriate language
        
        Args:
            text: Text to moderate
        
        Returns:
            (is_appropriate: bool, reason: str)
        """
        # Simple moderation - in production, use OpenAI moderation API
        inappropriate_words = ['offensive', 'inappropriate']  # Add more as needed
        
        text_lower = text.lower()
        for word in inappropriate_words:
            if word in text_lower:
                return False, f"Content contains inappropriate language: {word}"
        
        return True, "Content is appropriate"
