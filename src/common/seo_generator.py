import os
import json
import time
from openai import OpenAI
from dotenv import load_dotenv

# Try to import Google GenAI
try:
    from google import genai
    from google.genai import types
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

load_dotenv()

# ──────────────────────────────────────────────────────────────────────────────
# Trending Finance/Stock Market Keywords for SEO
# ──────────────────────────────────────────────────────────────────────────────
FINANCE_KEYWORDS = {
    "sectors": [
        "Stock Market", "Wall Street", "S&P 500", "Nasdaq", "Dow Jones",
        "Crypto", "Bitcoin", "Ethereum", "Forex", "Commodities", "Gold", "Oil",
    ],
    "companies": [
        "Apple", "Tesla", "NVIDIA", "Amazon", "Microsoft", "Google", "Meta",
        "Goldman Sachs", "JPMorgan", "Berkshire Hathaway", "BlackRock", "Visa",
    ],
    "topics": [
        "stock market", "trading", "investing", "earnings report", "IPO",
        "market analysis", "bull market", "bear market", "market crash",
        "financial news", "economy", "inflation", "interest rates",
    ],
    "finance_terms": [
        "market cap", "P/E ratio", "dividend", "portfolio", "hedge fund",
        "venture capital", "private equity", "market rally", "price target",
        "earnings call", "revenue growth", "profit margin",
    ],
    "emotional_hooks": [
        "market surge", "massive gains", "smart money moves", "breaking financial news",
        "what Wall Street won't tell you", "market prediction", "investing secrets",
        "wall street insider", "financial freedom", "must watch market update",
    ],
}

# ──────────────────────────────────────────────────────────────────────────────
# Trending Finance Hashtags
# ──────────────────────────────────────────────────────────────────────────────
FINANCE_HASHTAGS = [
    "#StockMarket", "#WallStreet", "#Investing", "#Trading", "#Finance",
    "#Crypto", "#Bitcoin", "#Nasdaq", "#SP500", "#DowJones",
    "#Economy", "#Stocks", "#Business", "#Money", "#Wealth",
    "#MarketNews", "#FinancialNews", "#Earnings", "#BullMarket", "#Tesla",
    "#NVIDIA", "#Apple", "#Amazon", "#Google", "#Forex",
    "#Commodities", "#Gold", "#IPO", "#ETF", "#Portfolio",
]


# ──────────────────────────────────────────────────────────────────────────────
# Client & Gemini helpers (unchanged)
# ──────────────────────────────────────────────────────────────────────────────
def _get_client():
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        return None
    return OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=api_key
    )

def _extract_gemini_video_context(video_path: str) -> str:
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not HAS_GEMINI or not gemini_key or not video_path or not os.path.exists(video_path):
        return ""
        
    print(f"Deep Video Analysis: Uploading {video_path} to Gemini 1.5 Flash...")
    try:
        client = genai.Client(api_key=gemini_key)
        video_file = client.files.upload(file=video_path)
        
        # Wait for video processing
        while video_file.state.name == "PROCESSING":
            print("Waiting for video processing...")
            time.sleep(5)
            video_file = client.files.get(name=video_file.name)
            
        if video_file.state.name == "FAILED":
            print("Gemini Video processing failed.")
            return ""
            
        prompt = "Analyze this video completely. 1) Describe exactly what is happening visually. 2) If it is a meme, edit, or specific historical event (e.g., a war edit masked as a football video), explicitly state what the true hidden subject is. 3) Read any on-screen text (OCR). 4) Transcribe any spoken words. Be extremely accurate."
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[video_file, prompt]
        )
        
        # Cleanup file from Gemini servers
        client.files.delete(name=video_file.name)
        
        print("Gemini Context Extraction Successful.")
        return response.text
    except Exception as e:
        print(f"Error extracting deep video context: {e}")
        return ""


