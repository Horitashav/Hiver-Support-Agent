"""
FastAPI Backend — REST API wrapping the AI Support Agent.
"""

import json
import time
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ─── Pydantic Schemas ──────────────────────────────────────────────────

class ProcessRequest(BaseModel):
    message: str = Field(..., description="The customer's support message")
    conversation_history: list[dict] = Field(
        default_factory=list,
        description="Previous messages in the thread [{role, text}]"
    )
    ticket_id: Optional[str] = Field(
        default=None,
        description="Existing ticket ID for follow-ups; null for new tickets"
    )

class IntentResult(BaseModel):
    intent: str
    confidence: float
    reasoning: str

class RetrievedExample(BaseModel):
    customer: str
    brand: str
    similarity: float

class ReplyResult(BaseModel):
    reply: str
    retrieved_examples: list[RetrievedExample] = []
    confidence: float = 0.0
    generated_draft: Optional[str] = None

class EscalationResult(BaseModel):
    escalate: bool
    reason: str
    reasons: list[str] = []
    confidence: float

class ProcessResponse(BaseModel):
    ticket_id: str
    timestamp: str
    intent: IntentResult
    reply: ReplyResult
    escalation: EscalationResult
    auto_handled: bool
    processing_time_ms: float

class OverrideRequest(BaseModel):
    ticket_id: str
    action: str = Field(..., description="'approve' | 'edit' | 'route_human'")
    edited_reply: Optional[str] = None
    agent_notes: Optional[str] = None

class OverrideResponse(BaseModel):
    ticket_id: str
    action: str
    status: str
    timestamp: str

class PresetScenario(BaseModel):
    id: str
    label: str
    category: str
    severity: str  # 'low' | 'medium' | 'high' | 'critical'
    customer_handle: str
    device_info: Optional[str] = None
    message: str
    conversation_history: list[dict] = []

# ─── Application Setup ───────────────────────────────────────────────────

