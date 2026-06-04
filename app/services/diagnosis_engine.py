import os
import json
import datetime
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.models.models import Diagnosis, DiagnosisDimension, Roadmap, RoadmapItem
from app.schemas.schemas import DiagnosisCreate

# Keys from env
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if GEMINI_API_KEY:
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)

if OPENAI_API_KEY:
    from openai import OpenAI
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

def generate_diagnosis_recommendations_and_roadmap(
    db: Session,
    workspace_id: int,
    organization_id: int,
    user_id: int,
    diag_data: DiagnosisCreate
) -> Diagnosis:
    """
    Analyzes 360 dimensions, updates database with recommendations, FODA/SWOT, and
    spawns a 30/60/90 execution roadmap with action items.
    """
    # 1. Create Diagnosis Record
    diagnosis = Diagnosis(
        workspace_id=workspace_id,
        organization_id=organization_id,
        user_id=user_id,
        status="COMPLETED"
    )
    db.add(diagnosis)
    db.flush()  # gets the diagnosis ID

    # Prepare input text for LLM if we call it
    input_summary = []
    for dim in diag_data.dimensions:
        input_summary.append({
            "dimension": dim.name,
            "rating": dim.rating,
            "user_findings": dim.findings,
            "challenges": dim.challenges
        })
        
    # We will generate recommendations, SWOT and roadmap items
    generated_data = {}
    
    # Check if we can use an LLM
    llm_available = bool(OPENAI_API_KEY or GEMINI_API_KEY)
    
    if llm_available:
        prompt = (
            "You are a Senior Business Consultant. Analyze the following 360 business questionnaire inputs and generate:\n"
            "1. Recommendations for each business dimension.\n"
            "2. SWOT/FODA factors (strengths, weaknesses, opportunities, threats) for each dimension.\n"
            "3. Action items for a 30/60/90-day roadmap. Each action item must have a title, description, dimension, and phase (30, 60, or 90).\n\n"
            f"Input questionnaire data:\n{json.dumps(input_summary, indent=2)}\n\n"
            "You MUST respond ONLY with a JSON object of the following format. Ensure valid JSON:\n"
            "{\n"
            "  \"dimensions\": [\n"
            "    {\n"
            "      \"name\": \"Ventas\", // Must match input dimension name\n"
            "      \"recommendations\": \"recommendation text...\",\n"
            "      \"swot\": {\n"
            "        \"strengths\": [\"factor 1\", \"factor 2\"],\n"
            "        \"weaknesses\": [\"factor 1\", \"factor 2\"],\n"
            "        \"opportunities\": [\"factor 1\", \"factor 2\"],\n"
            "        \"threats\": [\"factor 1\", \"factor 2\"]\n"
            "      }\n"
            "    }\n"
            "  ],\n"
            "  \"roadmap\": [\n"
            "    {\n"
            "      \"title\": \"Action item title\",\n"
            "      \"description\": \"Action item description\",\n"
            "      \"dimension\": \"Ventas\", // Must match dimension name\n"
            "      \"phase\": 30 // Must be 30, 60, or 90\n"
            "    }\n"
            "  ]\n"
            "}"
        )
        
        try:
            raw_response = ""
            if OPENAI_API_KEY:
                response = openai_client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    response_format={"type": "json_object"}
                )
                raw_response = response.choices[0].message.content
            elif GEMINI_API_KEY:
                model = genai.GenerativeModel(model_name="gemini-1.5-flash")
                response = model.generate_content(
                    prompt,
                    generation_config={"response_mime_type": "application/json", "temperature": 0.3}
                )
                raw_response = response.text
                
            generated_data = json.loads(raw_response)
        except Exception as e:
            print(f"Error calling LLM for diagnosis: {e}")
            generated_data = {}

    # If LLM failed or not available, use fallback rule-based template generator
    if not generated_data:
        generated_data = generate_fallback_diagnosis(input_summary)

    # 2. Add DiagnosisDimensions to database
    roadmap_items_to_create = generated_data.get("roadmap", [])
    
    for dim_data in diag_data.dimensions:
        # Find matching recommendations and SWOT from generated data
        matching_gen = next((d for d in generated_data.get("dimensions", []) if d["name"] == dim_data.name), None)
        
        recs = matching_gen.get("recommendations", f"Implement standard optimization strategies for {dim_data.name}.") if matching_gen else f"Enhance monitoring for {dim_data.name} processes."
        swot = matching_gen.get("swot", {
            "strengths": ["Documented core practices"],
            "weaknesses": ["Manual controls and tracking gaps"],
            "opportunities": ["IA automation and process integration"],
            "threats": ["Operational friction and resource limitations"]
        }) if matching_gen else {
            "strengths": ["Clear focus on core activities"],
            "weaknesses": ["Dependency on manual efforts"],
            "opportunities": ["Digital tool onboarding"],
            "threats": ["Competitive disruption"]
        }
        
        dim_record = DiagnosisDimension(
            diagnosis_id=diagnosis.id,
            name=dim_data.name,
            rating=dim_data.rating,
            findings=dim_data.findings + f" | User-specified Challenges: {dim_data.challenges}",
            recommendations=recs,
            swot_analysis=swot
        )
        db.add(dim_record)

    # 3. Create Roadmap and items
    roadmap = Roadmap(
        workspace_id=workspace_id,
        organization_id=organization_id,
        diagnosis_id=diagnosis.id
    )
    db.add(roadmap)
    db.flush()

    for item in roadmap_items_to_create:
        roadmap_item = RoadmapItem(
            roadmap_id=roadmap.id,
            title=item.get("title", "Initiate Strategic Review"),
            description=item.get("description", "Evaluate current operational workflows."),
            dimension=item.get("dimension", "Operations"),
            phase=item.get("phase", 30),
            status="TODO",
            due_date=datetime.date.today() + datetime.timedelta(days=int(item.get("phase", 30)))
        )
        db.add(roadmap_item)

    db.commit()
    db.refresh(diagnosis)
    return diagnosis


