try:
    import openai
    HAS_OPENAI = True
except ImportError:
    openai = None
    HAS_OPENAI = False

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    genai = None
    HAS_GEMINI = False

import os
import re
import subprocess
from datetime import datetime
import json
import requests

class GDService:
    """Service for handling GD Round AI operations"""

    # Canonical sentence the AI agent says when the participant's latest
    # statement is unrelated to the topic. Frontend detects an off-topic
    # intervention by exact match against this constant (OFF_TOPIC_REPLY).
    OFF_TOPIC_REPLY = "This is not related to the topic. Please speak points related to the topic."

    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY') if HAS_OPENAI else None
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        self.ollama_base_url = os.getenv('OLLAMA_BASE_URL', 'http://127.0.0.1:11434')
        self.ollama_model = os.getenv('OLLAMA_MODEL', 'llama3.2:3b')

        if HAS_OPENAI and self.openai_api_key:
            openai.api_key = self.openai_api_key
        if HAS_GEMINI and self.google_api_key:
            try:
                genai.configure(api_key=self.google_api_key)
            except Exception as e:
                print(f"Error configuring Gemini API: {e}")

    def check_topic_relevance(self, topic, transcript, recent_context=""):
        """Dedicated semantic topic-relevance check for a participant statement.

        This is the single authoritative relevance step: it runs BEFORE any
        normal agent response is generated. It uses the LLM for meaning-based
        judgement when a provider is configured and falls back to the
        deterministic heuristic gate otherwise. It is NOT keyword matching:
        a statement can be relevant without containing any topic keyword, and
        a statement containing a topic keyword can still be irrelevant.

        Returns structured output:
            {
                "is_relevant": bool,
                "confidence": float 0-1,
                "reason": str,
                "method": 'llm' | 'heuristic'
            }
        """
        result = {"is_relevant": True, "confidence": 0.0, "reason": "", "method": "heuristic"}
        text = (transcript or "").strip()
        if not text:
            result.update(is_relevant=False, confidence=1.0,
                          reason="Empty statement - nothing to evaluate.")
            return result

        context_section = f"""Recent discussion context:
{(recent_context or '')[:800]}

""" if recent_context else ""

        prompt = f"""Decide whether the participant's statement is genuinely RELATED to the group discussion topic.

Topic:
"{topic}"

{context_section}Participant statement:
"{text}"

Judge by MEANING, not by keyword matching:
- A statement can be RELEVANT without containing any topic keyword.
  Example: topic "Impact of AI on Employment", statement "Reskilling workers
  is necessary because automation can change job requirements" -> RELATED.
- A statement containing a topic keyword can still be UNRELATED.
  Example: topic "Impact of AI on Employment", statement "Yesterday I watched
  a movie with my friends" -> UNRELATED.
- Gibberish, filler or disconnected chatter is UNRELATED.

Respond with ONLY a valid JSON object:
{{"is_relevant": true or false, "confidence": 0.0-1.0, "reason": "one short sentence"}}"""
        system_prompt = "You are an impartial discussion moderator. Respond only with a valid JSON object."

        try:
            parsed = self._call_llm_with_fallback(
                prompt, system_prompt, max_tokens=120, temperature=0.0,
                json_mode=True, valid_keys=["is_relevant"]
            )
        except Exception as e:
            print(f"[RELEVANCE] LLM relevance check failed, falling back to heuristic: {e}")
            parsed = None

        if isinstance(parsed, dict) and "is_relevant" in parsed:
            try:
                conf = float(parsed.get("confidence", 0.0))
            except (TypeError, ValueError):
                conf = 0.0
            result.update(
                is_relevant=bool(parsed.get("is_relevant")),
                confidence=max(0.0, min(1.0, conf)),
                reason=str(parsed.get("reason", ""))[:200],
                method="llm",
            )
        else:
            related, ratio = self._judge_topic_relevance(text, topic)
            result.update(
                is_relevant=bool(related),
                confidence=round(float(ratio), 2),
                reason=("Statement contains genuine topic substance." if related
                        else "Statement does not address the GD topic."),
                method="heuristic",
            )

        print(f"[RELEVANCE] method={result['method']} is_relevant={result['is_relevant']} "
              f"confidence={result['confidence']} statement={text[:80]!r}")
        return result

    def generate_ai_agent_response(self, topic, context, agent_personality, agent_gender,
                                   latest_user_text="", respond_to_name=None,
                                   respond_to_type="user", respond_to_text="", agent_name=None,
                                   relevance=None):
        """
        Generate AI agent response for GD.

        Speaker-aware behaviour: the agent responds to the PREVIOUS speaker,
        who may be another AI agent (respond_to_type='agent') or the human
        participant (respond_to_type='user'). It must NOT always address the
        user.

        For USER-directed turns, the latest user utterance (latest_user_text)
        is first checked for topic relevance via check_topic_relevance(). If
        it is NOT related to the topic, the agent says so plainly instead of
        forcing an indirect connection to the topic.

        For AGENT-directed turns, the agent responds to respond_to_name's
        point (respond_to_text), grounded in the actual discussion context -
        never inventing statements.

        When no LLM provider is available we return an explicit error marker
        instead of a random canned response - the caller surfaces a clear
        'AI unavailable' message rather than speaking something unrelated.
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

            # Clean and truncate the latest utterances so the prompt always
            # reflects what was actually just said (transcription artifacts trimmed).
            latest_user_text = (latest_user_text or '').strip()
            if len(latest_user_text) > 500:
                latest_user_text = latest_user_text[:500] + '...'
            respond_to_text = (respond_to_text or '').strip()
            if len(respond_to_text) > 500:
                respond_to_text = respond_to_text[:500] + '...'

            # ---- Dedicated topic-relevance gate (semantic, not keyword-only) ----
            # Every USER statement is checked for topic relevance BEFORE a
            # normal response is generated. Agent-to-agent turns skip this:
            # agent statements are generated from the topic context itself,
            # so there is no new user statement to validate.
            if respond_to_type != 'agent' and latest_user_text:
                if relevance is None:
                    relevance = self.check_topic_relevance(topic, latest_user_text, context)
                if not relevance.get("is_relevant", True):
                    print(f"[RELEVANCE] UNRELATED (method={relevance.get('method')}, "
                          f"confidence={relevance.get('confidence')}) -> off-topic intervention, "
                          f"no normal agent response generated")
                    return self.OFF_TOPIC_REPLY

            if respond_to_type == 'agent' and respond_to_name and respond_to_text:
                # Agent-to-agent turn: respond to the previous AGENT's point so
                # the discussion flows between speakers, not always to the user.
                user_section = f"""The previous speaker, {respond_to_name}, JUST said (respond to THEM, not to the participant):
