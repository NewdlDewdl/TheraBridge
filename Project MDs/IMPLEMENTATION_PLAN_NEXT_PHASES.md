# TherapyBridge - Next Phases Implementation Plan

## Overview

This plan covers the remaining implementation phases for TherapyBridge after resolving the current Railway deployment network issues. The system has Wave 1 and Wave 2 analysis complete, but needs production deployment optimization, additional features, and scaling improvements.

## Current State Analysis

### What's Working ✅
- **Backend API**: FastAPI with non-blocking demo initialization
- **Database**: Neon PostgreSQL with Wave 1 + Wave 2 schema
- **Transcription Pipeline**: Audio preprocessing, Whisper API, pyannote diarization
- **Analysis Pipeline**:
  - Wave 1: Topics, mood, summary, breakthrough detection
  - Wave 2: Deep analysis (JSONB) + prose analysis (TEXT)
- **Frontend**: Next.js 16 dashboard with real-time updates (SSE + polling fallback)
- **Demo Mode**: 10 pre-seeded sessions with full analysis

### Current Issues ⚠️
- Railway deployment experiencing network failures
- SSE CORS errors blocking real-time updates
- GET requests timing out (not reaching backend)
- Latest fix (b477185) removes duplicate CORS headers - awaiting deployment test

### Key Discoveries
- Non-blocking demo init works (~2-3 seconds with 120s timeout buffer)
- Wave 1 + Wave 2 analysis completes in ~30-40 seconds
- Polling fallback provides reliable updates when SSE fails
- Railway requires `print(..., flush=True)` for real-time logs

## Desired End State

After completing all phases, TherapyBridge will have:

1. **Stable Production Deployment**: Railway backend + frontend with reliable connectivity
2. **Analytics Dashboard** (Feature 2): Therapist-level insights across all patients
3. **AWS Lambda Deployment**: Cost-optimized serverless backend option
4. **GPU Pipeline**: Vast.ai integration for faster local transcription
5. **Production-Ready Auth**: Replace demo mode with real user authentication
6. **Monitoring & Observability**: Error tracking, performance metrics, alerts

### Verification
- [ ] All Railway endpoints respond within 2 seconds
- [ ] SSE connections stable for 5+ minutes
- [ ] Analytics dashboard loads with real aggregated data
- [ ] AWS Lambda handles 100+ concurrent requests
- [ ] GPU pipeline processes 60-min audio in <10 minutes
- [ ] Production auth works with real user signup/login

## What We're NOT Doing

- Therapist/Client native apps (web-only for MVP)
- Real-time transcription during sessions (post-session only)
- Multi-language support (English only for MVP)
- HIPAA compliance certification (future phase)
- Payment processing (free tier for MVP)
- Email notifications for analysis completion

---

## Phase 1: Resolve Railway Network Issues & Stabilize Deployment

### Overview
Fix the current network failure preventing all API requests from reaching Railway backend. Verify SSE connections work reliably in production.

### Changes Required

#### 1.1 Backend CORS Configuration

**File**: `backend/app/routers/sse.py`
**Status**: ✅ Already fixed in commit b477185
**Changes**: Removed duplicate CORS headers - now relies on global middleware

#### 1.2 Frontend Request Logging

**File**: `frontend/lib/api-client.ts`
**Status**: ✅ Already added in commit b477185
**Changes**: Detailed logging before fetch, on timeout, on network error, on response

#### 1.3 Railway Health Check Verification

**Action**: Verify backend is running and healthy
**Steps**:
1. Check Railway dashboard for deployment status
2. Test health endpoint: `curl https://therabridge-backend.up.railway.app/health`
3. Check Railway logs for startup errors

#### 1.4 Network Connectivity Testing

**Test Sequence**:
1. Hard refresh frontend (Cmd+Shift+R)
2. Verify demo initialization succeeds
3. Verify GET /api/sessions returns 200 with data
4. Verify SSE connection establishes
5. Monitor for 5+ minutes to ensure stability

### Success Criteria

#### Automated Verification:
- [ ] Backend health check returns 200: `curl https://therabridge-backend.up.railway.app/health`
- [ ] API root returns version 1.0.1: `curl https://therabridge-backend.up.railway.app/`
- [ ] Sessions endpoint accessible: `curl https://therabridge-backend.up.railway.app/api/sessions/` (expect 401 - no auth)
- [ ] SSE endpoint accessible: `curl https://therabridge-backend.up.railway.app/api/sse/events/test-id` (expect event stream)