app = FastAPI(
    title="Hiver AI Support Agent API",
    description="REST API for the AI customer support agent pipeline",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for active demo session
agent = None
override_log = []
ticket_store = {}

# ─── Startup Event ────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    global agent
    try:
        from src.agent import SupportAgent
        agent = SupportAgent()
        print("✅ SupportAgent initialized and ready for API traffic")
    except Exception as e:
        print(f"⚠️ Agent failed to load: {e}")

# ─── Preset Scenarios ─────────────────────────────────────────────────────

PRESET_SCENARIOS: list[dict] = [
    {
        "id": "preset_1",
        "label": "🔋 Urgent: Battery Swelling",
        "category": "technical_issue",
        "severity": "critical",
        "customer_handle": "@alex_tech99",
        "device_info": "iPhone 14 Pro, iOS 17.1",
        "message": "My iPhone 14 Pro battery is literally swelling and pushing the screen out. I'm scared it might explode. What do I do?? This phone is only 8 months old!",
        "conversation_history": []
    },
    {
        "id": "preset_2",
        "label": "💳 Billing Dispute",
        "category": "billing_inquiry",
        "severity": "high",
        "customer_handle": "@sarah_m2024",
        "device_info": None,
        "message": "I've been charged $14.99/month for an Apple Music family plan I cancelled THREE months ago. I want a full refund for all 3 months. This is unacceptable.",
        "conversation_history": []
    },
    {
        "id": "preset_3",
        "label": "🔐 Account Locked Out",
        "category": "account_access",
        "severity": "high",
        "customer_handle": "@dev_james_k",
        "device_info": "MacBook Air M2, macOS Sonoma",
        "message": "My Apple ID got locked after someone tried to hack into it. Now I can't access ANY of my devices or iCloud data. I have critical work files in there. Help!!!",
        "conversation_history": []
    },
    {
        "id": "preset_4",
        "label": "📱 Routine How-To",
        "category": "how_to",
        "severity": "low",
        "customer_handle": "@maria_garcia_88",
        "device_info": "iPhone 15, iOS 18",
        "message": "How do I set up Focus modes on my new iPhone 15? I want different notification settings for work and home.",
        "conversation_history": []
    },
    {
        "id": "preset_5",
        "label": "😡 Escalation: Repeated Failures",
        "category": "service_complaint",
        "severity": "critical",
        "customer_handle": "@frustrated_user_x",
        "device_info": "iPad Pro 2022, iPadOS 17",
        "message": "This is my FOURTH time contacting you about the same issue. My iPad randomly shuts down during video calls. I've done every troubleshoot you've suggested. Nothing works. I want a replacement or I'm contacting the BBB and posting this everywhere.",
        "conversation_history": [
            {"role": "customer", "text": "My iPad keeps shutting down during FaceTime calls"},
            {"role": "agent", "text": "We're sorry to hear that. Have you tried restarting your iPad?"},
            {"role": "customer", "text": "Yes I've restarted it 10 times. Still happens."},
            {"role": "agent", "text": "Please try resetting all settings: Settings > General > Reset > Reset All Settings."}
        ]
    },
    {
        "id": "preset_6",
        "label": "📦 Missing Delivery",
        "category": "order_shipping",
        "severity": "medium",
        "customer_handle": "@online_shopper_22",
        "device_info": None,
        "message": "My order says delivered but I never received it. The tracking shows it was left at the front door but nothing was there. Order #W892347123.",
        "conversation_history": []
    },
    {
        "id": "preset_7",
        "label": "🤔 Product Compatibility",
        "category": "product_inquiry",
        "severity": "low",
        "customer_handle": "@new_apple_fan",
        "device_info": None,
        "message": "I'm thinking of buying the Apple Watch Ultra 2. Will it work with my iPhone 11? Also does it support blood oxygen monitoring in India?",
        "conversation_history": []
    },
    {
        "id": "preset_8",
        "label": "🙏 Positive Feedback",
        "category": "other",
        "severity": "low",
        "customer_handle": "@happy_customer_01",
        "device_info": "iPhone 15 Pro Max",
        "message": "Just wanted to say thanks for the amazing support yesterday. The rep helped me recover all my photos after I thought they were lost forever. You guys rock! 🎉",
        "conversation_history": []
    }
]

# ─── Endpoints ─────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy" if agent else "degraded",
        "agent_loaded": agent is not None,
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/api/presets", response_model=list[PresetScenario])
async def get_presets():
    return PRESET_SCENARIOS

@app.post("/api/process", response_model=ProcessResponse)
async def process_message(request: ProcessRequest):
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not loaded. Check server initialization.")
    
    start_time = time.time()
    ticket_id = request.ticket_id or f"TKT-{uuid.uuid4().hex[:8].upper()}"
    
    try:
        result = agent.process(
            message=request.message,
            conversation_history=request.conversation_history or None
        )
        processing_time = (time.time() - start_time) * 1000
        
        response = ProcessResponse(
            ticket_id=ticket_id,
            timestamp=datetime.now().isoformat(),
            intent=IntentResult(
                intent=result['intent'].get('intent', 'other'),
                confidence=result['intent'].get('confidence', 0.0),
                reasoning=result['intent'].get('reasoning', '')
            ),
            reply=ReplyResult(
                reply=result['reply'].get('reply', ''),
                retrieved_examples=[
                    RetrievedExample(
                        customer=ex.get('customer', ''),
                        brand=ex.get('brand', ''),
                        similarity=ex.get('similarity', 0.0)
                    )
                    for ex in result['reply'].get('retrieved_examples', [])
                ],
                confidence=result['reply'].get('confidence', 0.0),
                generated_draft=result['reply'].get('generated_draft')
            ),
            escalation=EscalationResult(
                escalate=result['escalation'].get('escalate', False),
                reason=result['escalation'].get('reason', ''),
                reasons=result['escalation'].get('reasons', []),
                confidence=result['escalation'].get('confidence', 0.0)
            ),
            auto_handled=result.get('auto_handled', True),
            processing_time_ms=round(processing_time, 2)
        )
        
        ticket_store[ticket_id] = {
            "request": request.model_dump(),
            "response": response.model_dump(),
            "overrides": []
        }
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

@app.post("/api/override", response_model=OverrideResponse)
async def log_override(request: OverrideRequest):
    if request.ticket_id not in ticket_store:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    override_entry = {
        "ticket_id": request.ticket_id,
        "action": request.action,
        "edited_reply": request.edited_reply,
        "agent_notes": request.agent_notes,
        "timestamp": datetime.now().isoformat()
    }
    ticket_store[request.ticket_id]["overrides"].append(override_entry)
    override_log.append(override_entry)
    
    return OverrideResponse(
        ticket_id=request.ticket_id,
        action=request.action,
        status="logged",
        timestamp=datetime.now().isoformat()
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)