"{respond_to_text}"
"""
                instruction = f"""You are {agent_name or 'a participant'} in this group discussion.
1. Respond directly to {respond_to_name}'s latest point: agree, disagree
   partially, ask a question, or build on it
2. Ground every claim in the ACTUAL statements visible in the context below -
   never invent or quote statements that were not made
3. Vary your move: agree / disagree / clarify / give an example / challenge /
   extend the argument (do not always agree)
4. This is a discussion between participants - do not simply address the user
5. Stay on the topic "{topic}" and be professional"""
            elif latest_user_text:
                user_section = f"""The participant JUST said (respond directly to this):
"{latest_user_text}"
"""
                instruction = f"""STEP 1 - Judge relevance: Is the participant's latest statement genuinely
RELATED to the topic "{topic}"?

If it is NOT related to the topic (different subject, only a loose/indirect
connection, gibberish, or meaningless filler):
- Respond with EXACTLY this sentence and nothing else:
  This is not related to the topic. Please speak points related to the topic.
- Do NOT connect their statement to the topic. Do NOT build on it.
  Do NOT invent an indirect link between their words and the topic.

If it IS related to the topic:
1. Reference or acknowledge their specific point (do not ignore it)
2. Agree, disagree, or build on THAT point - stay on the discussion topic
3. Do not invent facts or arguments that the user did not make
4. If the transcript is unclear, acknowledge the unclear point and respond
   conservatively instead of creating a completely new argument