#### Manual Verification:
- [ ] Hard refresh loads demo successfully within 5 seconds
- [ ] Dashboard displays 10 sessions with Wave 1 + Wave 2 data
- [ ] SSE connection shows "📡 SSE connected" in console
- [ ] No CORS errors in browser console
- [ ] No network timeout errors
- [ ] Session cards show mood, topics, summary correctly

**Implementation Note**: After Railway deployment completes and all automated checks pass, perform manual testing. If SSE still fails, disable SSE entirely and rely on polling (5-second interval) as interim solution.

---

## Phase 2: Analytics Dashboard (Feature 2)

### Overview
Build therapist-level analytics dashboard showing aggregate insights across all patients. Provides bird's-eye view of practice trends, common issues, and breakthrough patterns.

### Changes Required

#### 2.1 Database Analytics Queries

**File**: `backend/app/services/analytics_service.py` (new file)
**Changes**: Create analytics aggregation service

```python
"""Analytics Service - Aggregate patient data for therapist insights"""

from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta
from app.models.session import Session

class AnalyticsService:
    """Service for generating therapist-level analytics"""

    async def get_mood_trends(
        self,
        db: AsyncSession,
        therapist_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get mood score trends over time"""
        cutoff_date = datetime.now() - timedelta(days=days)

        # Query average mood by week
        query = (
            select(
                func.date_trunc('week', Session.session_date).label('week'),
                func.avg(Session.mood_score).label('avg_mood'),
                func.count(Session.id).label('session_count')
            )
            .where(
                and_(
                    Session.therapist_id == therapist_id,
                    Session.session_date >= cutoff_date
                )
            )
            .group_by(func.date_trunc('week', Session.session_date))
            .order_by('week')
        )

        result = await db.execute(query)
        rows = result.all()

        return {
            "trend_data": [
                {
                    "week": row.week.isoformat(),
                    "avg_mood": float(row.avg_mood),
                    "session_count": row.session_count
                }
                for row in rows
            ],
            "overall_avg": sum(r.avg_mood for r in rows) / len(rows) if rows else 0,
            "total_sessions": sum(r.session_count for r in rows)
        }

    async def get_common_topics(
        self,
        db: AsyncSession,
        therapist_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get most common topics across all sessions"""
        # Use PostgreSQL array functions to unnest topics
        query = """
            SELECT
                unnest(topics) as topic,
                COUNT(*) as frequency,
                ROUND(AVG(mood_score), 2) as avg_mood
            FROM sessions
            WHERE therapist_id = :therapist_id
              AND topics IS NOT NULL
            GROUP BY unnest(topics)
            ORDER BY frequency DESC
            LIMIT :limit
        """

        result = await db.execute(query, {"therapist_id": therapist_id, "limit": limit})
        rows = result.all()

        return [
            {
                "topic": row.topic,
                "frequency": row.frequency,
                "avg_mood": float(row.avg_mood) if row.avg_mood else None
            }
            for row in rows
        ]

    async def get_breakthrough_stats(
        self,
        db: AsyncSession,
        therapist_id: str
    ) -> Dict[str, Any]:
        """Get breakthrough detection statistics"""
        # Query sessions with breakthroughs
        query = (
            select(
                func.count(Session.id).label('total_sessions'),
                func.sum(
                    func.case((Session.breakthrough_detected == True, 1), else_=0)
                ).label('breakthrough_count')
            )
            .where(Session.therapist_id == therapist_id)
        )

        result = await db.execute(query)
        row = result.one()

        breakthrough_rate = (
            (row.breakthrough_count / row.total_sessions * 100)
            if row.total_sessions > 0
            else 0
        )

        return {
            "total_sessions": row.total_sessions,
            "breakthrough_count": row.breakthrough_count,
            "breakthrough_rate": round(breakthrough_rate, 1)
        }
```

#### 2.2 Analytics API Endpoints

**File**: `backend/app/routers/analytics.py` (new file)
**Changes**: Create analytics router

```python
"""Analytics Router - Therapist-level insights"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.analytics_service import AnalyticsService
from app.middleware.demo_auth import get_current_user

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.get("/mood-trends")
async def get_mood_trends(
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get mood trends over time"""
    service = AnalyticsService()
    therapist_id = current_user.get("therapist_id", "demo_therapist")

    return await service.get_mood_trends(db, therapist_id, days)

@router.get("/common-topics")
async def get_common_topics(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get most common topics across all sessions"""
    service = AnalyticsService()
    therapist_id = current_user.get("therapist_id", "demo_therapist")

    return await service.get_common_topics(db, therapist_id, limit)

@router.get("/breakthrough-stats")
async def get_breakthrough_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get breakthrough detection statistics"""
    service = AnalyticsService()
    therapist_id = current_user.get("therapist_id", "demo_therapist")

    return await service.get_breakthrough_stats(db, therapist_id)
```

