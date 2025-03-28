"""
FastAPI-powered API for Continuum Digital Twin.
This module provides RESTful API access to the ad platform simulators.
"""

import os
import json
import asyncio
import uuid
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from enum import Enum

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Header, BackgroundTasks, Query, Path, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator, SecretStr
from contextlib import asynccontextmanager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import simulator components
try:
    from ad_simulator import AdSimulator
    from google import GoogleAdsSimulator
    from facebook import FacebookAdsSimulator
    from linkedin import LinkedInAdsSimulator
except ImportError as e:
    logger.error(f"Failed to import simulator components: {e}")
    # Create placeholders if imports fail
    AdSimulator = None
    GoogleAdsSimulator = None
    FacebookAdsSimulator = None
    LinkedInAdsSimulator = None

# Initialize FastAPI app with documentation config
app = FastAPI(
    title="Continuum Digital Twin API",
    description="API for simulating ad campaigns across multiple platforms",
    version="1.0.0",
    # Additional configuration for documentation
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize simulator instances (one per user session in production)
simulators = {}

# Pydantic models for request/response
class Platform(str, Enum):
    """Supported ad platforms."""
    GOOGLE = "google"
    FACEBOOK = "facebook"
    LINKEDIN = "linkedin"
    ALL = "all"

class CampaignObjective(str, Enum):
    """Campaign objectives."""
    AWARENESS = "awareness"
    CONSIDERATION = "consideration"
    CONVERSION = "conversion"
    TRAFFIC = "traffic"
    ENGAGEMENT = "engagement"
    LEAD_GENERATION = "lead_generation"
    APP_INSTALLS = "app_installs"
    VIDEO_VIEWS = "video_views"

class BidStrategy(str, Enum):
    """Bidding strategies."""
    LOWEST_COST = "lowest_cost"
    COST_CAP = "cost_cap"
    BID_CAP = "bid_cap"
    TARGET_CPA = "target_cpa"
    TARGET_ROAS = "target_roas"

class AudienceData(BaseModel):
    """Audience configuration."""
    size: int = Field(..., ge=1000, description="Size of the audience")
    ctr_base: float = Field(..., ge=0.001, le=0.1, description="Base click-through rate")
    conversion_rate: float = Field(..., ge=0.001, le=0.1, description="Conversion rate")
    demographics_match: Optional[float] = Field(0.7, ge=0.1, le=1.0, description="Demographic match score")
    interests_match: Optional[float] = Field(0.6, ge=0.1, le=1.0, description="Interests match score")
    behaviors_match: Optional[float] = Field(0.5, ge=0.1, le=1.0, description="Behaviors match score")

class TargetingData(BaseModel):
    """Campaign targeting configuration."""
    audience: str = Field(..., description="Name of the audience to target")
    location: Optional[List[str]] = Field(None, description="List of locations to target")
    age_range: Optional[Dict[str, int]] = Field(None, description="Age range to target (min, max)")
    gender: Optional[str] = Field(None, description="Gender to target")
    interests: Optional[List[str]] = Field(None, description="List of interests to target")
    behaviors: Optional[List[str]] = Field(None, description="List of behaviors to target")

class CampaignData(BaseModel):
    """Campaign configuration."""
    name: str = Field(..., min_length=3, max_length=100, description="Campaign name")
    objective: CampaignObjective
    daily_budget: float = Field(..., gt=0, description="Daily budget in USD")
    total_budget: Optional[float] = Field(None, gt=0, description="Total budget in USD")
    bid_strategy: Optional[BidStrategy] = Field(None, description="Bidding strategy")
    targeting: TargetingData
    start_date: Optional[datetime] = Field(None, description="Campaign start date")
    end_date: Optional[datetime] = Field(None, description="Campaign end date")

class GoogleAdGroupData(BaseModel):
    """Google Ads ad group configuration."""
    name: str = Field(..., min_length=3, max_length=100, description="Ad group name")
    ad_format: str = Field("search", description="Ad format")
    
class GoogleKeywordData(BaseModel):
    """Google Ads keyword configuration."""
    text: str = Field(..., min_length=1, description="Keyword text")
    match_type: str = Field("exact", description="Match type (exact, phrase, broad)")
    bid: float = Field(1.0, gt=0, description="Bid amount")

class GoogleAdData(BaseModel):
    """Google Ads ad configuration."""
    headline1: str = Field(..., min_length=1, max_length=30, description="Headline 1")
    headline2: str = Field(..., min_length=1, max_length=30, description="Headline 2")
    description: str = Field(..., min_length=1, max_length=90, description="Description") 

class FacebookAdSetData(BaseModel):
    """Facebook ad set configuration."""
    name: str = Field(..., min_length=3, max_length=100, description="Ad set name")
    budget: float = Field(..., gt=0, description="Ad set budget in USD")
    placements: List[str] = Field(["feed"], description="Ad placements")
    targeting: Optional[Dict[str, Any]] = Field(None, description="Detailed targeting options")

class FacebookAdData(BaseModel):
    """Facebook ad configuration."""
    title: str = Field(..., min_length=1, max_length=40, description="Ad title")
    body: str = Field(..., min_length=1, max_length=125, description="Ad body text")
    image_url: Optional[str] = Field(None, description="Image URL")
    call_to_action: Optional[str] = Field(None, description="Call to action button text")

class LinkedInCreativeData(BaseModel):
    """LinkedIn creative configuration."""
    title: str = Field(..., min_length=1, max_length=100, description="Creative title")
    body: str = Field(..., min_length=1, max_length=600, description="Creative body text")
    destination_url: Optional[str] = Field(None, description="Destination URL")
    call_to_action: Optional[str] = Field(None, description="Call to action")

class SimulationRequest(BaseModel):
    """Simulation request configuration."""
    days: int = Field(30, ge=1, le=365, description="Number of days to simulate")
    platforms: List[Platform] = Field([Platform.ALL], description="Platforms to simulate")
    speed_factor: Optional[float] = Field(1.0, gt=0, description="Simulation speed factor")
    export_results: Optional[bool] = Field(False, description="Whether to export results")
    
class SimulationStatus(str, Enum):
    """Simulation status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class SimulationResponse(BaseModel):
    """Simulation response."""
    simulation_id: str
    status: SimulationStatus
    platforms: List[Platform]
    days: int
    start_time: datetime
    end_time: Optional[datetime] = None
    results_url: Optional[str] = None

class SimulationResultSummary(BaseModel):
    """Summary of simulation results."""
    impressions: int
    clicks: int
    conversions: int
    spend: float
    ctr: float
    cpa: float

class PlatformResultSummary(BaseModel):
    """Platform-specific result summary."""
    impressions: int
    clicks: int
    conversions: int
    spend: float
    ctr: float
    cpa: float
    
class SimulationResults(BaseModel):
    """Complete simulation results."""
    simulation_id: str
    overall: SimulationResultSummary
    platforms: Dict[Platform, PlatformResultSummary]
    campaigns: Dict[str, Any]
    detailed_metrics: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    """Error response model."""
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

# Simulator management
def get_simulator(user_id: str = "default"):
    """Get or create a simulator for a user."""
    if user_id not in simulators:
        if AdSimulator is None:
            raise HTTPException(
                status_code=500,
                detail="Simulator components not available"
            )
        simulators[user_id] = AdSimulator()
    return simulators[user_id]

def create_audiences(simulator: AdSimulator, audiences: Dict[str, AudienceData]):
    """Create audiences in the simulator."""
    for name, data in audiences.items():
        simulator.google_simulator.define_audience(name, data.dict())
        simulator.facebook_simulator.define_audience(name, data.dict())
        simulator.linkedin_simulator.define_audience(name, data.dict())

# API routes
@app.post("/audiences", status_code=201)
async def create_audience(audience_data: Dict[str, AudienceData]):
    """Create an audience for simulation."""
    simulator = get_simulator()
    create_audiences(simulator, audience_data)
    return {"message": f"Created {len(audience_data)} audiences", "audiences": list(audience_data.keys())}

@app.post("/campaigns/google", status_code=201)
async def create_google_campaign(campaign_data: CampaignData):
    """Create a Google Ads campaign."""
    simulator = get_simulator()
    
    # Map objective to Google format
    objective_mapping = {
        "awareness": "DISPLAY",
        "consideration": "SEARCH",
        "conversion": "CONVERSION",
        "traffic": "SEARCH",
        "engagement": "DISPLAY",
        "lead_generation": "CONVERSION",
        "app_installs": "APP",
        "video_views": "VIDEO"
    }
    
    google_campaign = {
        "name": campaign_data.name,
        "objective": objective_mapping.get(campaign_data.objective, "CONVERSION"),
        "daily_budget": campaign_data.daily_budget,
        "targeting": campaign_data.targeting.dict()
    }
    
    if campaign_data.total_budget:
        google_campaign["total_budget"] = campaign_data.total_budget
    
    campaign_id = simulator.google_simulator.create_campaign(google_campaign)
    return {
        "campaign_id": campaign_id,
        "platform": "google",
        "message": f"Created Google campaign: {campaign_data.name}"
    }

@app.post("/campaigns/google/{campaign_id}/adgroups", status_code=201)
async def create_google_ad_group(
    campaign_id: str,
    ad_group_data: GoogleAdGroupData
):
    """Create a Google Ads ad group."""
    simulator = get_simulator()
    ad_group_id = simulator.google_simulator.create_ad_group(campaign_id, ad_group_data.dict())
    return {
        "ad_group_id": ad_group_id,
        "campaign_id": campaign_id,
        "message": f"Created Google ad group: {ad_group_data.name}"
    }

@app.post("/campaigns/google/adgroups/{ad_group_id}/keywords", status_code=201)
async def add_google_keywords(
    ad_group_id: str,
    keyword_data: GoogleKeywordData
):
    """Add a keyword to a Google Ads ad group."""
    simulator = get_simulator()
    keyword_id = simulator.google_simulator.add_keyword(
        ad_group_id, 
        keyword_data.text, 
        keyword_data.match_type, 
        keyword_data.bid
    )
    return {
        "keyword_id": keyword_id,
        "ad_group_id": ad_group_id,
        "message": f"Added keyword: {keyword_data.text}"
    }

@app.post("/campaigns/google/adgroups/{ad_group_id}/ads", status_code=201)
async def create_google_ad(
    ad_group_id: str,
    ad_data: GoogleAdData
):
    """Create a Google ad."""
    simulator = get_simulator()
    ad_id = simulator.google_simulator.create_ad(ad_group_id, ad_data.dict())
    return {
        "ad_id": ad_id,
        "ad_group_id": ad_group_id,
        "message": f"Created Google ad with headline: {ad_data.headline1}"
    }

@app.post("/campaigns/facebook", status_code=201)
async def create_facebook_campaign(campaign_data: CampaignData):
    """Create a Facebook Ads campaign."""
    simulator = get_simulator()
    
    # Map objective to Facebook format
    objective_mapping = {
        "awareness": "BRAND_AWARENESS",
        "consideration": "TRAFFIC",
        "conversion": "CONVERSIONS",
        "traffic": "TRAFFIC",
        "engagement": "ENGAGEMENT",
        "lead_generation": "LEAD_GENERATION",
        "app_installs": "APP_INSTALLS",
        "video_views": "VIDEO_VIEWS"
    }
    
    facebook_campaign = {
        "name": campaign_data.name,
        "objective": objective_mapping.get(campaign_data.objective, "CONVERSIONS"),
        "budget": campaign_data.daily_budget * 30,  # Convert to monthly budget
        "targeting": campaign_data.targeting.dict()
    }
    
    campaign_id = simulator.facebook_simulator.create_campaign(facebook_campaign)
    return {
        "campaign_id": campaign_id,
        "platform": "facebook",
        "message": f"Created Facebook campaign: {campaign_data.name}"
    }

@app.post("/campaigns/facebook/{campaign_id}/adsets", status_code=201)
async def create_facebook_ad_set(
    campaign_id: str,
    ad_set_data: FacebookAdSetData
):
    """Create a Facebook ad set."""
    simulator = get_simulator()
    ad_set_id = simulator.facebook_simulator.create_ad_set(campaign_id, ad_set_data.dict())
    return {
        "ad_set_id": ad_set_id,
        "campaign_id": campaign_id,
        "message": f"Created Facebook ad set: {ad_set_data.name}"
    }

@app.post("/campaigns/facebook/adsets/{ad_set_id}/ads", status_code=201)
async def create_facebook_ad(
    ad_set_id: str,
    ad_data: FacebookAdData
):
    """Create a Facebook ad."""
    simulator = get_simulator()
    ad_id = simulator.facebook_simulator.create_ad(ad_set_id, ad_data.dict())
    return {
        "ad_id": ad_id,
        "ad_set_id": ad_set_id,
        "message": f"Created Facebook ad with title: {ad_data.title}"
    }

@app.post("/campaigns/linkedin", status_code=201)
async def create_linkedin_campaign(campaign_data: CampaignData):
    """Create a LinkedIn Ads campaign."""
    simulator = get_simulator()
    
    # Map objective to LinkedIn format
    objective_mapping = {
        "awareness": "BRAND_AWARENESS",
        "consideration": "WEBSITE_VISITS",
        "conversion": "WEBSITE_CONVERSIONS",
        "traffic": "WEBSITE_VISITS",
        "engagement": "ENGAGEMENT",
        "lead_generation": "LEAD_GENERATION",
        "video_views": "VIDEO_VIEWS",
    }
    
    linkedin_campaign = {
        "name": campaign_data.name,
        "objective": objective_mapping.get(campaign_data.objective, "WEBSITE_CONVERSIONS"),
        "type": "sponsored_content",
        "daily_budget": campaign_data.daily_budget,
        "total_budget": campaign_data.total_budget if campaign_data.total_budget else campaign_data.daily_budget * 30,
        "targeting": campaign_data.targeting.dict()
    }
    
    campaign_id = simulator.linkedin_simulator.create_campaign(linkedin_campaign)
    return {
        "campaign_id": campaign_id,
        "platform": "linkedin",
        "message": f"Created LinkedIn campaign: {campaign_data.name}"
    }

@app.post("/campaigns/linkedin/{campaign_id}/creatives", status_code=201)
async def create_linkedin_creative(
    campaign_id: str,
    creative_data: LinkedInCreativeData
):
    """Create a LinkedIn creative."""
    simulator = get_simulator()
    creative_id = simulator.linkedin_simulator.create_creative(campaign_id, creative_data.dict())
    return {
        "creative_id": creative_id,
        "campaign_id": campaign_id,
        "message": f"Created LinkedIn creative with title: {creative_data.title}"
    }

@app.post("/campaigns/crossplatform", status_code=201)
async def create_cross_platform_campaign(
    campaign_data: CampaignData,
    platforms: List[Platform] = Query([Platform.ALL])
):
    """Create a campaign across multiple platforms."""
    simulator = get_simulator()
    
    # Convert Platform enum to strings
    platform_list = []
    if Platform.ALL in platforms:
        platform_list = ["google", "facebook", "linkedin"]
    else:
        for platform in platforms:
            if platform != Platform.ALL:
                platform_list.append(platform)
    
    # Create the base campaign data
    cross_platform_data = {
        "name": campaign_data.name,
        "objective": campaign_data.objective,
        "daily_budget": campaign_data.daily_budget,
        "total_budget": campaign_data.total_budget,
        "targeting": campaign_data.targeting.dict()
    }
    
    # Create the campaign across platforms
    campaign_ids = simulator.create_cross_platform_campaign(cross_platform_data, platform_list)
    
    return {
        "campaign_ids": campaign_ids,
        "platforms": platform_list,
        "message": f"Created campaign across {len(campaign_ids)} platforms: {campaign_data.name}"
    }

@app.post("/simulations", response_model=SimulationResponse)
async def run_simulation(
    simulation_req: SimulationRequest,
    background_tasks: BackgroundTasks
):
    """Run a simulation."""
    simulator = get_simulator()
    
    # Generate a unique ID for this simulation
    simulation_id = f"sim-{str(uuid.uuid4())[:8]}"
    
    # Convert Platform enum to strings
    platform_list = []
    if Platform.ALL in simulation_req.platforms:
        platform_list = ["google", "facebook", "linkedin"]
    else:
        for platform in simulation_req.platforms:
            if platform != Platform.ALL:
                platform_list.append(platform)
    
    # Create a response object
    response = SimulationResponse(
        simulation_id=simulation_id,
        status=SimulationStatus.PENDING,
        platforms=simulation_req.platforms,
        days=simulation_req.days,
        start_time=datetime.now()
    )
    
    # Add the simulation to a background task
    background_tasks.add_task(
        run_simulation_task, 
        simulator,
        simulation_id,
        simulation_req.days,
        platform_list,
        simulation_req.speed_factor,
        simulation_req.export_results,
        "default"  # Default user ID
    )
    
    return response

async def run_simulation_task(
    simulator: AdSimulator,
    simulation_id: str,
    days: int,
    platforms: List[str],
    speed_factor: float,
    export_results: bool,
    user_id: str
):
    """Run a simulation in the background."""
    try:
        # Create a 'simulations' directory if it doesn't exist
        simulations_dir = os.path.join("results", "simulations", user_id)
        os.makedirs(simulations_dir, exist_ok=True)
        
        # Update simulation status to running
        result_path = os.path.join(simulations_dir, f"{simulation_id}_status.json")
        with open(result_path, "w") as f:
            json.dump({
                "simulation_id": simulation_id,
                "status": SimulationStatus.RUNNING,
                "start_time": datetime.now().isoformat(),
                "platforms": platforms,
                "days": days
            }, f)
        
        # Run the simulation
        results = simulator.run_campaigns(days=days, platforms=platforms)
        
        # Export results if requested
        if export_results:
            export_path = os.path.join(simulations_dir, simulation_id)
            simulator.export_results(output_dir=export_path)
            results_url = f"/simulations/{user_id}/{simulation_id}"
        else:
            results_url = None
        
        # Save the results
        result_path = os.path.join(simulations_dir, f"{simulation_id}_results.json")
        with open(result_path, "w") as f:
            # Convert the numerical results to JSON
            json_results = {}
            for platform, platform_results in results.items():
                json_results[platform] = {}
                for key, value in platform_results.items():
                    if isinstance(value, dict):
                        json_results[platform][key] = {}
                        for k, v in value.items():
                            if hasattr(v, 'tolist'):  # For numpy arrays
                                json_results[platform][key][k] = v.tolist()
                            else:
                                json_results[platform][key][k] = v
                    elif hasattr(value, 'tolist'):  # For numpy arrays
                        json_results[platform][key] = value.tolist()
                    else:
                        json_results[platform][key] = value
                        
            json.dump(json_results, f, default=str)
        
        # Update simulation status to completed
        status_path = os.path.join(simulations_dir, f"{simulation_id}_status.json")
        with open(status_path, "w") as f:
            json.dump({
                "simulation_id": simulation_id,
                "status": SimulationStatus.COMPLETED,
                "start_time": datetime.now().isoformat(),
                "end_time": datetime.now().isoformat(),
                "platforms": platforms,
                "days": days,
                "results_url": results_url
            }, f)
    
    except Exception as e:
        # Update simulation status to failed
        error_path = os.path.join(simulations_dir, f"{simulation_id}_error.json")
        with open(error_path, "w") as f:
            json.dump({
                "simulation_id": simulation_id,
                "status": SimulationStatus.FAILED,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }, f)

@app.get("/simulations/{simulation_id}/status", response_model=SimulationResponse)
async def get_simulation_status(simulation_id: str):
    """Get the status of a simulation."""
    user_id = "default"  # Use default user ID
    simulations_dir = os.path.join("results", "simulations", user_id)
    status_path = os.path.join(simulations_dir, f"{simulation_id}_status.json")
    
    if not os.path.exists(status_path):
        error_path = os.path.join(simulations_dir, f"{simulation_id}_error.json")
        if os.path.exists(error_path):
            with open(error_path, "r") as f:
                error_data = json.load(f)
                raise HTTPException(
                    status_code=500,
                    detail=f"Simulation failed: {error_data.get('error', 'Unknown error')}"
                )
        raise HTTPException(
            status_code=404,
            detail=f"Simulation {simulation_id} not found"
        )
    
    with open(status_path, "r") as f:
        status_data = json.load(f)
        
    return SimulationResponse(
        simulation_id=status_data["simulation_id"],
        status=status_data["status"],
        platforms=[Platform(p) for p in status_data["platforms"]],
        days=status_data["days"],
        start_time=datetime.fromisoformat(status_data["start_time"]),
        end_time=datetime.fromisoformat(status_data["end_time"]) if "end_time" in status_data else None,
        results_url=status_data.get("results_url")
    )

@app.get("/simulations/{simulation_id}/results", response_model=SimulationResults)
async def get_simulation_results(simulation_id: str):
    """Get the results of a simulation."""
    user_id = "default"  # Use default user ID
    simulations_dir = os.path.join("results", "simulations", user_id)
    results_path = os.path.join(simulations_dir, f"{simulation_id}_results.json")
    
    if not os.path.exists(results_path):
        raise HTTPException(
            status_code=404,
            detail=f"Results for simulation {simulation_id} not found"
        )
    
    with open(results_path, "r") as f:
        results = json.load(f)
    
    # Extract the combined results
    combined = results.get("combined", {})
    total_metrics = combined.get("total_metrics", {})
    
    # Create the overall summary
    overall = SimulationResultSummary(
        impressions=total_metrics.get("impressions", 0),
        clicks=total_metrics.get("clicks", 0),
        conversions=total_metrics.get("conversions", 0),
        spend=total_metrics.get("spend", 0.0),
        ctr=total_metrics.get("ctr", 0.0),
        cpa=total_metrics.get("cpa", 0.0)
    )
    
    # Create platform summaries
    platform_summaries = {}
    for platform in ["google", "facebook", "linkedin"]:
        if platform in results and "total_metrics" in results[platform]:
            metrics = results[platform]["total_metrics"]
            platform_summaries[Platform(platform)] = PlatformResultSummary(
                impressions=metrics.get("impressions", 0),
                clicks=metrics.get("clicks", 0),
                conversions=metrics.get("conversions", 0),
                spend=metrics.get("spend", 0.0),
                ctr=metrics.get("ctr", 0.0),
                cpa=metrics.get("cpa", 0.0)
            )
    
    # Extract campaign results
    campaigns = {}
    for platform, platform_data in results.items():
        if platform != "combined" and "campaigns" in platform_data:
            campaigns[platform] = platform_data["campaigns"]
    
    return SimulationResults(
        simulation_id=simulation_id,
        overall=overall,
        platforms=platform_summaries,
        campaigns=campaigns,
        detailed_metrics=results
    )

@app.post("/campaigns/optimize", status_code=200)
async def optimize_campaigns(
    simulation_id: str,
    optimization_type: str = Query(..., description="Type of optimization (budget, targeting, creative)")
):
    """Optimize campaigns based on simulation results."""
    # This would analyze simulation results and provide optimization recommendations
    # For now, we'll return mock recommendations
    
    return {
        "simulation_id": simulation_id,
        "optimization_type": optimization_type,
        "recommendations": [
            {
                "platform": "google",
                "campaign_id": "google-1",
                "recommendation": "Increase daily budget by 20%",
                "expected_impact": "15% more conversions",
                "confidence": 0.85
            },
            {
                "platform": "facebook",
                "campaign_id": "facebook-1",
                "recommendation": "Add Instagram placements",
                "expected_impact": "10% lower CPA",
                "confidence": 0.75
            }
        ]
    }

@app.post("/simulations/compare", status_code=200)
async def compare_simulations(
    simulation_ids: List[str],
    metric: str = Query("cpa", description="Metric to compare (cpa, ctr, roas)")
):
    """Compare multiple simulation results."""
    # This would load and compare results from multiple simulations
    # For now, we'll return mock comparison data
    
    return {
        "simulation_ids": simulation_ids,
        "metric": metric,
        "comparison": [
            {
                "simulation_id": simulation_ids[0],
                "description": "Baseline simulation",
                "value": 12.50
            },
            {
                "simulation_id": simulation_ids[1],
                "description": "Optimized simulation",
                "value": 10.25,
                "improvement": "18%"
            }
        ]
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            detail=exc.detail,
            error_code=str(exc.status_code),
            timestamp=datetime.now()
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            detail=f"Internal server error: {str(exc)}",
            error_code="500",
            timestamp=datetime.now()
        ).dict()
    )

# Health check endpoint
@app.get("/health", status_code=200)
async def health_check():
    """Check if the API is running."""
    return {
        "status": "ok",
        "time": datetime.now().isoformat(),
        "simulator_available": AdSimulator is not None
    }

# Run the app
if __name__ == "__main__":
    # Set development environment flag
    os.environ["ENVIRONMENT"] = "development"
    
    # Print startup banner
    print("\n" + "="*50)
    print("Continuum Digital Twin API Server")
    print("="*50)
    print("Documentation: http://localhost:8000/docs")
    print("="*50 + "\n")
    
    # Start the server
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