5. Never invent claims, statistics, or technologies (e.g. blockchain, metrics,
   hard data) that the user did not actually mention"""
            else:
                user_section = "No participant has spoken yet - open the discussion."
                instruction = """Open the discussion with a relevant point on the topic."""

            prompt = f"""You are participating in a Group Discussion on the topic: "{topic}".

{personality}

Recent discussion context:
{context}

{user_section}

{instruction}
6. Be professional and articulate
7. Stay within 30-40 words

Your response:"""

            system_prompt = "You are a professional participant in a group discussion. Always respond to the most recent speaker's point - whether that speaker is another AI participant or the human participant. If the most recent user statement is unrelated to the topic, say that it is not related to the topic and ask the speaker to share points related to the topic - never connect an unrelated statement to the topic. Never invent statements that were not made. Respond only in English."

            # [AI_CONTEXT] debug trail: makes it verifiable whether an unrelated
            # response is an STT problem (wrong transcript in) or a prompting
            # problem (right transcript in, wrong emphasis out).
            print(f"[AI_CONTEXT] CURRENT_USER_TRANSCRIPT: {latest_user_text!r}")
            print(f"[AI_CONTEXT] AI_PROMPT_USER_INPUT: {latest_user_text!r} "
                  f"(topic={topic!r}, personality={agent_personality!r}, "
                  f"context_len={len(context or '')}, respond_to={respond_to_type!r}, "
                  f"respond_to_name={respond_to_name!r}, agent_name={agent_name!r})")

            result = self._call_llm_with_fallback(prompt, system_prompt, max_tokens=100, temperature=0.7)
            if result:
                print(f"[AI_CONTEXT] AI_RESPONSE: {result!r}")
                return result

            # No LLM configured/available: explicit marker instead of a random
            # canned response that would be unrelated to what the user said.
            print("GDService: no LLM provider available for agent response")
            return "__AI_UNAVAILABLE__"

        except Exception as e:
            print(f"Error generating AI response: {e}")
            return "__AI_UNAVAILABLE__"

    def evaluate_participant_response(self, response_text, evaluation_criteria, topic=""):
        """
        Evaluate a participant's response using AI with an evidence-based rubric.

        The LLM prompt requires evidence from the transcript for every criterion —
        the AI cannot invent points the user did not actually make.

        Fixed rubric anchors (same for every participant, every round):
          0-19  : Off-topic / no content / empty
          20-39 : Very weak — mentions topic but no reasoning
          40-59 : Below average — some relevant points, minimal development
          60-74 : Average — clear point + basic reasoning
          75-89 : Good — clear point + reasoning + example/evidence from the text
          90-100: Excellent — compelling argument + concrete evidence + structure

        TOPIC RELEVANCE GATE: the evaluator first judges whether the response
        is genuinely related to the topic. If it is NOT, every criterion is
        capped at 5 regardless of length/fluency — speaking fluently but
        off-topic cannot earn marks.

        Returns:
            Dict with scores for each criterion, plus:
            - evaluation_method: 'llm' or 'heuristic'
            - topic_related: bool (True only when content is related to topic)
        """
        try:
            criteria_lines = "\n".join([
                f"- {key} (weight {value['weight']}%): {value['description']}"
                for key, value in evaluation_criteria.items()
            ])

            # Score anchors embedded in prompt for consistency
            rubric_anchors = """
SCORING ANCHORS (use these consistently for every participant):
  0-19  : Off-topic, no content, or empty
  20-39 : Mentions topic only, no reasoning or argument
  40-59 : Some relevant points but minimal development
  60-74 : Clear point with basic reasoning
  75-89 : Clear point + reasoning + example/evidence quoted from the response
  90-100: Compelling argument + concrete evidence from the response + clear structure
"""

            prompt = f"""You are evaluating a Group Discussion response on the topic: "{topic}".

RESPONSE TO EVALUATE:
"{response_text}"

EVALUATION CRITERIA:
{criteria_lines}

{rubric_anchors}

STEP 1 - TOPIC RELEVANCE GATE (mandatory):
Decide whether the response is genuinely RELATED to the topic "{topic}".
- Judge by the MEANING of what was said, not by single keyword matches.
- A response that talks about a different subject, or only has a loose,
  indirect connection, is NOT related.