#### 2.3 Register Analytics Router

**File**: `backend/app/main.py`
**Changes**: Add analytics router

```python
from app.routers import sessions, demo, debug, sse, analytics

# Include routers
app.include_router(sessions.router)
app.include_router(demo.router)
app.include_router(debug.router)
app.include_router(sse.router)
app.include_router(analytics.router)  # NEW
```

#### 2.4 Frontend Analytics Page

**File**: `frontend/app/analytics/page.tsx` (new file)
**Changes**: Create analytics dashboard page

```typescript
'use client'

import { useEffect, useState } from 'react'
import { apiClient } from '@/lib/api-client'
import { Line } from 'react-chartjs-2'

interface MoodTrend {
  week: string
  avg_mood: number
  session_count: number
}

interface Topic {
  topic: string
  frequency: number
  avg_mood: number
}

export default function AnalyticsPage() {
  const [moodTrends, setMoodTrends] = useState<MoodTrend[]>([])
  const [topics, setTopics] = useState<Topic[]>([])
  const [breakthroughStats, setBreakthroughStats] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const loadAnalytics = async () => {
      try {
        const [moodRes, topicsRes, breakthroughRes] = await Promise.all([
          apiClient.get('/api/analytics/mood-trends'),
          apiClient.get('/api/analytics/common-topics'),
          apiClient.get('/api/analytics/breakthrough-stats')
        ])

        if (moodRes.success) setMoodTrends(moodRes.data.trend_data)
        if (topicsRes.success) setTopics(topicsRes.data)
        if (breakthroughRes.success) setBreakthroughStats(breakthroughRes.data)
      } catch (error) {
        console.error('Failed to load analytics:', error)
      } finally {
        setIsLoading(false)
      }
    }

    loadAnalytics()
  }, [])

  if (isLoading) return <div>Loading analytics...</div>

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-8">Practice Analytics</h1>

      {/* Mood Trends Chart */}
      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">Mood Trends (Last 30 Days)</h2>
        <Line
          data={{
            labels: moodTrends.map(t => new Date(t.week).toLocaleDateString()),
            datasets: [{
              label: 'Average Mood Score',
              data: moodTrends.map(t => t.avg_mood),
              borderColor: 'rgb(75, 192, 192)',
              tension: 0.1
            }]
          }}
        />
      </section>

      {/* Common Topics */}
      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">Most Common Topics</h2>
        <div className="grid grid-cols-2 gap-4">
          {topics.map((topic, idx) => (
            <div key={idx} className="p-4 border rounded">
              <h3 className="font-semibold">{topic.topic}</h3>
              <p className="text-sm text-gray-600">
                {topic.frequency} sessions | Avg Mood: {topic.avg_mood.toFixed(1)}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Breakthrough Stats */}
      {breakthroughStats && (
        <section>
          <h2 className="text-2xl font-semibold mb-4">Breakthrough Detection</h2>
          <div className="p-6 border rounded">
            <p className="text-4xl font-bold text-green-600">
              {breakthroughStats.breakthrough_rate}%
            </p>
            <p className="text-gray-600">
              {breakthroughStats.breakthrough_count} breakthroughs in{' '}
              {breakthroughStats.total_sessions} sessions
            </p>
          </div>
        </section>
      )}
    </div>
  )
}
```

### Success Criteria

#### Automated Verification:
- [ ] Analytics service tests pass: `cd backend && pytest tests/test_analytics_service.py`
- [ ] API endpoints return valid data: `curl -H "X-Demo-Token: <token>" https://therabridge-backend.up.railway.app/api/analytics/mood-trends`
- [ ] Frontend builds without errors: `cd frontend && npm run build`

#### Manual Verification:
- [ ] Analytics page loads at `/analytics`
- [ ] Mood trend chart displays correctly
- [ ] Common topics list shows accurate counts
- [ ] Breakthrough stats calculate correctly
- [ ] Page updates when new sessions analyzed

**Implementation Note**: This phase requires Chart.js library (`npm install chart.js react-chartjs-2`). After automated tests pass, manually verify charts render correctly and data is accurate.

---

## Phase 3: AWS Lambda Deployment (Cost Optimization)

### Overview
Deploy backend to AWS Lambda + API Gateway for serverless cost optimization. Maintain Railway deployment as development/staging environment.

### Changes Required

#### 3.1 Lambda Handler

**File**: `backend/lambda_handler.py` (new file)
**Changes**: Create Lambda entry point using Mangum