# ──────────────────────────────────────────────────────────────────────────────
# Stage 1 – Analyze video for editing (improved prompts)
# ──────────────────────────────────────────────────────────────────────────────
def analyze_video_for_editing(context: dict) -> dict:
    """
    Stage 1: Analyzes video context and generates Hook Line, Short Headline, Overlay Text, and Category.
    """
    client = _get_client()
    original_title = context.get('title', '')
    fallback = {
        "category": "Market News",
        "short_headline": (
            original_title[:35] + "..."
            if len(original_title) > 35
            else (original_title if original_title else "BREAKING MARKET NEWS 📈")
        ),
        "story": (
            original_title
            if original_title
            else "Breaking financial news you need to see. Watch till the end for the full story! 📈"
        ),
        "overlay_text": "📈 BREAKING MARKET NEWS",
        "safety_flags": [],
        "safety_actions": []
    }
    
    if not client:
        print("Warning: NVIDIA_API_KEY not found. Using fallback analysis.")
        return fallback
        
    # Check if we should extract deep context via Gemini
    deep_context = ""
    local_path = context.get('local_path')
    if local_path and os.getenv("GEMINI_API_KEY"):
        deep_context = _extract_gemini_video_context(local_path)
        if deep_context:
            context['deep_context'] = deep_context  # Save for stage 2
            
    # Build context snippet for trending keywords injection
    trending_snippet = (
        f"\nTrending keyword pools to weave in naturally: "
        f"Sectors: {', '.join(FINANCE_KEYWORDS['sectors'][:6])}; "
        f"Companies: {', '.join(FINANCE_KEYWORDS['companies'][:6])}; "
        f"Terms: {', '.join(FINANCE_KEYWORDS['finance_terms'][:6])}; "
        f"Hooks: {', '.join(FINANCE_KEYWORDS['emotional_hooks'][:5])}."
    )

    prompt = f"""You are a world-class Finance and Stock Market social media strategist and content safety auditor.
Analyze the video context and metadata carefully to ensure absolute compliance with Facebook's Community Standards and Copyright/Rights Manager policies.

=== SOURCE OF TRUTH ===
Original Title/Text: {context.get('title', 'Unknown')}
Source Profile: {context.get('source', 'Unknown')}
{f"Deep AI Video Context: {context.get('deep_context', '')[:800]}" if context.get('deep_context') else ""}
{trending_snippet}

=== YOUR TASK ===
Analyze the "Original Title/Text" and any visual context. Identify:
1. The financial topic (stocks, crypto, economy, earnings, market analysis, etc.).
2. The emotional hook (e.g., breaking news, market surge, investment insight).
3. The content safety risks:
   - Does this show graphic content or sensitive political issues?
   - Is it a meme containing non-finance sensitive topics?
   - Does it use copy-protected audio or official broadcaster footage?

Then generate:
1. **short_headline** – 3-6 words max, ALL CAPS, punchy, in ENGLISH. Include 1 relevant emoji.
2. **story** – A 2-3 sentence conversational paragraph hyping the video.
3. **category** – "Market News", "Earnings", "Crypto", "Economy", "Trading", "Analysis", "Breaking News", "Documentary".
4. **safety_flags** – List containing flags if present: "violence" (graphic content), "sensitive_meme" (non-finance topics), "copyright_audio" (heavy commentary), "broadcaster_watermark" (visible tv logos). Empty list if clean.
5. **safety_actions** – Actions required to make the video safe: "mute_audio" (if audio risk), "flip_horizontal" (to avoid visual match), "trim_video" (if too long or ends in unsafe content). Empty list if clean.

Return ONLY a valid JSON object with these exact keys:
{{
  "category": "...",
  "short_headline": "...",
  "story": "...",
  "safety_flags": [],
  "safety_actions": []
}}"""
    
    try:
        completion = client.chat.completions.create(
            model="meta/llama-3.1-70b-instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500,
            timeout=45,
        )
        content = completion.choices[0].message.content.strip()
        if content.startswith("```json"): content = content[7:]
        if content.startswith("```"): content = content[3:]
        if content.endswith("```"): content = content[:-3]
        
        data = json.loads(content.strip())
        
        for key in fallback.keys():
            if key not in data:
                data[key] = fallback[key]
                
        return data
    except Exception as e:
        print(f"Error calling NVIDIA LLM API for editing analysis: {e}")
        return fallback


# ──────────────────────────────────────────────────────────────────────────────
# Stage 2 – Generate upload metadata (improved, platform-specific)
# ──────────────────────────────────────────────────────────────────────────────
import re