def generate_fallback_diagnosis(inputs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate highly structured business advisory templates and SWOT matrices based
    on dimension rating levels.
    """
    dimensions_out = []
    roadmap_out = []
    
    # Generic dimension mapping advice
    consulting_templates = {
        "Ventas": {
            "low": {
                "recs": "Configure a standardized sales pipeline, implement basic CRM tracking (Hubspot/Pipedrive), and define core conversion metrics.",
                "swot": {
                    "strengths": ["Agile product or service adjustments", "Direct founder-client communication"],
                    "weaknesses": ["No formal CRM pipeline", "Inconsistent lead generation"],
                    "opportunities": ["Implement outbound email marketing automation", "Optimize social proof and case studies"],
                    "threats": ["Competitors with faster sales cycle", "High churn due to misaligned expectations"]
                },
                "tasks": [
                    {"title": "CRM Setup & Configuration", "description": "Deploy a CRM tool to map deal stages.", "phase": 30},
                    {"title": "Sales Pitch Scripting", "description": "Standardize the sales message for lead qualifiers.", "phase": 60},
                    {"title": "Referral Program Launch", "description": "Incentivize existing clients to refer new prospects.", "phase": 90}
                ]
            },
            "high": {
                "recs": "Introduce client segmentation, advanced performance dashboards, and automated lead scoring mechanisms.",
                "swot": {
                    "strengths": ["Robust and predictable client acquisition", "Cohesive sales rep onboarding"],
                    "weaknesses": ["Under-utilized cross-selling techniques", "Data silos between marketing and sales"],
                    "opportunities": ["Deploy predictive lead qualification models", "Launch corporate upsell campaigns"],
                    "threats": ["Market saturation", "Key personnel dependency"]
                },
                "tasks": [
                    {"title": "Pipeline Analytics Dashboard", "description": "Consolidate sales conversion ratios.", "phase": 30},
                    {"title": "Sales Playbook Automation", "description": "Integrate auto-responses for inactive leads.", "phase": 60},
                    {"title": "Key Account Review", "description": "Execute quarterly audits on top-tier clients.", "phase": 90}
                ]
            }
        },
        "Operaciones": {
            "low": {
                "recs": "Document critical workflows, reduce reliance on manual spreadsheets, and assign clear responsibilities.",
                "swot": {
                    "strengths": ["High flexibility to implement custom requirements", "Strong dedication from team"],
                    "weaknesses": ["Lack of written standard operating procedures (SOPs)", "Operational bottlenecks in delivery"],
                    "opportunities": ["Create digital training guides for onboarding", "Integrate automated workflows via Zapier"],
                    "threats": ["Critical operational failures during scaling", "Knowledge loss if key members leave"]
                },
                "tasks": [
                    {"title": "Operational Flow Mapping", "description": "Diagram core delivery steps to detect friction.", "phase": 30},
                    {"title": "SOP Documentation (Top 3)", "description": "Write manuals for the three most common tasks.", "phase": 60},
                    {"title": "Workflow Automation Run", "description": "Connect operational intake forms to project boards.", "phase": 90}
                ]
            },
            "high": {
                "recs": "Refine operational capacity models, carry out vendor reviews, and establish quality control loops.",
                "swot": {
                    "strengths": ["Optimized throughput and fast turnaround", "Structured quality checks"],
                    "weaknesses": ["Diminishing returns on legacy infrastructure", "Over-engineered workflows"],
                    "opportunities": ["Onboard AI-powered process copilots", "Optimize supply chain pricing structures"],
                    "threats": ["Compliance changes", "Supplier dependencies"]
                },
                "tasks": [
                    {"title": "Capacity Utilization Audit", "description": "Assess peak load operational capacity.", "phase": 30},
                    {"title": "AI Integration Pilot", "description": "Test automated triage for operation tickets.", "phase": 60},
                    {"title": "Process Redundancy Cut", "description": "Remove duplicate verification steps in flow.", "phase": 90}
                ]
            }
        },
        "Administracion": {
            "low": {
                "recs": "Implement strict cash flow forecasting, categorize spending, and automate invoice tracking.",
                "swot": {
                    "strengths": ["Low overhead costs", "Minimal bureaucracy"],
                    "weaknesses": ["Unpredictable cash flow visibility", "Late client collections"],
                    "opportunities": ["Implement payment reminders", "Move to digital cloud accounting software"],
                    "threats": ["Working capital shortage", "Compliance/tax audit risks"]
                },
                "tasks": [
                    {"title": "Cash Flow Forecast Chart", "description": "Build a rolling 12-week cash flow model.", "phase": 30},
                    {"title": "Invoicing & Collection Automation", "description": "Establish auto-alerts for overdue receipts.", "phase": 60},
                    {"title": "Vendor Audits", "description": "Negotiate payment terms with top suppliers.", "phase": 90}
                ]
            },
            "high": {
                "recs": "Perform cost-benefit analyses on overhead, setup tax optimization strategies, and build unit economic models.",
                "swot": {
                    "strengths": ["Strong balance sheet stability", "Accurate budgets"],
                    "weaknesses": ["Complex corporate reporting structures", "Slow budget approvals"],
                    "opportunities": ["Investment of surplus capital", "Automated procurement systems"],
                    "threats": ["Currency rate fluctuations", "Regulatory changes"]
                },
                "tasks": [
                    {"title": "Unit Economics Model Review", "description": "Analyze margins per client category.", "phase": 30},
                    {"title": "Corporate Budget Allocation", "description": "Establish departmental budgets for next year.", "phase": 60},
                    {"title": "Compliance & Audit Check", "description": "Review regulatory compliance files.", "phase": 90}
                ]
            }
        },
        "Recursos Humanos": {
            "low": {
                "recs": "Define role profiles, initiate structured performance evaluations, and write a basic onboarding manual.",
                "swot": {
                    "strengths": ["High alignment with founder vision", "Tight-knit culture"],
                    "weaknesses": ["High burnout risk", "No clear progression paths"],
                    "opportunities": ["Implement feedback review cycles", "Offer virtual training resources"],
                    "threats": ["Key talent departures", "Culture dilution as head count grows"]
                },
                "tasks": [
                    {"title": "Org Chart & Role Clarity", "description": "Document responsibilities for every role.", "phase": 30},
                    {"title": "Performance Evaluation Draft", "description": "Introduce mid-year reviews.", "phase": 60},
                    {"title": "Employee Handbook Release", "description": "Publish cultural and operational guidelines.", "phase": 90}
                ]
            },
            "high": {
                "recs": "Foster leadership development programs, optimize compensation structures, and introduce employee Net Promoter Scores (eNPS).",
                "swot": {
                    "strengths": ["Attractive talent brand", "Clear career ladders"],
                    "weaknesses": ["Internal silos between business units", "Slow hiring cycles"],
                    "opportunities": ["Remote-first global hiring", "Mentorship programs"],
                    "threats": ["Intense market competition for talent", "Rising salary expectations"]
                },
                "tasks": [
                    {"title": "eNPS & Engagement Survey", "description": "Gather anonymous organizational feedback.", "phase": 30},
                    {"title": "Leadership Coaching Track", "description": "Deliver management modules to directors.", "phase": 60},
                    {"title": "Compensation Benchmarking", "description": "Align salaries with market data.", "phase": 90}
                ]
            }
        },
        "Tecnologia": {
            "low": {
                "recs": "Consolidate cloud software tools to eliminate redundancies, standardize logins, and create data backups.",
                "swot": {
                    "strengths": ["Low technical debt", "Flexibility to choose modern systems"],
                    "weaknesses": ["Siloed software tools", "Lack of cybersecurity protocols"],
                    "opportunities": ["Adopt centralized cloud directories", "Integrate databases with visual dashboards"],
                    "threats": ["Security breach or data loss", "Interrupted service during critical outages"]
                },
                "tasks": [
                    {"title": "Software Asset Audit", "description": "List all tools and users to cut duplicate seats.", "phase": 30},
                    {"title": "Password & Security Standard", "description": "Deploy a password manager for teams.", "phase": 60},
                    {"title": "Backup & Disaster Recovery Plan", "description": "Configure automatic database backups.", "phase": 90}
                ]
            },
            "high": {
                "recs": "Assess AI utility integrations, migrate legacy systems to microservices, and setup vulnerability testing.",
                "swot": {
                    "strengths": ["Modern microservices architecture", "Automated test coverage"],
                    "weaknesses": ["High maintenance cost for custom builds", "Tech stack complexity"],
                    "opportunities": ["Automate support with fine-tuned agents", "Expose developer APIs for partner tools"],
                    "threats": ["Rapid tech obsolescence", "Target for cyber attacks"]
                },
                "tasks": [
                    {"title": "AI Assistant Sandbox Test", "description": "Deploy internal LLM playground for staff.", "phase": 30},
                    {"title": "API Gateway Configuration", "description": "Standardize system integrations.", "phase": 60},
                    {"title": "Penetration Testing Run", "description": "Run external security scan.", "phase": 90}
                ]
            }
        }
    }

    # Evaluate each input dimension and compile output
    for item in inputs:
        name = item["dimension"]
        rating = item["rating"]
        
        # Use template database based on low (<=3) or high (>=4) ratings
        level = "low" if rating <= 3 else "high"
        
        # Get fallback default if dimension code name doesn't match keys
        template = consulting_templates.get(name, consulting_templates["Operaciones"])[level]
        
        dimensions_out.append({
            "name": name,
            "recommendations": template["recs"],
            "swot": template["swot"]
        })
        
        # Build tasks list
        for t in template["tasks"]:
            roadmap_out.append({
                "title": f"[{name}] {t['title']}",
                "description": t["description"] + f" (Based on rating: {rating}/5)",
                "dimension": name,
                "phase": t["phase"]
            })
            
    return {
        "dimensions": dimensions_out,
        "roadmap": roadmap_out
    }
