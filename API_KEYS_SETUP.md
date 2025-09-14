# 🔑 API Keys Setup Guide

## 🚀 Quick Setup (Recommended: Start with OpenAI)

### 1. **Get OpenAI API Key (GPT-4o Mini) - RECOMMENDED**

**Why start with OpenAI:**
- ✅ **Most cost-effective**: $0.15/1M input tokens
- ✅ **Best balance** of quality and speed
- ✅ **Easy setup** and reliable API
- ✅ **Perfect for job validation**

**Steps:**
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign up or log in
3. Click "Create new secret key"
4. Copy the key (starts with `sk-`)
5. Add to your `.env` file:
   ```env
   OPENAI_API_KEY=sk-your-key-here
   ```

**Cost**: ~$0.50-1.50 per day for 1000 job validations

---

### 2. **Get Google AI Key (Gemini 1.5 Flash) - CHEAPEST**

**Why add Gemini:**
- ✅ **Cheapest option**: $0.075/1M input tokens
- ✅ **Great for bulk processing**
- ✅ **60% cost reduction** when combined with OpenAI

**Steps:**
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the key
5. Add to your `.env` file:
   ```env
   GOOGLE_API_KEY=your-google-key-here
   ```

**Cost**: ~$0.25-0.75 per day for 1000 job validations

---

### 3. **Get Anthropic API Key (Claude 3.5 Sonnet) - BEST QUALITY**

**Why add Claude:**
- ✅ **Highest quality** for complex analysis
- ✅ **Best at reasoning** and edge cases
- ✅ **Used for complex jobs** only (5% of cases)

**Steps:**
1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Sign up or log in
3. Go to "API Keys" section
4. Click "Create Key"
5. Copy the key (starts with `sk-ant-`)
6. Add to your `.env` file:
   ```env
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   ```

**Cost**: ~$2-5 per day for 1000 job validations (but only used for 5% of jobs)

---

## 🎯 **Recommended Setup Strategy**

### **Phase 1: Start Simple (OpenAI Only)**
```env
OPENAI_API_KEY=sk-your-openai-key-here
AI_STRATEGY=speed
DAILY_AI_BUDGET=2.00
```
- **Cost**: $1-2 per day
- **Quality**: Good
- **Setup time**: 5 minutes

### **Phase 2: Add Cost Optimization (OpenAI + Google)**
```env
OPENAI_API_KEY=sk-your-openai-key-here
GOOGLE_API_KEY=your-google-key-here
AI_STRATEGY=cost_effective
DAILY_AI_BUDGET=3.00
```
- **Cost**: $0.75-1.25 per day
- **Quality**: Good
- **Savings**: 40-60% cost reduction

### **Phase 3: Full Quality (All Three)**
```env
OPENAI_API_KEY=sk-your-openai-key-here
GOOGLE_API_KEY=your-google-key-here
ANTHROPIC_API_KEY=sk-ant-your-claude-key-here
AI_STRATEGY=cost_effective
DAILY_AI_BUDGET=5.00
```
- **Cost**: $1-2 per day
- **Quality**: Excellent
- **Best of all worlds**: Cheap bulk + quality analysis

---

## 🧪 **Test Your Setup**

After adding API keys, test the processor:

```bash
cd backend
source ../venv/bin/activate
python test_ai_processor.py
```

**Expected output with valid keys:**
```
✅ AI Processor initialized successfully
🔍 Testing Job 1: Senior Software Engineer at TechCorp
   Model Used: gpt-4o-mini
   Valid: True
   Confidence: 0.95
   Cost: $0.0012
   Remote Type: remote
   Experience Level: senior
   Skills: ['Python', 'React', 'AWS', 'Docker']
```

---

## 💰 **Cost Comparison**

| Setup | Daily Cost (1000 jobs) | Quality | Best For |
|-------|----------------------|---------|----------|
| **OpenAI Only** | $1-2 | ⭐⭐⭐⭐ | Getting started |
| **OpenAI + Google** | $0.75-1.25 | ⭐⭐⭐⭐ | Cost optimization |
| **All Three** | $1-2 | ⭐⭐⭐⭐⭐ | Production ready |

---

## 🔧 **Environment Configuration**

Your `.env` file should look like this:

```env
# AI API Keys
OPENAI_API_KEY=sk-your-openai-key-here
GOOGLE_API_KEY=your-google-key-here
ANTHROPIC_API_KEY=sk-ant-your-claude-key-here

# AI Processing Settings
AI_STRATEGY=cost_effective
DAILY_AI_BUDGET=5.00
MAX_JOBS_PER_DAY=1000

# Database
DATABASE_URL=sqlite:///./remote_jobs.db

# Debug
DEBUG=true
```

---

## 🚨 **Important Notes**

1. **Never commit API keys** to version control
2. **Start with OpenAI** - it's the most reliable
3. **Set daily budgets** to avoid unexpected costs
4. **Monitor usage** in the provider dashboards
5. **Test with small batches** first

---

## 🆘 **Troubleshooting**

### **"API key not valid" error:**
- Check the key is copied correctly
- Ensure no extra spaces or characters
- Verify the key is active in the provider dashboard

### **"No AI providers available" error:**
- Check your `.env` file exists
- Verify at least one API key is set
- Restart the application after adding keys

### **High costs:**
- Reduce `DAILY_AI_BUDGET`
- Use `AI_STRATEGY=speed` for cheapest option
- Check `MAX_JOBS_PER_DAY` setting

---

## 🎉 **You're Ready!**

Once you have at least one API key set up, your remote jobs platform will be able to:

- ✅ **Validate job postings** for legitimacy
- ✅ **Extract structured data** (salary, skills, etc.)
- ✅ **Filter for remote positions** with US-level salaries
- ✅ **Process jobs cost-effectively** with AI
- ✅ **Scale to thousands of jobs** per day

**Next step**: Run the test script to verify everything works!
