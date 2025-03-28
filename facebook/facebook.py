import random
from datetime import datetime, timedelta
import sys
import os
import math
import pandas as pd
import numpy as np
import asyncio
from typing import Dict, List, Optional, Union, Tuple

# Add parent directory to path to import base_simulator
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_simulator import BaseAdSimulator

class FacebookAdsSimulator(BaseAdSimulator):
    """Digital twin simulator for Meta Ads API v22.0 platforms (Facebook, Instagram, WhatsApp)."""
    
    def __init__(self, config=None):
        super().__init__("MetaAds", config)
        # Meta Ads API version
        self.api_version = "v22.0"
        
        self.placement_factors = {
            # Facebook placements
            "feed": {"reach_factor": 1.0, "ctr_factor": 1.0, "cpm_base": 7.5, "platform": "facebook"},
            "marketplace": {"reach_factor": 0.5, "ctr_factor": 1.2, "cpm_base": 5.5, "platform": "facebook"},
            "video": {"reach_factor": 0.6, "ctr_factor": 0.9, "cpm_base": 8.0, "platform": "facebook"},
            "right_column": {"reach_factor": 0.4, "ctr_factor": 0.6, "cpm_base": 3.5, "platform": "facebook"},
            "search": {"reach_factor": 0.3, "ctr_factor": 1.5, "cpm_base": 6.0, "platform": "facebook"},
            "instant_articles": {"reach_factor": 0.4, "ctr_factor": 0.7, "cpm_base": 4.0, "platform": "facebook"},
            # Instagram placements - v22.0 updated placement options
            "instagram_feed": {"reach_factor": 0.9, "ctr_factor": 1.1, "cpm_base": 9.0, "platform": "instagram"},
            "instagram_stories": {"reach_factor": 0.7, "ctr_factor": 0.8, "cpm_base": 6.0, "platform": "instagram"},
            "instagram_explore": {"reach_factor": 0.6, "ctr_factor": 0.9, "cpm_base": 7.0, "platform": "instagram"},
            "instagram_reels": {"reach_factor": 1.2, "ctr_factor": 1.4, "cpm_base": 11.0, "platform": "instagram"}, # Enhanced in v22.0
            "instagram_shop": {"reach_factor": 0.5, "ctr_factor": 1.4, "cpm_base": 8.0, "platform": "instagram"},
            "instagram_threads": {"reach_factor": 0.8, "ctr_factor": 1.2, "cpm_base": 9.5, "platform": "instagram"}, # New in v22.0
            # WhatsApp placements - v22.0 enhancements
            "whatsapp_business": {"reach_factor": 0.6, "ctr_factor": 1.4, "cpm_base": 8.5, "platform": "whatsapp"},
            "whatsapp_click_to_chat": {"reach_factor": 0.5, "ctr_factor": 1.6, "cpm_base": 7.0, "platform": "whatsapp"},
            "whatsapp_status": {"reach_factor": 0.7, "ctr_factor": 1.3, "cpm_base": 8.0, "platform": "whatsapp"} # New in v22.0
        }
        
        self.ad_account = {
            "id": "act_12345",
            "spend_cap": 10000.0,
            "currency": "USD",
            "account_status": "active",
            "timezone_name": "America/Los_Angeles",
            "business_country_code": "US",
            "disable_reason": 0,
            "api_version": "v22.0",
            "capabilities": ["CUSTOM_AUDIENCE_VIDEOS", "LEAD_ADS", "WHATSAPP_ADS", "ADVANTAGE_PLUS_CREATIVE", "AUTO_VERSION_UPGRADE"]
        }
        
        # API rate limits based on Meta Ads API v22.0
        self.rate_limits = {
            "standard_tier": {
                "facebook": {"max_score": 9000, "decay_period": 300, "block_duration": 60},
                "instagram": {"max_score": 9000, "decay_period": 300, "block_duration": 60}
            },
            "development_tier": {
                "facebook": {"max_score": 60, "decay_period": 300, "block_duration": 300},
                "instagram": {"max_score": 60, "decay_period": 300, "block_duration": 300}
            },
            "whatsapp": {
                "calls_per_hour": 5000, 
                "messages_per_second": 80,
                "business_initiated_conversations": 250,
                "template_message_limit": 10000,
                "waba_api_calls": 1800000 # v22.0 multiplier based on phone numbers
            },
            "hourly_quotas": {
                "ads_management": 5000,
                "custom_audience": 1000,
                "ads_insights": 2000,
                "catalog_management": 1000
            },
            "error_codes": {
                "rate_limit_general": 17,
                "rate_limit_custom": 613,
                "whatsapp_limit": 80007,
                "whatsapp_messaging_limit": 63018
            }
        }
        
        # Platforms and their capabilities in v22.0
        self.platforms = {
            "facebook": {
                "ad_formats": ["single_image", "carousel", "video", "slideshow", "collection", "dynamic_ads", "lead_form", "advantage_plus_creative"],
                "objectives": ["CONVERSIONS", "LINK_CLICKS", "APP_INSTALLS", "REACH", "LEAD_GENERATION", "VIDEO_VIEWS", "MESSAGES", "CATALOG_SALES", "STORE_VISITS", "BRAND_AWARENESS"],
                "creative_specs": {
                    "image_ratio": "1.91:1",
                    "text_limit": 125,
                    "headline_limit": 40,
                    "link_description_limit": 30
                },
                "api_endpoints": {
                    "campaigns": f"/{self.api_version}/act_{{id}}/campaigns",
                    "adsets": f"/{self.api_version}/adsets",
                    "ads": f"/{self.api_version}/ads",
                    "customaudiences": f"/{self.api_version}/customaudiences",
                    "insights": f"/{self.api_version}/act_{{id}}/insights"
                }
            },
            "instagram": {
                "ad_formats": ["single_image", "carousel", "video", "reels", "stories", "collection", "advantage_plus_creative"],
                "objectives": ["CONVERSIONS", "LINK_CLICKS", "APP_INSTALLS", "REACH", "PROFILE_VISITS", "VIDEO_VIEWS", "MESSAGES", "CATALOG_SALES", "BRAND_AWARENESS"],
                "creative_specs": {
                    "image_ratio": "1:1, 1.91:1, 4:5, 9:16",
                    "text_limit": 125,
                    "headline_limit": 40,
                    "reels_duration": 90  # seconds
                },
                "api_endpoints": {
                    "media": f"/{self.api_version}/{{ig-user-id}}/media",
                    "insights": f"/{self.api_version}/{{ig-user-id}}/insights"
                }
            },
            "whatsapp": {
                "ad_formats": ["click_to_whatsapp", "message_templates"],
                "objectives": ["MESSAGES", "MESSAGE_DELIVERABILITY"],
                "template_categories": ["MARKETING", "UTILITY", "AUTHENTICATION"],
                "creative_specs": {
                    "cta_text_limit": 20,
                    "template_components": ["header", "body", "footer", "buttons"],
                    "interactive_buttons": ["quick_reply", "url", "phone_number"]
                },
                "api_endpoints": {
                    "whatsapp_business_accounts": f"/{self.api_version}/whatsapp_business_accounts",
                    "message_templates": f"/{self.api_version}/{{whatsapp-business-account-id}}/message_templates",
                    "phone_numbers": f"/{self.api_version}/{{whatsapp-business-account-id}}/phone_numbers"
                }
            }
        }
        
        # Bidding strategies with efficiency factors (v22.0 specific)
        self.bidding_strategies = {
            "LOWEST_COST_WITHOUT_CAP": {"efficiency": 1.0, "platforms": ["facebook", "instagram", "whatsapp"]},
            "COST_CAP": {"efficiency": 0.9, "platforms": ["facebook", "instagram"]},
            "LOWEST_COST_WITH_MIN_ROAS": {"efficiency": 0.85, "platforms": ["facebook", "instagram"]},
            "LOWEST_COST_WITH_BID_CAP": {"efficiency": 0.8, "platforms": ["facebook", "instagram", "whatsapp"]},
            "HIGHEST_VALUE_LOWEST_COST": {"efficiency": 0.95, "platforms": ["facebook", "instagram"]} # New in v22.0
        }
        
        # Webhook event types for real-time notifications (v22.0)
        self.webhook_events = {
            "facebook": ["CAMPAIGN_ACTIVE", "AD_REVIEW_APPROVED", "CONVERSION_EVENT", "BUDGET_PACING", "ADVANTAGE_PLUS_CREATIVE_GENERATED"],
            "instagram": ["CAMPAIGN_ACTIVE", "AD_REVIEW_APPROVED", "PROFILE_ENGAGEMENT", "REELS_ENGAGEMENT"],
            "whatsapp": ["MESSAGE_DELIVERED", "MESSAGE_READ", "CONVERSATION_STARTED", "TEMPLATE_APPROVAL", "WABA_STATUS_UPDATE"]
        }
        
        # Compliance and security settings (v22.0)
        self.compliance = {
            "data_retention": {
                "facebook": 180,  # days
                "instagram": 180,  # days
                "whatsapp": 90    # days (shorter for sensitive data)
            },
            "anonymization": {
                "phone_numbers": "SHA256",
                "emails": "SHA256",
                "device_ids": "MD5"
            },
            "creative_policies": {
                "facebook": ["prohibited content check", "advantage_plus_creative_requirements"],
                "instagram": ["aspect ratio enforcement", "branded content tags", "story interactivity", "reels_content_guidelines"],
                "whatsapp": ["template pre-approval", "message category enforcement", "business verification", "conversation_rate_limits"]
            },
            "authentication": {
                "system_user_tokens": {
                    "expires": False,
                    "scopes": ["ads_management", "business_management", "whatsapp_business_management"]
                },
                "user_tokens": {
                    "expires": True,
                    "scopes": ["ads_read", "ads_management", "whatsapp_business_messaging"]
                }
            }
        }
        
        # ML model parameters for simulation (v22.0 enhanced)
        self.ml_models = {
            "ctr_prediction": {
                "base_features": ["platform", "placement", "objective", "audience_match", "creative_quality"],
                "weights": {"platform": 0.2, "placement": 0.3, "objective": 0.15, "audience_match": 0.25, "creative_quality": 0.1},
                "learning_rate": 0.01,
                "decay_factor": 0.95
            },
            "budget_optimizer": {
                "metrics": ["ctr", "cpa", "roas"],
                "weights": {"ctr": 0.3, "cpa": 0.4, "roas": 0.3},
                "min_data_points": 100,
                "confidence_threshold": 0.7
            },
            "advantage_plus_creative": {
                "enabled": True,
                "asset_combination_limit": 50,
                "performance_boost": 0.15,
                "platforms": ["facebook", "instagram"]
            }
        }
        
        # Historical performance data storage for ML training
        self.historical_data = {
            "campaigns": {},
            "platform_benchmarks": {
                "facebook": {"ctr": 0.01, "cvr": 0.02, "cpm": 7.5},
                "instagram": {"ctr": 0.012, "cvr": 0.015, "cpm": 8.5},
                "whatsapp": {"ctr": 0.02, "cvr": 0.03, "cpm": 6.5}
            }
        }
    
    def create_ad_set(self, campaign_id, ad_set_data):
        """Create an ad set within a campaign."""
        for campaign in self.campaigns:
            if campaign["id"] == campaign_id:
                if "ad_sets" not in campaign:
                    campaign["ad_sets"] = []
                
                ad_set_id = f"{campaign_id}-as-{len(campaign['ad_sets']) + 1}"
                ad_set = {
                    "id": ad_set_id,
                    "data": ad_set_data,
                    "ads": [],
                    "status": "active",
                    "metrics": {
                        "impressions": 0,
                        "clicks": 0,
                        "conversions": 0,
                        "spend": 0.0
                    }
                }
                campaign["ad_sets"].append(ad_set)
                return ad_set_id
        
        raise ValueError(f"Campaign {campaign_id} not found")
    
    def create_ad(self, ad_set_id, ad_data):
        """Create an ad within an ad set."""
        for campaign in self.campaigns:
            if "ad_sets" not in campaign:
                continue
                
            for ad_set in campaign["ad_sets"] {
                if ad_set["id"] == ad_set_id:
                    ad_id = f"{ad_set_id}-ad-{len(ad_set['ads']) + 1}"
                    
                    # Generate a relevance score (1-10)
                    relevance_score = random.randint(1, 10)
                    
                    ad = {
                        "id": ad_id,
                        "data": ad_data,
                        "status": "active",
                        "review_status": "approved" if random.random() > 0.1 else "pending_review",
                        "relevance_score": relevance_score,
                        "metrics": {
                            "impressions": 0,
                            "clicks": 0,
                            "conversions": 0,
                            "spend": 0.0
                        }
                    }
                    ad_set["ads"].append(ad)
                    return ad_id
        
        raise ValueError(f"Ad set {ad_set_id} not found")
    
    def define_audience(self, audience_name, audience_params):
        """Define a Meta audience with specific targeting parameters."""
        audience_id = super().define_audience(audience_name, audience_params)
        
        # Meta-specific audience parameters
        self.audiences[audience_name].update({
            "demographics_match": audience_params.get("demographics_match", 0.7),
            "interests_match": audience_params.get("interests_match", 0.5),
            "behaviors_match": audience_params.get("behaviors_match", 0.4),
            "lookalike_quality": audience_params.get("lookalike_quality", 0.6),
            # Add platform-specific audience parameters
            "ig_engaged_users": audience_params.get("ig_engaged_users", False),
            "facebook_wifi_user": audience_params.get("facebook_wifi_user", False),
            "whatsapp_opted_in": audience_params.get("whatsapp_opted_in", False)
        })
        
        return audience_id
    
    def _calculate_audience_reach(self, ad_set_data):
        """Calculate the potential reach of an audience based on targeting."""
        base_reach = 1000000  # Starting point
        
        # Apply targeting modifiers
        targeting = ad_set_data.get("targeting", {})
        
        # Age range impact
        age_range = targeting.get("age_range", {"min": 18, "max": 65})
        age_span = age_range.get("max", 65) - age_range.get("min", 18)
        age_factor = min(age_span / 50.0, 1.0)  # Normalize to 0-1
        
        # Gender impact
        gender_factor = 1.0
        if targeting.get("gender") in ["male", "female"]:
            gender_factor = 0.5
            
        # Location impact
        locations = targeting.get("locations", [])
        location_factor = min(len(locations) / 5.0, 1.0)
        
        # Interest narrowing
        interests = targeting.get("interests", [])
        interest_factor = max(0.1, 1.0 - (len(interests) * 0.1))
        
        # Calculate effective reach
        reach = int(base_reach * age_factor * gender_factor * location_factor * interest_factor)
        return reach
    
    def _run_platform_simulation(self, days, speed_factor):
        """Run Meta Ads v22.0 specific simulation across Facebook, Instagram, and WhatsApp."""
        total_impressions = 0
        total_clicks = 0
        total_conversions = 0
        total_spend = 0.0
        
        for campaign in self.campaigns:
            campaign_id = campaign["id"]
            campaign_budget = campaign["data"].get("budget", 1000.0)
            campaign_objective = campaign["data"].get("objective", "CONVERSIONS")
            campaign_spend = 0.0
            campaign_impressions = 0
            campaign_clicks = 0
            campaign_conversions = 0
            
            # Skip inactive campaigns
            if campaign["status"] != "active":
                continue
            
            # Process each ad set
            if "ad_sets" in campaign:
                for ad_set in campaign["ad_sets"]:
                    # Skip inactive ad sets
                    if ad_set["status"] != "active":
                        continue
                    
                    ad_set_data = ad_set["data"]
                    ad_set_budget = ad_set_data.get("budget", campaign_budget / len(campaign["ad_sets"]))
                    ad_set_spend = 0.0
                    ad_set_impressions = 0
                    ad_set_clicks = 0
                    ad_set_conversions = 0
                    
                    # Get audience information
                    audience_name = ad_set_data.get("audience", "default")
                    audience = self.audiences.get(audience_name, {
                        "size": 1000000,
                        "ctr_base": 0.02,
                        "conversion_rate": 0.01,
                        "demographics_match": 0.7,
                        "interests_match": 0.5
                    })
                    
                    # Calculate potential reach
                    potential_reach = self._calculate_audience_reach(ad_set_data)
                    
                    # Get placements
                    placements = ad_set_data.get("placements", ["feed"])
                    if not isinstance(placements, list):
                        placements = [placements]
                    
                    # Default to feed if empty
                    if not placements:
                        placements = ["feed"]
                    
                    # Process each ad in the ad set
                    if "ads" in ad_set:
                        for ad in ad_set["ads"]:
                            # Skip inactive or unapproved ads
                            if ad["status"] != "active" or ad["review_status"] != "approved":
                                continue
                            
                            ad_relevance = ad["relevance_score"] / 10.0  # Normalize to 0-1
                            
                            # Calculate metrics for each placement
                            for placement in placements:
                                placement_data = self.placement_factors.get(
                                    placement, 
                                    self.placement_factors["feed"]
                                )
                                
                                # Daily metrics
                                for day in range(days):
                                    # Stop if budget is exhausted
                                    if ad_set_spend >= ad_set_budget:
                                        break
                                    
                                    # Daily variation factor
                                    daily_factor = random.uniform(0.8, 1.2)
                                    
                                    # Calculate daily impressions
                                    daily_reach = int(potential_reach * placement_data["reach_factor"] * daily_factor / 30)
                                    daily_impressions = int(daily_reach * (1 + random.uniform(-0.2, 0.2)))
                                    
                                    # Calculate CTR based on relevance and placement
                                    base_ctr = audience["ctr_base"] * placement_data["ctr_factor"] * ad_relevance
                                    daily_ctr = base_ctr * (1 + random.uniform(-0.3, 0.3))
                                    
                                    # Calculate clicks
                                    daily_clicks = int(daily_impressions * daily_ctr)
                                    
                                    # Calculate CPM and spend
                                    base_cpm = placement_data["cpm_base"] * (0.5 + ad_relevance)
                                    daily_cpm = base_cpm * (1 + random.uniform(-0.2, 0.2))
                                    daily_spend = (daily_impressions / 1000) * daily_cpm
                                    
                                    # Apply budget constraints
                                    if ad_set_spend + daily_spend > ad_set_budget:
                                        ratio = (ad_set_budget - ad_set_spend) / daily_spend
                                        daily_impressions = int(daily_impressions * ratio)
                                        daily_clicks = int(daily_clicks * ratio)
                                        daily_spend = ad_set_budget - ad_set_spend
                                    
                                    # Calculate conversions based on objective
                                    conversion_rate_multipliers = {
                                        "CONVERSIONS": 1.0,
                                        "TRAFFIC": 0.5,
                                        "ENGAGEMENT": 0.3,
                                        "VIDEO_VIEWS": 0.2,
                                        "BRAND_AWARENESS": 0.1
                                    }
                                    multiplier = conversion_rate_multipliers.get(campaign_objective, 0.5)
                                    
                                    daily_conversion_rate = audience["conversion_rate"] * multiplier * ad_relevance
                                    daily_conversions = int(daily_clicks * daily_conversion_rate)
                                    
                                    # Accumulate ad set metrics
                                    ad_set_impressions += daily_impressions
                                    ad_set_clicks += daily_clicks
                                    ad_set_conversions += daily_conversions
                                    ad_set_spend += daily_spend
                                    
                                    # Accumulate ad metrics
                                    ad["metrics"]["impressions"] += daily_impressions
                                    ad["metrics"]["clicks"] += daily_clicks
                                    ad["metrics"]["conversions"] += daily_conversions
                                    ad["metrics"]["spend"] += daily_spend
                                    
                    # Update ad set metrics
                    ad_set["metrics"]["impressions"] = ad_set_impressions
                    ad_set["metrics"]["clicks"] = ad_set_clicks
                    ad_set["metrics"]["conversions"] = ad_set_conversions
                    ad_set["metrics"]["spend"] = ad_set_spend
                    
                    # Accumulate campaign metrics
                    campaign_impressions += ad_set_impressions
                    campaign_clicks += ad_set_clicks
                    campaign_conversions += ad_set_conversions
                    campaign_spend += ad_set_spend
            
            # Store campaign results with enhanced metrics for Meta Ads API v22.0
            self.results["campaigns"][campaign_id] = {
                "impressions": campaign_impressions,
                "clicks": campaign_clicks,
                "conversions": campaign_conversions,
                "spend": campaign_spend,
                "ctr": campaign_clicks / campaign_impressions if campaign_impressions > 0 else 0,
                "cpa": campaign_spend / campaign_conversions if campaign_conversions > 0 else 0,
                "roas": (campaign_conversions * 50) / campaign_spend if campaign_spend > 0 else 0, # Assuming $50 per conversion
                "platform_breakdown": self._calculate_platform_breakdown(campaign_id),
                "quality_ranking": self._calculate_quality_ranking(campaign_impressions, campaign_clicks),
                "engagement_rate": self._calculate_engagement_rate(campaign_id),
                "message_deliverability": self._calculate_message_deliverability(campaign_id),
                "optimization_score": self._calculate_optimization_score(campaign_id),
                "auction_competitiveness": self._calculate_auction_insight(campaign_id),
                "compliance_status": self._check_campaign_compliance(campaign_id),
                "cross_platform_frequency": self._calculate_cross_platform_frequency(campaign_id),
                "time_series_data": self._generate_time_series_data(campaign_id, days),
                "advantage_plus_performance": self._calculate_advantage_plus_performance(campaign_id),
                "publisher_platform_breakdown": self._calculate_publisher_platform_breakdown(campaign_id)
            }
            
            # Store historical data for ML model training
            self.historical_data["campaigns"][campaign_id] = {
                "metrics": {
                    "daily_impressions": [ad_set["metrics"]["impressions"] // days for ad_set in campaign.get("ad_sets", [])],
                    "daily_clicks": [ad_set["metrics"]["clicks"] // days for ad_set in campaign.get("ad_sets", [])],
                    "daily_conversions": [ad_set["metrics"]["conversions"] // days for ad_set in campaign.get("ad_sets", [])]
                },
                "settings": {
                    "objective": campaign["data"].get("objective", "CONVERSIONS"),
                    "bid_strategy": campaign["data"].get("bid_strategy", "LOWEST_COST_WITHOUT_CAP"),
                    "placements": self._get_campaign_placements(campaign_id)
                }
            }
            
            # Accumulate total metrics
            total_impressions += campaign_impressions
            total_clicks += campaign_clicks
            total_conversions += campaign_conversions
            total_spend += campaign_spend
        
        # Update total metrics with enhanced Meta Ads API v22.0 data
        self.results["total_metrics"] = {
            "impressions": total_impressions,
            "clicks": total_clicks,
            "conversions": total_conversions,
            "spend": total_spend,
            "ctr": total_clicks / total_impressions if total_impressions > 0 else 0,
            "cpa": total_spend / total_conversions if total_conversions > 0 else 0,
            "roas": (total_conversions * 50) / total_spend if total_spend > 0 else 0,
            "platform_summary": {
                "facebook": self._calculate_platform_percentage("facebook"),
                "instagram": self._calculate_platform_percentage("instagram"),
                "whatsapp": self._calculate_platform_percentage("whatsapp")
            },
            "rate_limit_status": self._calculate_rate_limit_status(),
            "api_call_efficiency": self._calculate_api_efficiency(),
            "api_version": self.api_version,
            "advantage_plus_adoption": self._calculate_advantage_plus_adoption(),
            "cross_platform_lift": self._calculate_cross_platform_lift()
        }
        
        # Run machine learning optimizations
        self._run_ml_optimizations()
    
    def _calculate_platform_breakdown(self, campaign_id):
        """Calculate impression distribution across Meta platforms for a campaign."""
        # Find all ad sets in the campaign
        platform_metrics = {"facebook": 0, "instagram": 0, "whatsapp": 0}
        
        for campaign in self.campaigns:
            if campaign["id"] == campaign_id and "ad_sets" in campaign:
                total_impressions = 0
                for ad_set in campaign["ad_sets"]:
                    # Skip inactive ad sets
                    if ad_set["status"] != "active":
                        continue
                    
                    # Get placements
                    placements = ad_set["data"].get("placements", ["feed"])
                    if not isinstance(placements, list):
                        placements = [placements]
                    
                    # Count impressions by platform
                    for placement in placements:
                        impressions = ad_set["metrics"]["impressions"] / len(placements)
                        # Map placement to platform
                        placement_info = self.placement_factors.get(placement, {"platform": "facebook"})
                        platform = placement_info["platform"]
                        platform_metrics[platform] += impressions
                        total_impressions += impressions
                
                # Convert to percentages
                if total_impressions > 0:
                    for platform in platform_metrics:
                        platform_metrics[platform] = platform_metrics[platform] / total_impressions
        
        return platform_metrics
    
    def _calculate_platform_percentage(self, platform):
        """Calculate the percentage of total impressions on a specific platform."""
        total_impressions = self.results["total_metrics"]["impressions"]
        platform_impressions = 0
        
        for campaign_id, metrics in self.results["campaigns"].items():
            if "platform_breakdown" in metrics:
                platform_percentage = metrics["platform_breakdown"].get(platform, 0)
                campaign_impressions = metrics["impressions"]
                platform_impressions += platform_percentage * campaign_impressions
        
        return platform_impressions / total_impressions if total_impressions > 0 else 0
    
    def _calculate_quality_ranking(self, impressions, clicks):
        """Calculate quality ranking based on engagement metrics."""
        if impressions == 0:
            return "BELOW_AVERAGE"
        
        ctr = clicks / impressions
        
        if ctr >= 0.03:
            return "ABOVE_AVERAGE"
        elif ctr >= 0.015:
            return "AVERAGE"
        else:
            return "BELOW_AVERAGE"
    
    def _calculate_engagement_rate(self, campaign_id):
        """Calculate engagement rate for a campaign (includes likes, comments, shares)."""
        for campaign in self.campaigns:
            if campaign["id"] == campaign_id:
                clicks = 0
                impressions = 0
                
                if "ad_sets" in campaign:
                    for ad_set in campaign["ad_sets"]:
                        clicks += ad_set["metrics"]["clicks"]
                        impressions += ad_set["metrics"]["impressions"]
                
                # Simulate social engagements (likes, comments, shares)
                if impressions > 0:
                    engagement_factor = random.uniform(0.01, 0.05)
                    engagement_rate = (clicks / impressions) + engagement_factor
                    return min(engagement_rate, 0.15)  # Cap at reasonable maximum
        
        return 0.0
    
    def _calculate_message_deliverability(self, campaign_id):
        """Calculate WhatsApp message deliverability rate for a campaign."""
        # Check if campaign uses WhatsApp placement
        uses_whatsapp = False
        whatsapp_quality = random.uniform(0.85, 0.99)  # Simulate WhatsApp quality rating
        
        for campaign in self.campaigns:
            if campaign["id"] == campaign_id and "ad_sets" in campaign:
                for ad_set in campaign["ad_sets"]:
                    placements = ad_set["data"].get("placements", [])
                    if "whatsapp" in placements:
                        uses_whatsapp = True
                        break
        
        if uses_whatsapp:
            return whatsapp_quality
        else:
            return None
    
    def _calculate_optimization_score(self, campaign_id):
        """Calculate an optimization score based on campaign settings and performance."""
        optimization_score = 0.5  # Start with neutral score
        
        for campaign in self.campaigns:
            if campaign["id"] == campaign_id:
                # Check campaign objective
                objective = campaign["data"].get("objective", "CONVERSIONS")
                
                # Check if objective matches the platform distribution
                platform_breakdown = self._calculate_platform_breakdown(campaign_id)
                
                if objective == "MESSAGES" and platform_breakdown["whatsapp"] < 0.5:
                    optimization_score -= 0.1  # Penalize for not using WhatsApp enough for message objective
                
                if objective == "PROFILE_VISITS" and platform_breakdown["instagram"] < 0.5:
                    optimization_score -= 0.1  # Penalize for not using Instagram enough for profile visits
                
                # Check if bid strategy is appropriate for objective
                bid_strategy = campaign["data"].get("bid_strategy", "LOWEST_COST_WITHOUT_CAP")
                if objective == "CONVERSIONS" and bid_strategy == "LOWEST_COST_WITH_MIN_ROAS":
                    optimization_score += 0.1  # Good match
                
                if objective == "BRAND_AWARENESS" and bid_strategy == "COST_CAP":
                    optimization_score -= 0.05  # Not ideal match
                
                # Check if campaign has active ads
                if "ad_sets" in campaign:
                    active_ads_count = 0
                    for ad_set in campaign["ad_sets"]:
                        for ad in ad_set.get("ads", []):
                            if ad["status"] == "active" and ad["review_status"] == "approved":
                                active_ads_count += 1
                    
                    if active_ads_count == 0:
                        optimization_score -= 0.2  # No active ads
                    elif active_ads_count > 10:
                        optimization_score += 0.1  # Good number of ads for testing
                
                # Check if campaign has multiple ad formats
                ad_formats = set()
                if "ad_sets" in campaign:
                    for ad_set in campaign["ad_sets"]:
                        for ad in ad_set.get("ads", []):
                            ad_format = ad["data"].get("format", "single_image")
                            ad_formats.add(ad_format)
                
                if len(ad_formats) > 2:
                    optimization_score += 0.1  # Good variety of ad formats
                
                # Adjust score to be between 0 and 1
                optimization_score = max(0, min(1, optimization_score + 0.5))
                
                return optimization_score
        
        return optimization_score
    
    def _calculate_auction_insight(self, campaign_id):
        """Calculate auction competitiveness for a campaign."""
        # Simulate auction insights across platforms
        insights = {}
        
        for platform in self.platforms:
            # Randomly generate auction metrics
            if random.random() > 0.2:  # 80% chance to have data for this platform
                insights[platform] = {
                    "overlap_rate": random.uniform(0.1, 0.5),
                    "outranking_share": random.uniform(0.3, 0.7),
                    "impression_share": random.uniform(0.2, 0.8),
                    "competitiveness": random.choice(["HIGH", "MEDIUM", "LOW"])
                }
        
        return insights
    
    def _check_campaign_compliance(self, campaign_id):
        """Check campaign compliance status against platform policies (updated for v22.0)."""
        compliance_status = {"status": "COMPLIANT", "issues": []}
        
        for campaign in self.campaigns:
            if campaign["id"] == campaign_id and "ad_sets" in campaign:
                for ad_set in campaign["ad_sets"]:
                    placements = ad_set["data"].get("placements", ["feed"])
                    if not isinstance(placements, list):
                        placements = [placements]
                    
                    # Check platform-specific compliance issues
                    for placement in placements:
                        placement_info = self.placement_factors.get(placement, {"platform": "facebook"})
                        platform = placement_info["platform"]
                        
                        # Check for ads with platform-specific issues
                        for ad in ad_set.get("ads", []):
                            ad_format = ad["data"].get("format", "single_image")
                            
                            # Instagram specific checks - v22.0 updated rules
                            if platform == "instagram":
                                if ad_format == "reels":
                                    # Check if reels duration is within limits
                                    duration = ad["data"].get("video_duration", 15)
                                    if duration > 90:
                                        compliance_status["status"] = "ISSUES_FOUND"
                                        compliance_status["issues"].append(f"Instagram Reels exceeds 90 second limit: {duration}s")
                                
                                # Check for Instagram Threads placement issues
                                if placement == "instagram_threads":
                                    if ad_format not in ["single_image", "video"]:
                                        compliance_status["status"] = "ISSUES_FOUND"
                                        compliance_status["issues"].append(f"Unsupported format for Threads: {ad_format}")
                            
                            # WhatsApp specific checks - v22.0 updated requirements
                            if platform == "whatsapp":
                                if ad_format not in ["click_to_whatsapp", "message_templates"]:
                                    compliance_status["status"] = "ISSUES_FOUND"
                                    compliance_status["issues"].append(f"Unsupported format for WhatsApp: {ad_format}")
                                
                                # Check if using approved templates
                                template_status = ad["data"].get("template_status", "APPROVED")
                                if template_status != "APPROVED":
                                    compliance_status["status"] = "ISSUES_FOUND"
                                    compliance_status["issues"].append(f"WhatsApp template not approved: {template_status}")
                                
                                # Check for proper WhatsApp business verification
                                business_verification = ad["data"].get("business_verification_status", "VERIFIED")
                                if business_verification != "VERIFIED":
                                    compliance_status["status"] = "ISSUES_FOUND"
                                    compliance_status["issues"].append(f"WhatsApp business not properly verified: {business_verification}")
                            
                            # Facebook specific checks - v22.0 updated rules
                            if platform == "facebook":
                                if ad_format == "lead_form":
                                    privacy_policy = ad["data"].get("privacy_policy_url", None)
                                    if not privacy_policy:
                                        compliance_status["status"] = "ISSUES_FOUND"
                                        compliance_status["issues"].append("Lead form missing privacy policy URL")
                                
                                # Check for Advantage+ requirements if enabled
                                if ad["data"].get("is_advantage_plus", False):
                                    assets = ad["data"].get("assets", {})
                                    if not assets.get("headlines", []) or len(assets.get("headlines", [])) < 3:
                                        compliance_status["status"] = "ISSUES_FOUND"
                                        compliance_status["issues"].append("Advantage+ Creative requires at least 3 headlines")
                                    
                                    if not assets.get("descriptions", []) or len(assets.get("descriptions", [])) < 2:
                                        compliance_status["status"] = "ISSUES_FOUND"
                                        compliance_status["issues"].append("Advantage+ Creative requires at least 2 descriptions")
                                    
                                    if not assets.get("images", []) or len(assets.get("images", [])) < 2:
                                        compliance_status["status"] = "ISSUES_FOUND"
                                        compliance_status["issues"].append("Advantage+ Creative requires at least 2 images")
        
        return compliance_status
    
    def _calculate_cross_platform_frequency(self, campaign_id):
        """Calculate cross-platform frequency for user exposures."""
        # Calculate how many times the same user sees ads across platforms
        platform_impressions = {}
        total_audience = 0
        
        for campaign in self.campaigns:
            if campaign["id"] == campaign_id and "ad_sets" in campaign:
                # Estimate audience size
                for ad_set in campaign["ad_sets"]:
                    total_audience += self._calculate_audience_reach(ad_set["data"])
                
                # Distribute impressions by platform
                platform_breakdown = self._calculate_platform_breakdown(campaign_id)
                campaign_impressions = campaign["metrics"]["impressions"] if "metrics" in campaign else 0
                
                for platform, percentage in platform_breakdown.items():
                    platform_impressions[platform] = int(campaign_impressions * percentage)
        
        # Calculate average frequency per platform
        frequency_by_platform = {}
        overall_frequency = 0
        
        if total_audience > 0:
            for platform, impressions in platform_impressions.items():
                frequency_by_platform[platform] = impressions / total_audience
                overall_frequency += frequency_by_platform[platform]
            
            # Add cross-platform overlap estimate (users who see ads on multiple platforms)
            overlap_factor = random.uniform(0.2, 0.4)  # 20-40% overlap between platforms
            
            frequency_by_platform["cross_platform_overlap"] = overlap_factor
            frequency_by_platform["effective_frequency"] = overall_frequency * (1 - overlap_factor)
        
        return frequency_by_platform
    
    def _generate_time_series_data(self, campaign_id, days):
        """Generate daily time series data for campaign metrics."""
        daily_data = []
        
        for campaign in self.campaigns:
            if campaign["id"] == campaign_id:
                campaign_impressions = campaign["metrics"]["impressions"] if "metrics" in campaign else 0
                campaign_clicks = campaign["metrics"]["clicks"] if "metrics" in campaign else 0
                campaign_conversions = campaign["metrics"]["conversions"] if "metrics" in campaign else 0
                campaign_spend = campaign["metrics"]["spend"] if "metrics" in campaign else 0
                
                # Calculate daily averages
                daily_impressions_avg = campaign_impressions / days
                daily_clicks_avg = campaign_clicks / days
                daily_conversions_avg = campaign_conversions / days
                daily_spend_avg = campaign_spend / days
                
                # Generate time series with realistic patterns
                start_date = datetime.now() - timedelta(days=days)
                
                for day in range(days):
                    current_date = start_date + timedelta(days=day)
                    weekday = current_date.weekday()
                    
                    # Apply day-of-week effect (weekends typically have different patterns)
                    day_factor = 0.8 if weekday >= 5 else 1.0  # Lower on weekends
                    
                    # Apply random daily variation
                    random_factor = random.uniform(0.85, 1.15)
                    
                    # Apply trend over time (slight improvement)
                    trend_factor = 1.0 + (day * 0.005)  # 0.5% improvement per day
                    
                    # Calculate daily metrics
                    daily_impressions = int(daily_impressions_avg * day_factor * random_factor * trend_factor)
                    daily_clicks = int(daily_clicks_avg * day_factor * random_factor * trend_factor)
                    daily_conversions = int(daily_conversions_avg * day_factor * random_factor * trend_factor)
                    daily_spend = daily_spend_avg * day_factor * random_factor
                    
                    daily_data.append({
                        "date": current_date.strftime("%Y-%m-%d"),
                        "impressions": daily_impressions,
                        "clicks": daily_clicks,
                        "conversions": daily_conversions,
                        "spend": daily_spend,
                        "ctr": daily_clicks / daily_impressions if daily_impressions > 0 else 0,
                        "cpa": daily_spend / daily_conversions if daily_conversions > 0 else 0,
                        "platform_breakdown": self._calculate_daily_platform_breakdown(campaign_id, day_factor)
                    })
        
        return daily_data
    
    def _calculate_daily_platform_breakdown(self, campaign_id, day_factor):
        """Calculate platform breakdown for a specific day."""
        base_breakdown = self._calculate_platform_breakdown(campaign_id)
        daily_breakdown = {}
        
        # Adjust breakdown based on day factor (e.g., more mobile/Instagram usage on weekends)
        if day_factor < 1.0:  # Weekend
            # Boost Instagram share on weekends
            instagram_boost = random.uniform(0.05, 0.1)
            facebook_reduction = instagram_boost * (base_breakdown["facebook"] / (base_breakdown["facebook"] + base_breakdown["whatsapp"]))
            whatsapp_reduction = instagram_boost * (base_breakdown["whatsapp"] / (base_breakdown["facebook"] + base_breakdown["whatsapp"]))
            
            daily_breakdown["facebook"] = max(0, base_breakdown["facebook"] - facebook_reduction)
            daily_breakdown["instagram"] = base_breakdown["instagram"] + instagram_boost
            daily_breakdown["whatsapp"] = max(0, base_breakdown["whatsapp"] - whatsapp_reduction)
        else:
            # Regular weekday - similar to base breakdown with slight variation
            variation = random.uniform(-0.03, 0.03)
            
            daily_breakdown["facebook"] = max(0, base_breakdown["facebook"] + variation)
            daily_breakdown["instagram"] = max(0, base_breakdown["instagram"] - variation/2)
            daily_breakdown["whatsapp"] = max(0, base_breakdown["whatsapp"] - variation/2)
            
            # Normalize to ensure sum = 1
            total = daily_breakdown["facebook"] + daily_breakdown["instagram"] + daily_breakdown["whatsapp"]
            if total > 0:
                for platform in daily_breakdown:
                    daily_breakdown[platform] /= total
        
        return daily_breakdown
    
    def _calculate_rate_limit_status(self):
        """Calculate simulated rate limit status for API calls (v22.0 specific)."""
        return {
            "facebook_ads_management": {
                "calls_used": random.randint(1000, 4800),
                "calls_limit": 5000,
                "reset_time_seconds": random.randint(1, 3600),
                "error_code_if_exceeded": self.rate_limits["error_codes"]["rate_limit_general"]
            },
            "instagram_api": {
                "calls_used": random.randint(50, 190),
                "calls_limit": 200,
                "reset_time_seconds": random.randint(1, 3600),
                "error_code_if_exceeded": self.rate_limits["error_codes"]["rate_limit_general"]
            },
            "whatsapp_business_api": {
                "calls_used": random.randint(1000, 4800),
                "calls_limit": 5000,
                "reset_time_seconds": random.randint(1, 3600),
                "messaging_limit_used": random.randint(50, 240),
                "messaging_limit": 250,
                "error_code_if_exceeded": self.rate_limits["error_codes"]["whatsapp_limit"]
            },
            "auto_version_upgrade": {
                "enabled": True,
                "eligible_endpoints": ["campaigns", "adsets", "ads", "insights"],
                "version_from": "v21.0",
                "version_to": "v22.0"
            }
        }
    
    def _calculate_api_efficiency(self):
        """Calculate API call efficiency metrics."""
        return {
            "call_success_rate": random.uniform(0.95, 0.995),
            "average_response_time_ms": random.uniform(150, 350),
            "throttled_requests": random.randint(0, 10),
            "batch_efficiency": random.uniform(0.7, 0.9)
        }
    
    def _get_campaign_placements(self, campaign_id):
        """Get all placements used in a campaign."""
        placements = set()
        
        for campaign in self.campaigns:
            if campaign["id"] == campaign_id and "ad_sets" in campaign:
                for ad_set in campaign["ad_sets"]:
                    ad_set_placements = ad_set["data"].get("placements", ["feed"])
                    if isinstance(ad_set_placements, list):
                        placements.update(ad_set_placements)
                    else:
                        placements.add(ad_set_placements)
        
        return list(placements)
    
    def _run_ml_optimizations(self):
        """Run machine learning optimizations on campaign data."""
        # Only run if we have enough historical data
        if len(self.historical_data["campaigns"]) < 3:
            return
        
        # Perform campaign budget optimization
        self._optimize_campaign_budgets()
        
        # Perform creative optimization
        self._optimize_ad_creatives()
        
        # Perform cross-platform allocation optimization
        self._optimize_platform_allocation()
    
    def _optimize_campaign_budgets(self):
        """Use ML to optimize campaign budgets based on performance."""
        for campaign in self.campaigns:
            campaign_id = campaign["id"]
            if campaign_id not in self.results["campaigns"]:
                continue
            
            # Get campaign performance metrics
            metrics = self.results["campaigns"][campaign_id]
            
            # Skip if not enough data
            if metrics["impressions"] < 1000:
                continue
            
            # Calculate performance score based on objective
            objective = campaign["data"].get("objective", "CONVERSIONS")
            performance_score = 0
            
            if objective == "CONVERSIONS":
                # Lower CPA is better
                performance_score = 100 / (metrics["cpa"] + 1) if metrics["cpa"] > 0 else 100
            elif objective in ["LINK_CLICKS", "TRAFFIC"]:
                # Higher CTR is better
                performance_score = metrics["ctr"] * 1000
            elif objective == "REACH":
                # Lower CPM is better
                cpm = (metrics["spend"] * 1000) / metrics["impressions"] if metrics["impressions"] > 0 else 0
                performance_score = 10 / (cpm + 0.1) if cpm > 0 else 100
            
            # Calculate budget adjustment
            if performance_score > 50:
                # Good performance, increase budget by 10-20%
                adjustment_factor = random.uniform(1.1, 1.2)
            elif performance_score > 30:
                # Average performance, maintain budget
                adjustment_factor = random.uniform(0.95, 1.05)
            else:
                # Poor performance, decrease budget by 10-20%
                adjustment_factor = random.uniform(0.8, 0.9)
            
            # Create optimization recommendation
            if "optimizations" not in self.results:
                self.results["optimizations"] = {"campaigns": {}}
            
            self.results["optimizations"]["campaigns"][campaign_id] = {
                "current_budget": campaign["data"].get("budget", 1000.0),
                "recommended_budget": campaign["data"].get("budget", 1000.0) * adjustment_factor,
                "performance_score": performance_score,
                "reasoning": f"Based on {objective} performance with CPA: ${metrics['cpa']:.2f}, CTR: {metrics['ctr']:.2%}",
                "confidence": random.uniform(0.7, 0.95)
            }
    
    def _optimize_ad_creatives(self):
        """Use ML to optimize ad creatives based on performance."""
        # Identify top and bottom performing ads
        top_ads = []
        bottom_ads = []
        
        for campaign in self.campaigns:
            if "ad_sets" not in campaign:
                continue
            
            for ad_set in campaign["ad_sets"]:
                if "ads" not in ad_set:
                    continue
                
                for ad in ad_set["ads"]:
                    if ad["metrics"]["impressions"] < 100:
                        continue
                    
                    ctr = ad["metrics"]["clicks"] / ad["metrics"]["impressions"] if ad["metrics"]["impressions"] > 0 else 0
                    
                    ad_info = {
                        "id": ad["id"],
                        "ad_set_id": ad_set["id"],
                        "campaign_id": campaign["id"],
                        "ctr": ctr,
                        "format": ad["data"].get("format", "single_image"),
                        "platform": self._get_primary_platform_for_ad(ad, ad_set)
                    }
                    
                    if ctr > 0.03:
                        top_ads.append(ad_info)
                    elif ctr < 0.01:
                        bottom_ads.append(ad_info)
        
        # Create creative optimization recommendations
        if "optimizations" not in self.results:
            self.results["optimizations"] = {}
        
        if "creatives" not in self.results["optimizations"]:
            self.results["optimizations"]["creatives"] = {"insights": [], "actions": []}
        
        # Extract patterns from top performing ads
        top_formats = {}
        top_platforms = {}
        
        for ad in top_ads:
            format_key = ad["format"]
            top_formats[format_key] = top_formats.get(format_key, 0) + 1
            
            platform_key = ad["platform"]
            top_platforms[platform_key] = top_platforms.get(platform_key, 0) + 1
        
        # Add insights
        if top_formats:
            best_format = max(top_formats.items(), key=lambda x: x[1])[0]
            self.results["optimizations"]["creatives"]["insights"].append(
                f"Top performing creative format: {best_format} with average CTR: {sum(ad['ctr'] for ad in top_ads if ad['format'] == best_format) / top_formats[best_format]:.2%}"
            )
        
        if top_platforms:
            best_platform = max(top_platforms.items(), key=lambda x: x[1])[0]
            self.results["optimizations"]["creatives"]["insights"].append(
                f"Top performing platform: {best_platform} with average CTR: {sum(ad['ctr'] for ad in top_ads if ad['platform'] == best_platform) / top_platforms[best_platform]:.2%}"
            )
        
        # Add recommended actions
        for ad in bottom_ads[:5]:  # Limit to 5 recommendations
            self.results["optimizations"]["creatives"]["actions"].append({
                "ad_id": ad["id"],
                "action": "Replace underperforming creative",
                "current_ctr": ad["ctr"],
                "benchmark_ctr": self.historical_data["platform_benchmarks"][ad["platform"]]["ctr"],
                "recommended_format": max(top_formats.items(), key=lambda x: x[1])[0] if top_formats else "video"
            })
    
    def _get_primary_platform_for_ad(self, ad, ad_set):
        """Determine primary platform for an ad based on placements."""
        placements = ad_set["data"].get("placements", ["feed"])
        if not isinstance(placements, list):
            placements = [placements]
        
        # Count by platform
        platform_counts = {"facebook": 0, "instagram": 0, "whatsapp": 0}
        
        for placement in placements:
            placement_info = self.placement_factors.get(placement, {"platform": "facebook"})
            platform = placement_info["platform"]
            platform_counts[platform] += 1
        
        # Return the platform with most placements
        return max(platform_counts.items(), key=lambda x: x[1])[0]
    
    def _optimize_platform_allocation(self):
        """Optimize allocation across Facebook, Instagram, and WhatsApp."""
        platform_performance = {
            "facebook": {"impressions": 0, "clicks": 0, "conversions": 0, "spend": 0},
            "instagram": {"impressions": 0, "clicks": 0, "conversions": 0, "spend": 0},
            "whatsapp": {"impressions": 0, "clicks": 0, "conversions": 0, "spend": 0}
        }
        
        # Aggregate performance by platform
        for campaign_id, metrics in self.results["campaigns"].items():
            platform_breakdown = metrics.get("platform_breakdown", {
                "facebook": 0.6, "instagram": 0.3, "whatsapp": 0.1
            })
            
            for platform, percentage in platform_breakdown.items():
                platform_performance[platform]["impressions"] += metrics["impressions"] * percentage
                platform_performance[platform]["clicks"] += metrics["clicks"] * percentage
                platform_performance[platform]["conversions"] += metrics["conversions"] * percentage
                platform_performance[platform]["spend"] += metrics["spend"] * percentage
        
        # Calculate performance metrics by platform
        platform_metrics = {}
        
        for platform, data in platform_performance.items():
            ctr = data["clicks"] / data["impressions"] if data["impressions"] > 0 else 0
            cpa = data["spend"] / data["conversions"] if data["conversions"] > 0 else float('inf')
            cpm = (data["spend"] * 1000) / data["impressions"] if data["impressions"] > 0 else 0
            
            platform_metrics[platform] = {
                "ctr": ctr,
                "cpa": cpa,
                "cpm": cpm,
                "efficiency_score": (ctr * 100) / (cpa + 0.1) if cpa > 0 else ctr * 100
            }
        
        # Create platform allocation recommendations
        if "optimizations" not in self.results:
            self.results["optimizations"] = {}
        
        self.results["optimizations"]["platform_allocation"] = {
            "current_allocation": {
                platform: self.results["total_metrics"]["platform_summary"].get(platform, 0)
                for platform in ["facebook", "instagram", "whatsapp"]
            },
            "recommended_allocation": {},
            "platform_metrics": platform_metrics,
            "reasoning": []
        }
        
        # Calculate recommended allocation based on performance
        total_efficiency = sum(m["efficiency_score"] for m in platform_metrics.values())
        
        if total_efficiency > 0:
            for platform, metrics in platform_metrics.items():
                # Base allocation on efficiency score
                recommended = metrics["efficiency_score"] / total_efficiency
                
                # Ensure minimum allocation and round
                recommended = max(0.1, recommended)
                
                self.results["optimizations"]["platform_allocation"]["recommended_allocation"][platform] = recommended
                
                # Add reasoning
                current = self.results["optimizations"]["platform_allocation"]["current_allocation"][platform]
                change = recommended - current
                
                if abs(change) > 0.05:  # Only mention significant changes
                    direction = "Increase" if change > 0 else "Decrease"
                    self.results["optimizations"]["platform_allocation"]["reasoning"].append(
                        f"{direction} {platform} allocation from {current:.1%} to {recommended:.1%} due to {'high' if change > 0 else 'low'} performance (CTR: {metrics['ctr']:.2%}, CPA: ${metrics['cpa']:.2f})"
                    )
        
        # Normalize recommended allocation to sum to 1
        total_recommended = sum(self.results["optimizations"]["platform_allocation"]["recommended_allocation"].values())
        
        if total_recommended > 0:
            for platform in self.results["optimizations"]["platform_allocation"]["recommended_allocation"]:
                self.results["optimizations"]["platform_allocation"]["recommended_allocation"][platform] /= total_recommended
    
    # Async methods for batch operations
    async def async_batch_update(self, updates):
        """Simulate async batch update of multiple campaigns/ad sets/ads."""
        result = {"success": [], "failed": []}
        
        # Simulate API latency
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        for update in updates:
            try:
                if update["type"] == "campaign":
                    # Update campaign
                    for campaign in self.campaigns:
                        if campaign["id"] == update["id"]:
                            if "status" in update["data"]:
                                campaign["status"] = update["data"]["status"]
                            if "budget" in update["data"]:
                                campaign["data"]["budget"] = update["data"]["budget"]
                            result["success"].append({"id": update["id"], "type": "campaign"})
                            break
                
                elif update["type"] == "ad_set":
                    # Update ad set
                    for campaign in self.campaigns:
                        if "ad_sets" not in campaign:
                            continue
                        
                        for ad_set in campaign["ad_sets"]:
                            if ad_set["id"] == update["id"]:
                                if "status" in update["data"]:
                                    ad_set["status"] = update["data"]["status"]
                                if "budget" in update["data"]:
                                    ad_set["data"]["budget"] = update["data"]["budget"]
                                result["success"].append({"id": update["id"], "type": "ad_set"})
                                break
                
                elif update["type"] == "ad":
                    # Update ad
                    for campaign in self.campaigns:
                        if "ad_sets" not in campaign:
                            continue
                        
                        for ad_set in campaign["ad_sets"]:
                            if "ads" not in ad_set:
                                continue
                            
                            for ad in ad_set["ads"]:
                                if ad["id"] == update["id"]:
                                    if "status" in update["data"]:
                                        ad["status"] = update["data"]["status"]
                                    result["success"].append({"id": update["id"], "type": "ad"})
                                    break
                
                else:
                    # Unknown type
                    result["failed"].append({
                        "id": update["id"],
                        "type": update["type"],
                        "error": "Unknown update type"
                    })
            
            except Exception as e:
                # Simulate random failures
                if random.random() < 0.05:  # 5% chance of failure
                    result["failed"].append({
                        "id": update.get("id", "unknown"),
                        "type": update.get("type", "unknown"),
                        "error": str(e)
                    })
        
        return result
    
    def simulate_engagement(self, platform: str, historical_data: pd.DataFrame) -> float:
        """
        Simulate engagement rates based on historical data and platform characteristics.
        
        Args:
            platform: The Meta platform to simulate (facebook, instagram, whatsapp)
            historical_data: DataFrame containing historical performance metrics
            
        Returns:
            Predicted engagement rate as a float
        """
        if platform not in self.platforms:
            raise ValueError(f"Unknown platform: {platform}. Must be one of {list(self.platforms.keys())}")
        
        if historical_data.empty:
            # Use platform benchmarks if no historical data
            if platform == "facebook":
                return random.uniform(0.01, 0.03)
            elif platform == "instagram":
                return random.uniform(0.02, 0.04)
            elif platform == "whatsapp":
                return random.uniform(0.03, 0.06)
        
        # Extract relevant features from historical data
        try:
            # Basic engagement model based on historical CTR with platform adjustment
            base_ctr = historical_data['clicks'].sum() / historical_data['impressions'].sum()
            
            # Apply platform-specific adjustments
            if platform == "facebook":
                return base_ctr * random.uniform(0.9, 1.1)
            elif platform == "instagram":
                return base_ctr * random.uniform(1.1, 1.3)  # Instagram typically has higher engagement
            elif platform == "whatsapp":
                return base_ctr * random.uniform(1.3, 1.6)  # WhatsApp has highest engagement when relevant
            
        except (KeyError, ZeroDivisionError):
            # Fallback to platform benchmarks
            return self.historical_data["platform_benchmarks"][platform]["ctr"]
    
    def optimize_budget(self, real_time_metrics: dict) -> dict:
        """
        Optimize budget allocation across platforms based on real-time metrics.
        
        Args:
            real_time_metrics: Dictionary containing current performance metrics
            
        Returns:
            Dictionary with recommended budget allocations by platform
        """
        # Extract current performance by platform
        platform_performance = {}
        for platform in self.platforms:
            if platform in real_time_metrics:
                metrics = real_time_metrics[platform]
                
                # Calculate efficiency score based on conversions and cost
                conversions = metrics.get('conversions', 0)
                spend = metrics.get('spend', 0.01)  # Avoid division by zero
                cpa = spend / conversions if conversions > 0 else float('inf')
                
                # Weighted score based on platform objectives
                if platform == "facebook":
                    efficiency = (1 / cpa) if cpa > 0 else 0
                elif platform == "instagram":
                    # For Instagram, also consider engagement rate
                    engagement = metrics.get('engagement_rate', 0)
                    efficiency = (1 / cpa) * (1 + engagement) if cpa > 0 else engagement
                elif platform == "whatsapp":
                    # For WhatsApp, prioritize conversation starts
                    conversation_rate = metrics.get('conversation_rate', 0)
                    efficiency = (1 / cpa) * (1 + conversation_rate * 2) if cpa > 0 else conversation_rate
                
                platform_performance[platform] = {
                    'efficiency': efficiency,
                    'current_budget': metrics.get('budget', 0)
                }
        
        # Calculate optimal budget allocation
        total_efficiency = sum(p['efficiency'] for p in platform_performance.values())
        total_budget = sum(p['current_budget'] for p in platform_performance.values())
        
        recommendations = {}
        
        if total_efficiency > 0:
            for platform, perf in platform_performance.items():
                # Allocate budget proportionally to efficiency
                ideal_share = perf['efficiency'] / total_efficiency
                
                # Ensure minimum allocation
                min_allocation = 0.1  # Minimum 10% to any platform
                if ideal_share < min_allocation:
                    ideal_share = min_allocation
                
                recommendations[platform] = {
                    'current_budget': perf['current_budget'],
                    'recommended_budget': total_budget * ideal_share,
                    'change_percentage': ((total_budget * ideal_share / perf['current_budget']) - 1) * 100 if perf['current_budget'] > 0 else 100
                }
        
        # Normalize recommendations to maintain total budget
        total_recommended = sum(r['recommended_budget'] for r in recommendations.values())
        if total_recommended > 0 and abs(total_recommended - total_budget) > 0.01:
            scaling_factor = total_budget / total_recommended
            for platform in recommendations:
                recommendations[platform]['recommended_budget'] *= scaling_factor
                recommendations[platform]['change_percentage'] = ((recommendations[platform]['recommended_budget'] / recommendations[platform]['current_budget']) - 1) * 100 if recommendations[platform]['current_budget'] > 0 else 100
        
        return recommendations
    
    def _calculate_advantage_plus_performance(self, campaign_id):
        """Calculate performance metrics for Advantage+ creatives (new in v22.0)."""
        advantage_plus_performance = {
            "enabled": False,
            "metrics": {
                "impressions": 0,
                "clicks": 0,
                "conversions": 0,
                "spend": 0.0
            },
            "performance_lift": 0.0,
            "top_combinations": []
        }
        
        for campaign in self.campaigns:
            if campaign["id"] == campaign_id:
                # Check if Advantage+ is enabled for this campaign
                advantage_plus_enabled = campaign["data"].get("advantage_plus_creative", False)
                if not advantage_plus_enabled:
                    return advantage_plus_performance
                
                advantage_plus_performance["enabled"] = True
                
                # Calculate baseline performance
                baseline_impressions = 0
                baseline_clicks = 0
                baseline_conversions = 0
                baseline_spend = 0.0
                
                # Calculate Advantage+ performance
                advantage_impressions = 0
                advantage_clicks = 0
                advantage_conversions = 0
                advantage_spend = 0.0
                
                # Extract assets used in Advantage+
                asset_combinations = []
                
                if "ad_sets" in campaign:
                    for ad_set in campaign["ad_sets"]:
                        for ad in ad_set.get("ads", []):
                            # Check if ad is an Advantage+ creative
                            is_advantage_plus = ad["data"].get("is_advantage_plus", False)
                            
                            # Calculate metrics
                            impressions = ad["metrics"]["impressions"]
                            clicks = ad["metrics"]["clicks"]
                            conversions = ad["metrics"]["conversions"]
                            spend = ad["metrics"]["spend"]
                            
                            if is_advantage_plus:
                                advantage_impressions += impressions
                                advantage_clicks += clicks
                                advantage_conversions += conversions
                                advantage_spend += spend
                                
                                # Track asset combinations
                                assets = ad["data"].get("assets", {})
                                if assets:
                                    asset_combinations.append({
                                        "id": ad["id"],
                                        "assets": assets,
                                        "ctr": clicks / impressions if impressions > 0 else 0
                                    })
                            else:
                                baseline_impressions += impressions
                                baseline_clicks += clicks
                                baseline_conversions += conversions
                                baseline_spend += spend
                
                # Calculate performance lift if we have both baseline and advantage+ ads
                if baseline_impressions > 0 and advantage_impressions > 0:
                    baseline_ctr = baseline_clicks / baseline_impressions
                    advantage_ctr = advantage_clicks / advantage_impressions
                    
                    ctr_lift = (advantage_ctr - baseline_ctr) / baseline_ctr if baseline_ctr > 0 else 0
                    
                    baseline_cvr = baseline_conversions / baseline_clicks if baseline_clicks > 0 else 0
                    advantage_cvr = advantage_conversions / advantage_clicks if advantage_clicks > 0 else 0
                    
                    cvr_lift = (advantage_cvr - baseline_cvr) / baseline_cvr if baseline_cvr > 0 else 0
                    
                    # Average lift across metrics
                    average_lift = (ctr_lift + cvr_lift) / 2
                    advantage_plus_performance["performance_lift"] = average_lift
                
                # Store metrics
                advantage_plus_performance["metrics"] = {
                    "impressions": advantage_impressions,
                    "clicks": advantage_clicks,
                    "conversions": advantage_conversions,
                    "spend": advantage_spend,
                    "ctr": advantage_clicks / advantage_impressions if advantage_impressions > 0 else 0,
                    "cvr": advantage_conversions / advantage_clicks if advantage_clicks > 0 else 0
                }
                
                # Sort and get top asset combinations
                if asset_combinations:
                    asset_combinations.sort(key=lambda x: x["ctr"], reverse=True)
                    advantage_plus_performance["top_combinations"] = asset_combinations[:3]
        
        return advantage_plus_performance
    
    def _calculate_advantage_plus_adoption(self):
        """Calculate overall adoption rate of Advantage+ creative feature (v22.0)."""
        total_campaigns = len(self.campaigns)
        if total_campaigns == 0:
            return 0.0
        
        advantage_plus_campaigns = 0
        for campaign in self.campaigns:
            if campaign["data"].get("advantage_plus_creative", False):
                advantage_plus_campaigns += 1
        
        return advantage_plus_campaigns / total_campaigns
    
    def _calculate_publisher_platform_breakdown(self, campaign_id):
        """Calculate detailed publisher_platform breakdown for cross-platform attribution (v22.0)."""
        breakdown = {
            "facebook": {
                "feed": 0,
                "marketplace": 0,
                "video": 0,
                "right_column": 0,
                "search": 0,
                "instant_articles": 0
            },
            "instagram": {
                "feed": 0,
                "stories": 0,
                "explore": 0,
                "reels": 0,
                "shop": 0,
                "threads": 0
            },
            "whatsapp": {
                "business": 0,
                "click_to_chat": 0,
                "status": 0
            }
        }
        
        for campaign in self.campaigns:
            if campaign["id"] == campaign_id and "ad_sets" in campaign:
                for ad_set in campaign["ad_sets"]:
                    # Skip inactive ad sets
                    if ad_set["status"] != "active":
                        continue
                    
                    # Get placements
                    placements = ad_set["data"].get("placements", ["feed"])
                    if not isinstance(placements, list):
                        placements = [placements]
                    
                    # Count impressions by placement
                    for placement in placements:
                        impressions = ad_set["metrics"]["impressions"] / len(placements)
                        
                        # Map placement to platform and sub-placement
                        placement_info = self.placement_factors.get(placement, {"platform": "facebook"})
                        platform = placement_info["platform"]
                        
                        if platform == "facebook":
                            if placement == "feed":
                                breakdown["facebook"]["feed"] += impressions
                            elif placement == "marketplace":
                                breakdown["facebook"]["marketplace"] += impressions
                            elif placement == "video":
                                breakdown["facebook"]["video"] += impressions
                            elif placement == "right_column":
                                breakdown["facebook"]["right_column"] += impressions
                            elif placement == "search":
                                breakdown["facebook"]["search"] += impressions
                            elif placement == "instant_articles":
                                breakdown["facebook"]["instant_articles"] += impressions
                            else:
                                breakdown["facebook"]["feed"] += impressions  # Default
                        
                        elif platform == "instagram":
                            if placement == "instagram_feed":
                                breakdown["instagram"]["feed"] += impressions
                            elif placement == "instagram_stories":
                                breakdown["instagram"]["stories"] += impressions
                            elif placement == "instagram_explore":
                                breakdown["instagram"]["explore"] += impressions
                            elif placement == "instagram_reels":
                                breakdown["instagram"]["reels"] += impressions
                            elif placement == "instagram_shop":
                                breakdown["instagram"]["shop"] += impressions
                            elif placement == "instagram_threads":
                                breakdown["instagram"]["threads"] += impressions
                            else:
                                breakdown["instagram"]["feed"] += impressions  # Default
                        
                        elif platform == "whatsapp":
                            if placement == "whatsapp_business":
                                breakdown["whatsapp"]["business"] += impressions
                            elif placement == "whatsapp_click_to_chat":
                                breakdown["whatsapp"]["click_to_chat"] += impressions
                            elif placement == "whatsapp_status":
                                breakdown["whatsapp"]["status"] += impressions
                            else:
                                breakdown["whatsapp"]["business"] += impressions  # Default
        
        # Calculate percentages
        total_impressions = sum(sum(values.values()) for values in breakdown.values())
        
        if total_impressions > 0:
            for platform in breakdown:
                for placement in breakdown[platform]:
                    breakdown[platform][placement] = breakdown[platform][placement] / total_impressions
        
        return breakdown
    
    def _calculate_cross_platform_lift(self):
        """Calculate cross-platform performance lift (v22.0 feature)."""
        # Initialize platform-specific metrics
        platform_metrics = {
            "facebook": {"impressions": 0, "clicks": 0, "conversions": 0},
            "instagram": {"impressions": 0, "clicks": 0, "conversions": 0},
            "whatsapp": {"impressions": 0, "clicks": 0, "conversions": 0},
            "cross_platform": {"impressions": 0, "clicks": 0, "conversions": 0}
        }
        
        # Collect campaigns using multiple platforms
        cross_platform_campaigns = []
        single_platform_campaigns = {"facebook": [], "instagram": [], "whatsapp": []}
        
        for campaign in self.campaigns:
            if "ad_sets" not in campaign:
                continue
            
            # Check which platforms are used in this campaign
            used_platforms = set()
            
            for ad_set in campaign["ad_sets"]:
                placements = ad_set["data"].get("placements", ["feed"])
                if not isinstance(placements, list):
                    placements = [placements]
                
                for placement in placements:
                    placement_info = self.placement_factors.get(placement, {"platform": "facebook"})
                    used_platforms.add(placement_info["platform"])
            
            if len(used_platforms) > 1:
                cross_platform_campaigns.append(campaign["id"])
            elif len(used_platforms) == 1:
                platform = list(used_platforms)[0]
                single_platform_campaigns[platform].append(campaign["id"])
        
        # Aggregate metrics for each campaign type
        for campaign_id in cross_platform_campaigns:
            if campaign_id not in self.results["campaigns"]:
                continue
                
            metrics = self.results["campaigns"][campaign_id]
            platform_metrics["cross_platform"]["impressions"] += metrics["impressions"]
            platform_metrics["cross_platform"]["clicks"] += metrics["clicks"]
            platform_metrics["cross_platform"]["conversions"] += metrics["conversions"]
        
        for platform, campaign_ids in single_platform_campaigns.items():
            for campaign_id in campaign_ids:
                if campaign_id not in self.results["campaigns"]:
                    continue
                    
                metrics = self.results["campaigns"][campaign_id]
                platform_metrics[platform]["impressions"] += metrics["impressions"]
                platform_metrics[platform]["clicks"] += metrics["clicks"]
                platform_metrics[platform]["conversions"] += metrics["conversions"]
        
        # Calculate CTR and CVR for each platform type
        for platform, metrics in platform_metrics.items():
            if metrics["impressions"] > 0:
                metrics["ctr"] = metrics["clicks"] / metrics["impressions"]
            else:
                metrics["ctr"] = 0
                
            if metrics["clicks"] > 0:
                metrics["cvr"] = metrics["conversions"] / metrics["clicks"]
            else:
                metrics["cvr"] = 0
        
        # Calculate lift compared to average of single-platform campaigns
        lift_data = {"ctr_lift": 0, "cvr_lift": 0}
        
        # Only calculate if we have both cross-platform and single-platform campaigns
        if platform_metrics["cross_platform"]["impressions"] > 0:
            single_platform_ctr_sum = 0
            single_platform_cvr_sum = 0
            single_platform_count = 0
            
            for platform in ["facebook", "instagram", "whatsapp"]:
                if platform_metrics[platform]["impressions"] > 0:
                    single_platform_ctr_sum += platform_metrics[platform]["ctr"]
                    single_platform_cvr_sum += platform_metrics[platform]["cvr"]
                    single_platform_count += 1
            
            if single_platform_count > 0:
                avg_single_platform_ctr = single_platform_ctr_sum / single_platform_count
                avg_single_platform_cvr = single_platform_cvr_sum / single_platform_count
                
                cross_platform_ctr = platform_metrics["cross_platform"]["ctr"]
                cross_platform_cvr = platform_metrics["cross_platform"]["cvr"]
                
                # Calculate lift
                if avg_single_platform_ctr > 0:
                    lift_data["ctr_lift"] = (cross_platform_ctr - avg_single_platform_ctr) / avg_single_platform_ctr
                
                if avg_single_platform_cvr > 0:
                    lift_data["cvr_lift"] = (cross_platform_cvr - avg_single_platform_cvr) / avg_single_platform_cvr
        
        # Add platform-specific metrics and lift data
        return {
            "platform_metrics": platform_metrics,
            "lift": lift_data,
            "cross_platform_campaign_count": len(cross_platform_campaigns),
            "single_platform_campaign_counts": {
                platform: len(campaigns) for platform, campaigns in single_platform_campaigns.items()
            }
        }
