# Voice Agent Configuration Guide

## 🎙️ Voice Quality Improvements

The voice agent has been enhanced with the following optimizations:

### **Voice Provider: ElevenLabs**
- **Voice ID**: `rachel` - Professional, clear female voice
- **Alternative voices**: `adam`, `josh`, `bella`, `antoni`

### **Voice Parameters**
```python
{
    "stability": 0.8,           # Range: 0-1 (Higher = more consistent, less variation)
    "similarityBoost": 0.75,    # Range: 0-1 (Higher = more similar to original voice)
    "speed": 0.9,               # Range: 0.5-2.0 (Lower = slower, clearer speech)
    "optimizeStreamingLatency": 3  # Range: 0-4 (Higher = faster response)
}
```

### **Transcription: Deepgram Nova-2**
- Most accurate speech-to-text model
- Better at handling accents and background noise
- Real-time transcription

### **Conversation Settings**
```python
{
    "silenceTimeoutSeconds": 30,    # Wait 30s for candidate response
    "maxDurationSeconds": 900,      # 15 minutes max interview
    "backgroundSound": "office"     # Professional office ambiance
}
```

---

## 🎯 Key Improvements Made

### 1. **Clearer Speech**
- **Speed reduced to 0.9** (from default 1.0) for better clarity
- **Higher stability (0.8)** for consistent pronunciation
- **Professional voice** (Rachel from ElevenLabs)

### 2. **Natural Conversation**
- Clear system instructions to speak naturally
- Emphasis on pausing between sentences
- Instructions to avoid interrupting
- Conversational language instead of robotic responses

### 3. **Better Instructions**
The AI interviewer now has explicit instructions to:
- Speak clearly and at a moderate pace
- Use simple, conversational language
- Ask one question at a time
- Wait for complete answers
- Be friendly and professional

### 4. **Structured Interview Flow**
1. Warm greeting
2. Brief introduction
3. One question at a time
4. Active listening
5. Follow-up questions for clarity
6. Professional closing

---

## 🔧 Customization Options

### Change Voice Gender/Style
Edit `calling_agent.py` line ~62:

```python
"voiceId": "rachel",  # Options: rachel, bella (female), adam, josh, antoni (male)
```

### Adjust Speech Speed
Edit `calling_agent.py` line ~65:

```python
"speed": 0.9,  # Range: 0.5 (very slow) to 2.0 (very fast)
```

### Adjust Voice Consistency
Edit `calling_agent.py` line ~63:

```python
"stability": 0.8,  # Range: 0.0 (varied) to 1.0 (very consistent)
```

### Change Interview Duration
Edit `calling_agent.py` line ~78:

```python
"maxDurationSeconds": 900,  # 900 = 15 minutes
```

---

## 🎤 Available ElevenLabs Voices

| Voice ID | Gender | Description |
|----------|--------|-------------|
| `rachel` | Female | Professional, clear, friendly |
| `bella` | Female | Warm, conversational |
| `sarah` | Female | Energetic, engaging |
| `adam` | Male | Deep, authoritative |
| `josh` | Male | Casual, friendly |
| `antoni` | Male | Smooth, professional |

---

## 📊 Before vs After

### **Before (Old Configuration)**
- ❌ Used pre-configured assistant (unknown settings)
- ❌ No control over voice quality
- ❌ Generic system instructions
- ❌ No speech rate optimization
- ❌ Default transcription settings

### **After (New Configuration)**
- ✅ Custom voice configuration (ElevenLabs Rachel)
- ✅ Optimized speech rate (0.9x speed)
- ✅ High stability (0.8) for consistency
- ✅ Clear, detailed interviewer instructions
- ✅ Deepgram Nova-2 transcription
- ✅ Professional office background sound
- ✅ Natural conversation flow

---

## 🧪 Testing Recommendations

1. **Test with different voices** to find the best fit
2. **Adjust speed** based on candidate feedback
3. **Monitor transcription accuracy** in `demo_assets/interview_transcript.txt`
4. **Check for interruptions** - increase `silenceTimeoutSeconds` if needed

---

## 🚨 Troubleshooting

### Voice sounds robotic
- **Decrease stability** to 0.6-0.7 for more variation
- **Increase temperature** in model config to 0.8

### Speech too fast
- **Decrease speed** to 0.8 or 0.7

### Voice cuts off candidate
- **Increase silenceTimeoutSeconds** to 40-60

### Poor transcription quality
- Already using best model (Deepgram Nova-2)
- Check candidate's phone connection quality
- Ensure quiet environment

---

## 💡 Pro Tips

1. **For technical interviews**: Use slower speed (0.8) for complex questions
2. **For casual screening**: Use faster speed (1.0) for efficiency
3. **For non-native speakers**: Increase `silenceTimeoutSeconds` to 45-60
4. **For better engagement**: Use warmer voices like `bella` or `josh`

---

## 📝 Notes

- The assistant configuration now **overrides** the pre-configured VAPI assistant
- Interview questions are dynamically injected into the system prompt
- All calls are recorded and transcribed automatically
- Background office sound adds professionalism to the call