- If NOT related: "topic_related" = false and EVERY score MUST be 0-5.
  Length, fluency and grammar earn NO marks when the content is off-topic.
- If related: "topic_related" = true and score normally.

RULES:
1. Score ONLY based on what is ACTUALLY in the response above.
2. Do NOT award points for arguments the speaker did NOT make.
3. Do NOT assume the speaker meant something they did not say.
4. For each criterion, copy a short quote from the response as evidence.
5. If the response contains no relevant content for a criterion, score it ≤ 30.
6. If the response is not related to the topic, every score MUST be ≤ 5.

Respond with ONLY a valid JSON object with EXACTLY this shape:
{{
  "topic_related": true or false,
  <one key per criterion>, where each criterion value is a JSON object with:
    - "score": integer 0-100
    - "evidence": a short quote from the response (or "none" if absent)
    - "reason": one sentence explaining the score
}}

Example format:
{{
  "topic_related": true,
  "communication_skills": {{
    "score": 72,
    "evidence": "I think AI will create new roles rather than destroy existing ones",
    "reason": "Response is clear and grammatically correct but lacks variety."
  }}
}}

JSON:"""

            system_prompt = (
                "You are an expert, impartial evaluator for group discussions. "
                "Score ONLY on the actual content of the transcript. "
                "Never invent examples or arguments absent from the text. "
                "Respond only with a valid JSON object."
            )

            print(f"[EVAL_INPUT] Topic: {topic!r}")
            print(f"[EVAL_INPUT] Response ({len(response_text)} chars): {response_text[:200]!r}")

            result = self._call_llm_with_fallback(
                prompt, system_prompt, max_tokens=700, temperature=0.1,
                json_mode=True, valid_keys=list(evaluation_criteria.keys())
            )

            if result and isinstance(result, dict):
                # Topic-relevance verdict from the gate; conservative default is
                # False so an unparseable verdict can never inflate marks.
                topic_related = bool(result.get("topic_related", False))

                # Extract scores from nested structure {crit: {score:, evidence:, reason:}}
                # or flat structure {crit: int} (LLMs sometimes ignore the format)
                scores = {}
                for key in evaluation_criteria.keys():
                    val = result.get(key)
                    if isinstance(val, dict):
                        raw = val.get("score", 0)
                        # Enforce the gate: off-topic content is capped at 5 even
                        # if the LLM ignored the rule and scored generously.
                        if not topic_related:
                            raw = min(float(raw), 5)
                        scores[key] = raw
                    elif isinstance(val, (int, float)):
                        raw = val
                        if not topic_related:
                            raw = min(float(raw), 5)
                        scores[key] = raw
                    else:
                        scores[key] = 0
                scores["topic_related"] = topic_related
                scores["evaluation_method"] = "llm"
                scores["_llm_detail"] = result   # preserve evidence/reason for future display
                print(f"[EVAL_OUTPUT] LLM scores: { {k: v for k, v in scores.items() if k not in ('_llm_detail', 'topic_related')} }")
                print(f"[EVAL_OUTPUT] topic_related={topic_related}")
                return scores

            # Deterministic content-based heuristic fallback.
            # scores["evaluation_method"] is set by the caller.
            scores = self._heuristic_evaluation(evaluation_criteria, response_text, topic)
            return scores

        except Exception as e:
            print(f"Error evaluating response: {e}")
            scores = self._heuristic_evaluation(evaluation_criteria, response_text, topic)
            scores["evaluation_method"] = "heuristic"
            return scores

    def _extract_json(self, text):
        """Robustly extract a JSON object from an LLM response (handles
        markdown fences, leading text, and trailing prose)."""
        if not text or not isinstance(text, str):
            return None
        cleaned = text.strip()
        # Strip markdown code fences
        cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
        cleaned = re.sub(r'\s*```$', '', cleaned)
        # Try direct parse
        try:
            obj = json.loads(cleaned)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            pass
        # Fall back to the first {...} block in the text
        match = re.search(r'\{[^{}]*\}', cleaned, re.DOTALL)
        if match:
            try:
                obj = json.loads(match.group(0))
                if isinstance(obj, dict):
                    return obj
            except json.JSONDecodeError:
                pass
        return None

    def _judge_topic_relevance(self, text, topic):
        """Strict, meaning-based topic relevance check for the heuristic
        evaluator (used when no LLM is configured).

        Returns (topic_related: bool, relevance_ratio: float).

        The gate requires the response to contain REAL topic substance: enough
        meaningful topic terms (or clear synonyms for the topic's core
        concepts). A single stray keyword inside unrelated speech is NOT
        enough - that is exactly the 'indirectly connected' case that must
        score near zero.
        """
        words = set(re.findall(r"[a-z']+", (text or '').lower()))
        if not words:
            return False, 0.0

        STOP = {
            'the', 'a', 'an', 'in', 'on', 'of', 'and', 'or', 'is', 'are', 'was',
            'were', 'be', 'been', 'to', 'for', 'with', 'vs', 'versus', 'at', 'by',
            'from', 'that', 'this', 'it', 'its', 'as', 'not', 'but', 'we', 'i',
            'you', 'they', 'he', 'she', 'will', 'would', 'should', 'can', 'could',
            'do', 'does', 'did', 'have', 'has', 'had', 'about', 'into', 'than',
            'then', 'so', 'if', 'when', 'what', 'which', 'who', 'how', 'why',
            'think', 'believe', 'feel', 'point', 'view', 'opinion', 'agree',
            'disagree', 'because', 'therefore', 'however', 'moreover', 'also',
            'very', 'really', 'just', 'like', 'some', 'many', 'much', 'more',
            'most', 'other', 'others', 'people', 'today', 'now', 'days', 'world',
        }

        # Meaningful words = everything except generic stopwords
        meaningful = words - STOP
        if not meaningful:
            return False, 0.0

        # Topic vocabulary: content words from the topic itself
        topic_words = set(re.findall(r"[a-z']+", (topic or '').lower())) - STOP
        if not topic_words:
            return False, 0.0

        # Core (longest) topic words weigh double - they carry the topic meaning
        core_topic_words = {w for w in topic_words if len(w) >= 5}
        matched_core = {w for w in core_topic_words if w in meaningful}
        matched_other = {w for w in topic_words - core_topic_words if w in meaningful}

        # Synonym seeds for common GD topic concepts (small, targeted map -
        # catches responses that discuss the concept without the exact word).
        SYNONYMS = {
            'ai': {'ai', 'artificial', 'intelligence', 'machine', 'automation', 'robots', 'algorithm'},
            'employment': {'employment', 'jobs', 'job', 'work', 'workers', 'unemployment', 'careers', 'labor', 'labour', 'hiring'},
            'remote': {'remote', 'home', 'hybrid', 'office'},
            'work': {'work', 'working', 'workplace', 'office', 'job'},
            'social': {'social', 'media', 'instagram', 'facebook', 'twitter', 'online', 'networks'},
            'media': {'media', 'internet', 'online', 'platforms'},
            'climate': {'climate', 'environment', 'warming', 'carbon', 'emissions', 'pollution'},
            'education': {'education', 'schools', 'school', 'students', 'teachers', 'learning', 'universities', 'classroom'},
            'health': {'health', 'mental', 'wellbeing', 'wellness', 'stress', 'burnout'},
            'energy': {'energy', 'renewable', 'solar', 'wind', 'fossil', 'power'},
            'privacy': {'privacy', 'data', 'surveillance', 'personal'},
            'ecommerce': {'ecommerce', 'e-commerce', 'retail', 'shopping', 'online', 'stores'},
            'startup': {'startup', 'startups', 'entrepreneurship', 'founders', 'venture'},
            'gender': {'gender', 'women', 'men', 'equality', 'equal', 'diversity'},
            'youth': {'youth', 'young', 'generation', 'students'},
        }

        # Expand topic words with their synonym families
        expanded = set(topic_words)
        for tw in topic_words:
            singular = tw.rstrip('s') if tw.endswith('s') and len(tw) > 3 else tw
            for key, fam in SYNONYMS.items():
                if tw == key or singular == key or tw in fam:
                    expanded |= fam

        matched_expanded = {w for w in expanded if w in meaningful}

        # Weighted score: core topic words count 2, others 1
        weight_sum = 2 * len(matched_core) + 1 * len(matched_expanded - matched_core)
        max_weight = 2 * len(core_topic_words) + len(expanded - core_topic_words)
        ratio = weight_sum / max_weight if max_weight else 0.0

        # GATE: need at least 2 distinct topic-concept matches (each can be a
        # core topic word or a synonym of the topic's core concepts). One
        # stray keyword (e.g. "AI" or "machine" in random chatter) is NOT
        # enough - that is the indirect connection case.
        distinct_matches = len(matched_expanded)
        related = distinct_matches >= 2

        return related, ratio

    def _heuristic_evaluation(self, criteria, response_text="", topic=""):
        """Deterministic, content-based scoring used ONLY when no LLM is
        available. Transparent and repeatable — the same response always gets
        the same scores, so it is clearly distinguishable from random dummy
        marks.

        STRICT TOPIC-RELEVANCE GATE (mirrors the LLM gate): if the response
        does not contain genuine topic substance, every criterion is capped
        at 5 — off-topic speech must score near zero regardless of length or
        fluency.

        Rubric anchors (matches the LLM rubric):
          < 5 words  → 0-20  (effectively empty / noise)
          5-19 words → 20-50 (very brief, minimal content)
          20-49 words → 40-65 (moderate)
          50+ words → up to 85 (with relevant content bonuses)

        evaluation_method is set by the caller.
        """
        scores = {}
        text = (response_text or "").strip().lower()
        words = text.split()
        word_count = len(words)

        if word_count == 0:
            # Nothing to evaluate: honest zero scores, not inflated dummies
            for key in criteria.keys():
                scores[key] = 0
            scores["topic_related"] = False
            return scores

        # ---- STRICT TOPIC RELEVANCE GATE ----
        topic_related, relevance_ratio = self._judge_topic_relevance(text, topic)
        if not topic_related:
            # Off-topic: honest near-zero scores no matter how long or fluent
            # the response is. Same gate the LLM evaluation enforces - this is
            # the fix for "random scores for irrelevant speech".
            for key in criteria.keys():
                scores[key] = 5
            scores["topic_related"] = False
            print(f"[EVAL_OUTPUT] Heuristic: OFF-TOPIC (relevance_ratio={relevance_ratio:.2f}) -> all scores capped at 5")
            return scores

        # --- Length-based base score ---
        # Short answers get modest bases; long answers have potential for higher
        if word_count < 5:
            base = 15
        elif word_count < 10:
            base = 30
        elif word_count < 20:
            base = 45
        elif word_count < 50:
            base = 58
        else:
            base = 65

        # Word count bonus: up to +15 for very long responses (100+ words)
        length_bonus = min(15, word_count // 7)

        # Topic relevance factor
        topic_words = set((topic or "").lower().split()) - {
            'the', 'a', 'an', 'in', 'on', 'of', 'and', 'or', 'is', 'vs', 'to', 'for'
        }
        matched_topic_words = sum(1 for w in words if w in topic_words)
        relevance_bonus = min(12, matched_topic_words * 4)

        # Logical connectors factor
        logic_connectors = {
            'because', 'therefore', 'however', 'since', 'furthermore',
            'due', 'consequently', 'thus', 'impact', 'result', 'reason',
            'although', 'moreover', 'instead', 'otherwise', 'hence',
        }
        logic_count = sum(1 for w in words if w in logic_connectors)
        logic_bonus = min(12, logic_count * 4)

        # Collaboration / team dynamics factor
        team_keywords = {
            'agree', 'point', 'perspective', 'view', 'build', 'listen',
            'consider', 'opinion', 'collaborate', 'understand', 'respect',
            'support', 'team', 'together', 'balance',
        }
        team_count = sum(1 for w in words if w in team_keywords)
        team_bonus = min(12, team_count * 4)

        for key in criteria.keys():
            if key == 'communication_skills':
                unique_words = len(set(words)) if words else 0
                diversity = (unique_words / word_count * 12) if word_count > 0 else 0
                score = base + length_bonus + min(12, int(diversity))
            elif key == 'content_relevance':
                score = base + length_bonus + relevance_bonus
            elif key == 'logical_reasoning':
                score = base + length_bonus + logic_bonus
            elif key == 'leadership':
                score = base + length_bonus + min(8, logic_bonus) + min(8, relevance_bonus)
            elif key == 'listening_team_dynamics':
                score = base + length_bonus + team_bonus
            else:
                score = base + length_bonus

            # Clamp between honest bounds: empty answer floor is 0 (set above),
            # heuristic ceiling is 85 (LLM is needed for 85-100 range evidence).
            scores[key] = min(85, max(0, round(score)))

        scores["topic_related"] = True
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

            system_prompt = "You are an expert at summarizing group discussions."

            result = self._call_llm_with_fallback(prompt, system_prompt, max_tokens=300, temperature=0.5)
            if result:
                return result

            return self._generate_mock_summary(topic, participants)

        except Exception as e:
            print(f"Error generating summary: {e}")
            return self._generate_mock_summary(topic, participants)

    def _generate_mock_summary(self, topic, participants):
        """Generate mock summary"""
        if participants:
            top_performer = max(participants, key=lambda x: x['total_score'])
        else:
            top_performer = {'name': 'No participants', 'total_score': 0}

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
        import random
        return random.choice(personalities)

    # Ordered list of Gemini models to try. The first entry is the preferred
    # fast model; later entries are fallbacks for accounts/regions where a
    # model is unavailable or disabled.
    GEMINI_MODEL_CANDIDATES = [
        'gemini-flash-lite-latest',
        'gemini-3.1-flash-lite',
        'gemini-flash-latest',
        'gemini-2.5-flash-lite',
    ]

    def _is_quality_text(self, text, min_chars=15, min_words=3):
        """Return True if the generated text looks like a real response and not
        a truncated/garbage fragment (e.g. '4', 'While', 'AI displacing')."""
        if not text or not isinstance(text, str):
            return False
        stripped = text.strip()
        if len(stripped) < min_chars:
            return False
        word_count = len(stripped.split())
        return word_count >= min_words

    def _call_gemini(self, prompt, system_prompt, max_tokens=100, temperature=0.7, json_mode=False, valid_keys=None):
        """Call Google Gemini API, trying multiple model candidates.
        With json_mode=True, returns a parsed dict instead of text."""
        if not (HAS_GEMINI and self.google_api_key):
            return None
        # Allow an explicit env override, then fall back to the candidate list
        candidates = [os.getenv('GEMINI_MODEL')] if os.getenv('GEMINI_MODEL') else []
        candidates += [m for m in self.GEMINI_MODEL_CANDIDATES if m not in candidates]
        for model_name in candidates:
            try:
                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=system_prompt
                )
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=max_tokens,
                        temperature=temperature,
                        response_mime_type="application/json" if json_mode else None,
                    )
                )
                text = response.text.strip() if (response and hasattr(response, 'text') and response.text) else ''
                if json_mode:
                    parsed = self._extract_json(text)
                    if parsed and (not valid_keys or any(k in parsed for k in valid_keys)):
                        return parsed
                    print(f"Gemini model {model_name} JSON-mode returned unparseable/invalid content: {text[:80]!r}")
                    continue
                if self._is_quality_text(text):
                    return text
                print(f"Gemini model {model_name} returned low-quality response: {text[:50]!r}")
            except Exception as e:
                print(f"Gemini model {model_name} error: {str(e)[:120]}")
        return None

    def _call_openai(self, prompt, system_prompt, max_tokens=100, temperature=0.7, json_mode=False, valid_keys=None):
        """Call OpenAI API"""
        if not (HAS_OPENAI and self.openai_api_key):
            return None
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            text = response.choices[0].message.content.strip()
            if json_mode:
                parsed = self._extract_json(text)
                if parsed and (not valid_keys or any(k in parsed for k in valid_keys)):
                    return parsed
                print(f"OpenAI JSON-mode returned unparseable content: {text[:80]!r}")
                return None
            return text
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return None

    # Groq models in order of preference (ultra-low latency)
    GROQ_MODEL_CANDIDATES = ['llama-3.1-8b-instant', 'llama-3.3-70b-versatile', 'llama3-8b-8192']

    def _call_groq(self, prompt, system_prompt, max_tokens=100, temperature=0.7, json_mode=False, valid_keys=None):
        """Call Groq API (OpenAI-compatible) - fast llama inference"""
        if not self.groq_api_key:
            return None
        for model in self.GROQ_MODEL_CANDIDATES:
            try:
                headers = {
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json"
                }
                body = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": max_tokens,
                    "temperature": temperature
                }
                if json_mode:
                    body["response_format"] = {"type": "json_object"}
                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=body,
                    timeout=15
                )
                response.raise_for_status()
                text = response.json()["choices"][0]["message"]["content"].strip()
                if json_mode:
                    parsed = self._extract_json(text)
                    if parsed and (not valid_keys or any(k in parsed for k in valid_keys)):
                        return parsed
                    print(f"Groq model {model} JSON-mode returned unparseable content: {text[:80]!r}")
                    continue
                if text:
                    return text
            except Exception as e:
                # 404 = model unavailable for this key; try next candidate
                if "404" in str(e):
                    print(f"Groq model {model} unavailable, trying next...")
                    continue
                print(f"Groq API error ({model}): {e}")
                return None
        return None

    def _call_ollama(self, prompt, system_prompt, max_tokens=100, temperature=0.7, json_mode=False, valid_keys=None):
        """Call local Ollama API"""
        try:
            full_prompt = f"{system_prompt}\n\n{prompt}"
            body = {
                "model": self.ollama_model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature
                }
            }
            if json_mode:
                body["format"] = "json"
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json=body,
                timeout=60
            )
            response.raise_for_status()
            text = response.json().get("response", "").strip()
            if json_mode:
                parsed = self._extract_json(text)
                if parsed and (not valid_keys or any(k in parsed for k in valid_keys)):
                    return parsed
                print(f"Ollama JSON-mode returned unparseable content: {text[:80]!r}")
                return None
            return text
        except Exception as e:
            print(f"Ollama API error: {e}")
            return None

    def _call_llm_with_fallback(self, prompt, system_prompt, max_tokens=100, temperature=0.7,
                                json_mode=False, valid_keys=None):
        """Try LLM providers in order: Groq -> Gemini -> OpenAI -> Ollama.
        Groq (llama) is tried first when configured since it has the lowest
        latency; each provider's output is quality-checked so truncated/garbage
        responses don't short-circuit better (or later) providers.

        With json_mode=True, providers return parsed dicts (validated against
        valid_keys when given) instead of raw text. Returns None when every
        provider is unavailable or failed - callers must handle that."""
        # Try Groq first - lowest latency llama inference
        result = self._call_groq(prompt, system_prompt, max_tokens, temperature, json_mode, valid_keys)
        if result and (json_mode or self._is_quality_text(result)):
            return result

        # Try Gemini next for sub-second responses
        result = self._call_gemini(prompt, system_prompt, max_tokens, temperature, json_mode, valid_keys)
        if result and (json_mode or self._is_quality_text(result)):
            return result

        # Try OpenAI
        result = self._call_openai(prompt, system_prompt, max_tokens, temperature, json_mode, valid_keys)
        if result and (json_mode or self._is_quality_text(result)):
            return result

        # Try Ollama
        result = self._call_ollama(prompt, system_prompt, max_tokens, temperature, json_mode, valid_keys)
        if result and (json_mode or self._is_quality_text(result)):
            return result

        # No provider succeeded
        return None

    def get_audio_loudness(self, audio_file_path):
        """Probe the decoded audio loudness with ffmpeg to distinguish
        'silent/dead mic input' from 'transcription failure'. Returns
        (mean_volume_db, max_volume_db) or None if ffmpeg is unavailable."""
        try:
            result = subprocess.run(
                ['ffmpeg', '-i', audio_file_path, '-af', 'volumedetect', '-f', 'null', '-'],
                capture_output=True, text=True, timeout=30
            )
            stderr = result.stderr or ''
            mean_match = re.search(r'mean_volume:\s*(-?[\d.]+)\s*dB', stderr)
            max_match = re.search(r'max_volume:\s*(-?[\d.]+)\s*dB', stderr)
            if mean_match and max_match:
                return float(mean_match.group(1)), float(max_match.group(1))
        except Exception:
            pass
        return None

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