def clean_input_title(title: str) -> str:
    if not title:
        return ""
    # Remove URLs
    title = re.sub(r'https?://\S+', '', title)
    # Remove Twitter handles (e.g. .@username or @username)
    title = re.sub(r'\.?@\w+', '', title)
    # Remove hashtag terms (e.g. #Football)
    title = re.sub(r'#\w+', '', title)
    # Replace hyphens/underscores with spaces
    title = re.sub(r'[-_]', ' ', title)
    # Clean up extra spacing
    title = re.sub(r'\s+', ' ', title)
    return title.strip()

def generate_upload_metadata(context: dict) -> dict:
    """
    Stage 2: Generates SEO metadata based on the full editing context.
    Platform-specific: YouTube (title <60 chars, description, tags) + Facebook (caption, hashtags).
    """
    client = _get_client()
    if not client:
        print("Warning: NVIDIA_API_KEY not found. Using fallback SEO data.")
        return _get_fallback_metadata(context)
    
    # Clean the input context strings to remove noisy handles, URLs, and hashtags
    title_clean = clean_input_title(context.get('title', 'Unknown'))
    headline_clean = clean_input_title(context.get('short_headline', ''))
    story_clean = clean_input_title(context.get('story', ''))

    # Build a compact keyword reference for the prompt
    sample_keywords = ', '.join(
        FINANCE_KEYWORDS['sectors'][:4]
        + FINANCE_KEYWORDS['companies'][:4]
        + FINANCE_KEYWORDS['topics'][:3]
    )
    sample_hashtags = ' '.join(FINANCE_HASHTAGS[:15])

    prompt = f"""You are a top-tier Finance and Stock Market social media SEO specialist. Generate platform-specific upload metadata for a viral finance video.

=== FULL VIDEO CONTEXT ===
Original Title/Text: {title_clean}
Source Profile: {context.get('source', 'Unknown')}
Determined Category: {context.get('category', 'Market News')}
Headline Used in Video: {headline_clean}
Story Used in Video: {story_clean}

=== TRENDING FINANCE REFERENCE DATA ===
Keyword pool (use naturally): {sample_keywords}
Trending hashtag pool: {sample_hashtags}

=== YOUR TASK ===
Generate SEO metadata tailored for YouTube AND Facebook. Each platform has different best practices.

**1. "title" (YouTube SEO Title)**
• STRICTLY under 60 characters.
• Include the most relevant stock/company/market name.
• Use a power word (BREAKING, MASSIVE, ELITE, EPIC, SURGING, CRASH).
• Example: "NVIDIA Surges 10% After Earnings Beat 📈"

**2. "description" (YouTube Description)**
• 2-3 sentences. First sentence must hook the viewer.
• Naturally include 3-5 finance keywords (sectors, companies, topics).
• End with a call to action (Like, Subscribe, Comment).
• Include relevant hashtags at the end.
• DO NOT append or request any Source URLs. Keep it clean.

**3. "facebook_caption" (Facebook Reels Caption)**
• Short, punchy, MAX 2 sentences. Do NOT include hashtags here.
• Must include a clear call-to-action (e.g., "Drop a 📈 if you're bullish!", "Who saw this coming?").
• Conversational tone, like texting a friend.

**4. "hashtags" (Facebook Hashtags – string)**
• A single string of 7-8 highly relevant hashtags.
• MUST include at least 2 finance-specific hashtags from the context.
• Mix broad (#Finance, #StockMarket) with specific (#Bitcoin, #NVIDIA).
• Never use non-finance hashtags.

**5. "tags" (YouTube Tags – list of strings)**
• A list of 8-10 SEO tags for YouTube.
• Include: sector names (2-3), company names (1-2), topic names (1-2), generic finance terms (2-3).
• Tags should be what investors would actually search on YouTube.

=== RULES ===
• Everything must be strictly finance, stock market, crypto, economy related. No politics, no military, no unrelated topics.
• Write only in English.
• Match the emotional tone of the video (breaking news → urgent, market surge → excited, analysis → informative).
• Do NOT output any source URLs or Twitter usernames/handles.

Return ONLY a valid JSON object with these exact keys:
{{
  "title": "...",
  "description": "...",
  "facebook_caption": "...",
  "hashtags": "...",
  "tags": ["...", "...", "..."]
}}"""
    
    try:
        completion = client.chat.completions.create(
            model="nvidia/nemotron-3-ultra-550b-a55b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            top_p=0.95,
            max_tokens=1024,
        )
        
        content = completion.choices[0].message.content
        if content.startswith("```json"): content = content[7:]
        if content.startswith("```"): content = content[3:]
        if content.endswith("```"): content = content[:-3]
            
        data = json.loads(content.strip())
        
        # Enforce YouTube title length
        if "title" in data and len(data["title"]) > 60:
            data["title"] = data["title"][:57] + "..."
        
        required_keys = ["title", "description", "facebook_caption", "hashtags", "tags"]
        for key in required_keys:
            if key not in data:
                data[key] = _get_fallback_metadata(context)[key]
                
        return data

    except Exception as e:
        print(f"Error calling NVIDIA LLM API for SEO: {e}")
        return _get_fallback_metadata(context)