```python
"""AWS Lambda handler for FastAPI application"""

from mangum import Mangum
from app.main import app

# Mangum wraps FastAPI for Lambda/API Gateway
handler = Mangum(app, lifespan="off")
```

#### 3.2 Lambda-Specific Configuration

**File**: `backend/app/config.py`
**Changes**: Add Lambda environment detection

```python
# Detect Lambda environment
is_lambda = bool(os.getenv("AWS_LAMBDA_FUNCTION_NAME"))

class Settings(BaseSettings):
    # ... existing settings ...

    # Lambda-specific settings
    lambda_timeout: int = 30  # API Gateway limit
    lambda_memory: int = 1024  # MB

    @property
    def is_lambda_environment(self) -> bool:
        return is_lambda
```

#### 3.3 Deployment Configuration

**File**: `backend/serverless.yml` (new file)
**Changes**: Serverless Framework configuration

```yaml
service: therapybridge-api

provider:
  name: aws
  runtime: python3.13
  region: us-east-1
  timeout: 30
  memorySize: 1024
  environment:
    DATABASE_URL: ${env:DATABASE_URL}
    JWT_SECRET: ${env:JWT_SECRET}
    OPENAI_API_KEY: ${env:OPENAI_API_KEY}
    SUPABASE_URL: ${env:SUPABASE_URL}
    SUPABASE_KEY: ${env:SUPABASE_KEY}

functions:
  api:
    handler: lambda_handler.handler
    events:
      - httpApi: '*'

plugins:
  - serverless-python-requirements

custom:
  pythonRequirements:
    dockerizePip: true
    layer: true
```

#### 3.4 Requirements for Lambda

**File**: `backend/requirements-lambda.txt` (new file)
**Changes**: Lambda-optimized dependencies (exclude dev tools)

```
fastapi==0.104.1
mangum==0.17.0
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
asyncpg==0.29.0
pydantic==2.5.0
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
openai==1.3.7
```

### Success Criteria

#### Automated Verification:
- [ ] Lambda deployment succeeds: `serverless deploy --stage prod`
- [ ] API Gateway endpoint returns health check: `curl https://<api-id>.execute-api.us-east-1.amazonaws.com/health`
- [ ] Lambda function executes under 5 seconds: Check CloudWatch logs
- [ ] Cold start time < 3 seconds

#### Manual Verification:
- [ ] All API endpoints work through API Gateway
- [ ] Database connections stable
- [ ] Demo initialization works on Lambda
- [ ] SSE endpoints stream correctly (if supported by API Gateway)
- [ ] No Lambda timeout errors under normal load

**Implementation Note**: API Gateway v2 supports SSE, but v1 does not. If using v1, disable SSE and rely on polling. Test thoroughly before switching production traffic.

---

## Phase 4: GPU Pipeline Integration (Vast.ai)

### Overview
Integrate Vast.ai GPU instances for faster local transcription using Whisper large-v3 model. Reduces API costs and improves processing speed for long sessions.

### Changes Required

#### 4.1 Vast.ai Instance Configuration

**File**: `audio-transcription-pipeline/scripts/setup_vast_instance.sh` (new file)
**Changes**: Automated setup script for Vast.ai instances

```bash
#!/bin/bash
# Setup script for Vast.ai GPU instances

# Install CUDA and cuDNN
apt-get update
apt-get install -y cuda-toolkit-12-2 libcudnn8

# Install Python 3.13
apt-get install -y python3.13 python3.13-venv python3-pip

# Create venv and install dependencies
python3.13 -m venv /opt/pipeline-venv
source /opt/pipeline-venv/bin/activate
pip install -r requirements-gpu.txt

# Download Whisper model (cache it)
python -c "import whisper; whisper.load_model('large-v3')"

# Start pipeline server
python src/pipeline_server.py
```

#### 4.2 GPU Pipeline Server

**File**: `audio-transcription-pipeline/src/pipeline_server.py` (new file)
**Changes**: HTTP server for receiving transcription jobs

```python
"""GPU Pipeline Server - Runs on Vast.ai instance"""

from fastapi import FastAPI, UploadFile, BackgroundTasks
from src.pipeline_gpu import GPUTranscriptionPipeline
import uvicorn

app = FastAPI()
pipeline = GPUTranscriptionPipeline()

@app.post("/transcribe")
async def transcribe_audio(
    file: UploadFile,
    background_tasks: BackgroundTasks
):
    """Receive audio file and return transcript"""
    # Save uploaded file
    audio_path = f"/tmp/{file.filename}"
    with open(audio_path, "wb") as f:
        f.write(await file.read())

    # Run pipeline
    result = await pipeline.process(audio_path)

    # Cleanup
    background_tasks.add_task(os.remove, audio_path)

    return result

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

#### 4.3 Backend Integration

**File**: `backend/app/services/transcription_service.py` (new file)
**Changes**: Service to route transcription to GPU or API

```python
"""Transcription Service - Routes to GPU or API based on availability"""

import httpx
from app.config import settings

class TranscriptionService:
    def __init__(self):
        self.gpu_endpoint = settings.gpu_pipeline_url
        self.use_gpu = bool(self.gpu_endpoint)

    async def transcribe(self, audio_file_path: str) -> dict:
        """Transcribe audio using GPU pipeline or OpenAI API"""

        if self.use_gpu:
            try:
                return await self._transcribe_gpu(audio_file_path)
            except Exception as e:
                print(f"GPU transcription failed, falling back to API: {e}")
                # Fall through to API

        return await self._transcribe_api(audio_file_path)

    async def _transcribe_gpu(self, audio_file_path: str) -> dict:
        """Send to Vast.ai GPU instance"""
        async with httpx.AsyncClient(timeout=600) as client:
            with open(audio_file_path, "rb") as f:
                response = await client.post(
                    f"{self.gpu_endpoint}/transcribe",
                    files={"file": f}
                )
            return response.json()

    async def _transcribe_api(self, audio_file_path: str) -> dict:
        """Use OpenAI Whisper API"""
        # ... existing API logic ...
```

### Success Criteria

#### Automated Verification:
- [ ] GPU pipeline server starts: `python src/pipeline_server.py`
- [ ] Health check responds: `curl http://vast-instance:8080/health`
- [ ] Test transcription completes: `pytest tests/test_gpu_pipeline.py`
- [ ] Fallback to API works when GPU unavailable

#### Manual Verification:
- [ ] 60-minute audio transcribes in <10 minutes on GPU
- [ ] Diarization accuracy matches API quality
- [ ] Backend correctly routes to GPU when available
- [ ] Costs reduced by 70%+ compared to API-only
- [ ] No quality degradation vs OpenAI API

**Implementation Note**: Vast.ai instances must be manually started before processing jobs. Consider implementing auto-scaling or on-demand instance provisioning for production use.

---

## Testing Strategy

### Unit Tests
- Analytics service aggregation logic
- Lambda handler request/response formatting
- GPU pipeline fallback behavior
- SSE connection retry logic

### Integration Tests
- End-to-end demo initialization → analysis → analytics
- Railway → Lambda traffic routing
- GPU → API failover
- SSE → polling fallback

### Load Tests
- 100 concurrent demo initializations
- 1000 sessions analyzed in parallel
- Analytics queries with 10k+ sessions
- Lambda cold start performance

### Manual Testing Steps
1. Deploy latest code to Railway staging
2. Verify all endpoints respond correctly
3. Test SSE connections for 10+ minutes
4. Load analytics dashboard with real data
5. Deploy to AWS Lambda production
6. Switch 10% traffic to Lambda, monitor for 24 hours
7. If stable, increase to 50%, then 100%
8. Provision Vast.ai GPU instance
9. Process 10 test audio files
10. Verify quality and cost savings

## Performance Considerations

- **Database Connection Pooling**: Use SQLAlchemy pool size 20 for Railway, 5 for Lambda
- **Lambda Cold Starts**: Keep functions warm with CloudWatch cron (every 5 min)
- **GPU Instance Costs**: Vast.ai RTX 4090 = $0.34/hr vs OpenAI API $0.006/min
- **SSE Keep-Alive**: Send ping every 30 seconds to prevent Railway timeout
- **Analytics Caching**: Cache aggregated stats for 1 hour using Redis

## Migration Notes

### Railway → Lambda Migration
1. Deploy Lambda alongside Railway (blue/green)
2. Test all endpoints on Lambda staging
3. Route 10% traffic via weighted DNS
4. Monitor error rates and latency
5. Gradually increase to 100% over 1 week
6. Keep Railway running for 1 month as fallback

### Demo → Production Auth Migration
1. Create new `users` table with proper auth schema
2. Implement JWT auth endpoints
3. Update middleware to support both demo and real auth
4. Migrate demo user data (optional)
5. Disable demo endpoints in production

## References

- Current Railway deployment: https://therabridge-backend.up.railway.app
- Frontend: https://therabridge.up.railway.app
- Neon PostgreSQL: Via SUPABASE_URL env var
- OpenAI Whisper API: https://platform.openai.com/docs/api-reference/audio
- Vast.ai GPU instances: https://vast.ai
- AWS Lambda Python: https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html