# ──────────────────────────────────────────────────────────────────────────────
# Football-specific fallbacks
# ──────────────────────────────────────────────────────────────────────────────
def _get_fallback_metadata(context=None):
    if not context:
        context = {}
    
    raw_title = context.get('title', 'Breaking Financial News! 📈💰')
    original_title = clean_input_title(raw_title)
    if not original_title:
        original_title = "Breaking Financial News! 📈💰"
        
    category = context.get('category', 'Market News')

    # Smart truncation for YouTube title
    yt_title = original_title[:57] + "..." if len(original_title) > 57 else original_title

    # Build description with trending keywords
    kw = FINANCE_KEYWORDS
    sector_hint = ""
    for s in kw["sectors"]:
        if s.lower() in original_title.lower():
            sector_hint = f" covering {s}"
            break

    description = (
        f"{original_title}\n\n"
        f"An important update from the world of finance{sector_hint}.\n"
        f"👉 LIKE this video, SUBSCRIBE for daily market updates, and COMMENT your thoughts! 📈💰"
    )

    # Pick the most relevant hashtags from the trending list
    context_lower = original_title.lower()
    specific_hashtags = []
    for ht in FINANCE_HASHTAGS:
        name = ht[1:].lower()  # strip #
        if name in context_lower or any(name in s.lower() for s in kw["sectors"]) or any(name in c.lower() for c in kw["companies"]):
            specific_hashtags.append(ht)
    # Always include broad ones
    base_hashtags = ["#Finance", "#StockMarket", "#WallStreet", "#Investing"]
    all_hashtags = list(dict.fromkeys(specific_hashtags + base_hashtags))[:8]
    hashtag_string = " ".join(all_hashtags)

    # Build tags
    tags = []
    # Add matched sectors
    for s in kw["sectors"]:
        if s.lower() in context_lower:
            tags.append(s)
    # Add matched companies
    for c in kw["companies"]:
        if c.lower() in context_lower:
            tags.append(c)
    # Add matched topics
    for t in kw["topics"]:
        if t.lower() in context_lower:
            tags.append(t)
    # Fill with generic finance tags
    generic = ["Finance", "Stock Market", "Trading", "Investing", "Economy", "Wall Street", "Market News"]
    for g in generic:
        if len(tags) < 10 and g not in tags:
            tags.append(g)
    tags = tags[:10]

    return {
        "title": yt_title,
        "description": description,
        "facebook_caption": (
            f"{original_title}\n\n"
            f"{'📈 Breaking market news! What do you think?' if 'breaking' in category.lower() else '💰 Important financial update!'}"
            f" Drop a comment and share your take! 👇"
        ),
        "hashtags": hashtag_string,
        "tags": tags,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Self-test
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    dummy_context = {
        "title": "NVIDIA Surges 15% After Blowout Earnings Report .@NVIDIA https://t.co/xyz",
        "source": "Bloomberg",
        "source_url": "https://x.com/Bloomberg/status/1234567890"
    }
    analysis = analyze_video_for_editing(dummy_context)
    print("Editing Analysis:")
    print(json.dumps(analysis, indent=4))
    
    # Merge for Stage 2
    dummy_context.update(analysis)
    
    print("\nGenerated Metadata:")
    print(json.dumps(generate_upload_metadata(dummy_context), indent=4))

