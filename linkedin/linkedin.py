import random
from datetime import datetime, timedelta
import sys
import os
import time
import uuid
import json

# Add parent directory to path to import base_simulator
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_simulator import BaseAdSimulator

class LinkedInAdsSimulator(BaseAdSimulator):
    """Digital twin simulator for LinkedIn Ads platform."""
    
    def __init__(self, config=None):
        super().__init__("LinkedInAds", config)
        
        # LinkedIn ad formats based on actual offerings
        self.ad_formats = {
            "single_image_sponsored_content": {"ctr_multiplier": 1.0, "cpm_base": 8.5},
            "carousel_sponsored_content": {"ctr_multiplier": 1.2, "cpm_base": 9.5},
            "video_sponsored_content": {"ctr_multiplier": 1.5, "cpm_base": 10.0},
            "message_ads": {"ctr_multiplier": 3.0, "cpm_base": 25.0},
            "text_ads": {"ctr_multiplier": 0.5, "cpm_base": 5.0},
            "dynamic_ads": {"ctr_multiplier": 0.8, "cpm_base": 7.0},
            "conversation_ads": {"ctr_multiplier": 2.5, "cpm_base": 20.0},
            "document_ads": {"ctr_multiplier": 0.9, "cpm_base": 8.0},
            "event_ads": {"ctr_multiplier": 1.1, "cpm_base": 9.0}
        }
        
        # LinkedIn targeting dimensions based on API capabilities
        self.targeting_dimensions = [
            "job_title", "job_function", "industry", "company_size",
            "seniority", "skills", "education", "interests", "groups",
            "company", "company_connections", "company_followers", 
            "location", "language", "years_of_experience"
        ]
        
        # LinkedIn campaign objectives
        self.campaign_objectives = [
            "WEBSITE_VISITS", "LEAD_GENERATION", "ENGAGEMENT", 
            "VIDEO_VIEWS", "BRAND_AWARENESS", "WEBSITE_CONVERSIONS",
            "JOB_APPLICANTS"
        ]
        
        # Bidding strategies
        self.bidding_strategies = {
            "CPC": "Cost Per Click",
            "CPM": "Cost Per 1000 Impressions",
            "AUTO": "Automated Bidding",
            "COST_CAP": "Cost Cap (for Lead Gen)"
        }
        
        # Initialize webhook events
        self.webhooks = {
            "lead_form_submit": [],
            "message_open": [],
            "social_action": []  # For likes, comments, shares
        }
        
        # Rate limiting configuration
        self.rate_limits = {
            "calls_per_day": 100000,
            "calls_per_minute": 300,
            "current_day_calls": 0,
            "current_minute_calls": 0,
            "last_minute_reset": datetime.now(),
            "last_day_reset": datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        }
        
        # OAuth token simulation
        self.oauth = {
            "access_token": str(uuid.uuid4()),
            "refresh_token": str(uuid.uuid4()),
            "expires_at": datetime.now() + timedelta(days=60)
        }
    
    def create_creative(self, campaign_id, creative_data):
        """Create a creative within a campaign."""
        # Check rate limits before proceeding
        if not self._check_rate_limits():
            raise Exception("RATE_LIMITED: API call limit exceeded. Please try again later.")
        
        # Validate access token
        if not self._validate_token():
            raise Exception("INVALID_ACCESS_TOKEN: The access token is invalid or has expired.")
            
        for campaign in self.campaigns:
            if campaign["id"] == campaign_id:
                if "creatives" not in campaign:
                    campaign["creatives"] = []
                
                creative_id = f"{campaign_id}-cr-{len(campaign['creatives']) + 1}"
                
                # Validate creative format against campaign objective
                campaign_objective = campaign["data"].get("objective", "WEBSITE_VISITS")
                creative_format = creative_data.get("format", "single_image_sponsored_content")
                
                # Check if the creative format is compatible with the campaign objective
                if not self._is_format_compatible_with_objective(creative_format, campaign_objective):
                    raise ValueError(f"Creative format '{creative_format}' is not compatible with campaign objective '{campaign_objective}'")
                
                # Check creative specifications
                self._validate_creative_specs(creative_data)
                
                creative = {
                    "id": creative_id,
                    "data": creative_data,
                    "status": "active",
                    "review_status": "pending_review",
                    "created_at": datetime.now().isoformat(),
                    "serving_hold_reasons": []
                }
                
                # Simulate the review process
                self._simulate_creative_review(creative)
                
                campaign["creatives"].append(creative)
                return creative_id
        
        raise ValueError(f"Campaign {campaign_id} not found")
    
    def _validate_token(self):
        """Validate the OAuth access token."""
        if datetime.now() > self.oauth["expires_at"]:
            # Token has expired
            # In a real implementation, we would attempt to refresh the token here
            return False
        return True
    
    def refresh_token(self):
        """Simulate refreshing an OAuth token."""
        if datetime.now() > self.oauth["expires_at"] + timedelta(days=365):
            # Refresh token has also expired
            raise Exception("Refresh token has expired. User must re-authenticate.")
        
        # Generate new tokens
        self.oauth = {
            "access_token": str(uuid.uuid4()),
            "refresh_token": str(uuid.uuid4()),
            "expires_at": datetime.now() + timedelta(days=60)
        }
        
        return self.oauth
    
    def _check_rate_limits(self):
        """Check if the current request exceeds rate limits."""
        now = datetime.now()
        
        # Reset day counter if needed
        if now.date() > self.rate_limits["last_day_reset"].date():
            self.rate_limits["current_day_calls"] = 0
            self.rate_limits["last_day_reset"] = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Reset minute counter if needed
        minute_diff = (now - self.rate_limits["last_minute_reset"]).total_seconds() / 60
        if minute_diff >= 1:
            self.rate_limits["current_minute_calls"] = 0
            self.rate_limits["last_minute_reset"] = now
        
        # Increment counters
        self.rate_limits["current_day_calls"] += 1
        self.rate_limits["current_minute_calls"] += 1
        
        # Check if limits are exceeded
        if self.rate_limits["current_day_calls"] > self.rate_limits["calls_per_day"]:
            return False
        
        if self.rate_limits["current_minute_calls"] > self.rate_limits["calls_per_minute"]:
            return False
        
        return True
    
    def _is_format_compatible_with_objective(self, format_type, objective):
        """Check if the creative format is compatible with the campaign objective."""
        # Define format compatibility with objectives
        compatibility_map = {
            "WEBSITE_VISITS": ["single_image_sponsored_content", "carousel_sponsored_content", 
                              "video_sponsored_content", "text_ads", "dynamic_ads", "event_ads"],
            "LEAD_GENERATION": ["single_image_sponsored_content", "carousel_sponsored_content", 
                               "video_sponsored_content", "message_ads", "conversation_ads", "document_ads"],
            "ENGAGEMENT": ["single_image_sponsored_content", "carousel_sponsored_content", 
                          "video_sponsored_content", "dynamic_ads", "conversation_ads", "document_ads", "event_ads"],
            "VIDEO_VIEWS": ["video_sponsored_content"],
            "BRAND_AWARENESS": ["single_image_sponsored_content", "carousel_sponsored_content", 
                              "video_sponsored_content", "dynamic_ads"],
            "WEBSITE_CONVERSIONS": ["single_image_sponsored_content", "carousel_sponsored_content", 
                                  "video_sponsored_content", "dynamic_ads"],
            "JOB_APPLICANTS": ["single_image_sponsored_content", "job_ads"]
        }
        
        return format_type in compatibility_map.get(objective, [])
    
    def _validate_creative_specs(self, creative_data):
        """Validate creative specifications based on format."""
        format_type = creative_data.get("format", "single_image_sponsored_content")
        
        if format_type == "single_image_sponsored_content":
            # Check image dimensions, file size, character limits, etc.
            if "intro_text" in creative_data and len(creative_data["intro_text"]) > 600:
                raise ValueError("Intro text exceeds 600 character limit for Single Image ads")
            
            if "headline" in creative_data and len(creative_data["headline"]) > 70:
                raise ValueError("Headline exceeds 70 character limit for Single Image ads")
        
        elif format_type == "carousel_sponsored_content":
            # Check number of cards, image dimensions, character limits, etc.
            if "cards" in creative_data:
                if len(creative_data["cards"]) < 2 or len(creative_data["cards"]) > 10:
                    raise ValueError("Carousel ads must have between 2 and 10 cards")
                
                for card in creative_data["cards"]:
                    if "headline" in card and len(card["headline"]) > 45:
                        raise ValueError("Card headline exceeds 45 character limit for Carousel ads")
            
            if "intro_text" in creative_data and len(creative_data["intro_text"]) > 255:
                raise ValueError("Intro text exceeds 255 character limit for Carousel ads")
        
        elif format_type == "video_sponsored_content":
            # Check video duration, file size, dimensions, etc.
            if "video_duration" in creative_data:
                duration_sec = creative_data["video_duration"]
                if duration_sec < 3 or duration_sec > 1800:  # 3 seconds to 30 minutes
                    raise ValueError("Video duration must be between 3 seconds and 30 minutes")
                
            if "intro_text" in creative_data and len(creative_data["intro_text"]) > 600:
                raise ValueError("Intro text exceeds 600 character limit for Video ads")
        
        elif format_type == "message_ads":
            # Check subject line, message text, CTA character limits
            if "subject_line" in creative_data and len(creative_data["subject_line"]) > 60:
                raise ValueError("Subject line exceeds 60 character limit for Message ads")
                
            if "message_text" in creative_data and len(creative_data["message_text"]) > 1500:
                raise ValueError("Message text exceeds 1500 character limit for Message ads")
                
            if "cta_text" in creative_data and len(creative_data["cta_text"]) > 20:
                raise ValueError("CTA text exceeds 20 character limit for Message ads")
    
    def _simulate_creative_review(self, creative):
        """Simulate LinkedIn's ad review process."""
        # 90% of creatives pass review automatically
        if random.random() > 0.1:
            creative["review_status"] = "approved"
        else:
            creative["review_status"] = "rejected"
            # Possible rejection reasons
            rejection_reasons = [
                "POLICY_VIOLATION: Content violates LinkedIn advertising policies",
                "LOW_QUALITY: Image resolution is too low",
                "MISLEADING_CONTENT: Ad contains misleading claims",
                "EXCESSIVE_TEXT: Image contains too much text",
                "INAPPROPRIATE_CONTENT: Content is not appropriate for LinkedIn audience"
            ]
            creative["serving_hold_reasons"] = [random.choice(rejection_reasons)]
    
    def trigger_webhook(self, event_type, data):
        """Simulate a webhook event being triggered."""
        if event_type not in self.webhooks:
            raise ValueError(f"Unknown webhook event type: {event_type}")
        
        event_data = {
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        self.webhooks[event_type].append(event_data)
        return event_data
    
    def simulate_lead_form_submission(self, campaign_id, form_id, member_data):
        """Simulate a lead form submission event."""
        # Check if the campaign exists
        campaign = None
        for c in self.campaigns:
            if c["id"] == campaign_id:
                campaign = c
                break
                
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")
        
        # Create lead submission data
        lead_data = {
            "id": str(uuid.uuid4()),
            "form_id": form_id,
            "campaign_id": campaign_id,
            "member_data": {k: v for k, v in member_data.items() if k in ["email", "firstName", "lastName", "company", "jobTitle"]},
            "submission_time": datetime.now().isoformat()
        }
        
        # Trigger webhook event
        return self.trigger_webhook("lead_form_submit", lead_data)
    
    def simulate_message_open(self, message_id, member_id):
        """Simulate a message open event."""
        message_data = {
            "message_id": message_id,
            "member_id": member_id,
            "open_time": datetime.now().isoformat()
        }
        
        # Trigger webhook event
        return self.trigger_webhook("message_open", message_data)
    
    def _targeting_match_score(self, targeting):
        """Calculate how targeted an audience is (0-1 scale)."""
        score = 0
        used_dimensions = 0
        
        for dimension in self.targeting_dimensions:
            if dimension in targeting and targeting[dimension]:
                score += 1
                used_dimensions += 1
        
        # If no targeting dimensions are used, return a low base score
        if used_dimensions == 0:
            return 0.2
            
        # Calculate score with a bonus for using multiple dimensions
        base_score = score / len(self.targeting_dimensions)
        multi_dimension_bonus = min(used_dimensions / 5, 1.0) * 0.2
        
        return min(base_score + multi_dimension_bonus, 1.0)
    
    def _calculate_bid_competitiveness(self, bid, format_type):
        """Calculate how competitive a bid is compared to market averages."""
        format_data = self.ad_formats.get(format_type, self.ad_formats["single_image_sponsored_content"])
        market_average = format_data["cpm_base"]
        
        if bid >= market_average * 1.5:
            return 1.0  # Very competitive
        elif bid >= market_average * 1.2:
            return 0.9  # Highly competitive
        elif bid >= market_average:
            return 0.7  # Competitive
        elif bid >= market_average * 0.8:
            return 0.5  # Somewhat competitive
        else:
            return 0.3  # Less competitive
    
    def get_analytics(self, campaign_ids=None, start_date=None, end_date=None, time_granularity="DAILY"):
        """Get analytics data with time granularity support."""
        if not self._check_rate_limits():
            raise Exception("RATE_LIMITED: API call limit exceeded. Please try again later.")
            
        # Validate parameters
        valid_granularities = ["DAILY", "MONTHLY", "YEARLY", "ALL"]
        if time_granularity not in valid_granularities:
            raise ValueError(f"Invalid time_granularity: {time_granularity}. Must be one of {valid_granularities}")
            
        # Default date range if not provided
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).date()
        if not end_date:
            end_date = datetime.now().date()
            
        # Filter campaigns if campaign_ids is provided
        target_campaigns = []
        if campaign_ids:
            for campaign in self.campaigns:
                if campaign["id"] in campaign_ids:
                    target_campaigns.append(campaign)
        else:
            target_campaigns = self.campaigns
            
        analytics_data = []
        
        # Process each campaign
        for campaign in target_campaigns:
            campaign_id = campaign["id"]
            if campaign_id not in self.results["campaigns"]:
                continue
                
            campaign_results = self.results["campaigns"][campaign_id]
            
            # Process based on time granularity
            if time_granularity == "ALL":
                # Return single aggregated result
                analytics_data.append({
                    "campaign_id": campaign_id,
                    "time_range": f"{start_date} to {end_date}",
                    "metrics": campaign_results
                })
            else:
                # Generate time-series data based on granularity
                current_date = start_date
                date_format = "%Y-%m-%d" if time_granularity == "DAILY" else "%Y-%m" if time_granularity == "MONTHLY" else "%Y"
                
                while current_date <= end_date:
                    # Calculate metrics for this time period
                    period_factor = random.uniform(0.8, 1.2)
                    
                    if time_granularity == "DAILY":
                        # Daily data
                        day_metrics = {
                            "impressions": int(campaign_results["impressions"] / 30 * period_factor),
                            "clicks": int(campaign_results["clicks"] / 30 * period_factor),
                            "conversions": int(campaign_results["conversions"] / 30 * period_factor),
                            "spend": round(campaign_results["spend"] / 30 * period_factor, 2)
                        }
                        
                        # Add derived metrics
                        day_metrics["ctr"] = day_metrics["clicks"] / day_metrics["impressions"] if day_metrics["impressions"] > 0 else 0
                        day_metrics["cpa"] = day_metrics["spend"] / day_metrics["conversions"] if day_metrics["conversions"] > 0 else 0
                        
                        analytics_data.append({
                            "campaign_id": campaign_id,
                            "date": current_date.strftime(date_format),
                            "metrics": day_metrics
                        })
                        
                        current_date += timedelta(days=1)
                    
                    elif time_granularity == "MONTHLY":
                        # Monthly data
                        month_metrics = {
                            "impressions": int(campaign_results["impressions"] / 12 * period_factor),
                            "clicks": int(campaign_results["clicks"] / 12 * period_factor),
                            "conversions": int(campaign_results["conversions"] / 12 * period_factor),
                            "spend": round(campaign_results["spend"] / 12 * period_factor, 2)
                        }
                        
                        # Add derived metrics
                        month_metrics["ctr"] = month_metrics["clicks"] / month_metrics["impressions"] if month_metrics["impressions"] > 0 else 0
                        month_metrics["cpa"] = month_metrics["spend"] / month_metrics["conversions"] if month_metrics["conversions"] > 0 else 0
                        
                        analytics_data.append({
                            "campaign_id": campaign_id,
                            "date": current_date.strftime(date_format),
                            "metrics": month_metrics
                        })
                        
                        # Move to next month
                        if current_date.month == 12:
                            current_date = current_date.replace(year=current_date.year + 1, month=1)
                        else:
                            current_date = current_date.replace(month=current_date.month + 1)
                    
                    elif time_granularity == "YEARLY":
                        # Yearly data
                        year_metrics = {
                            "impressions": int(campaign_results["impressions"] * period_factor),
                            "clicks": int(campaign_results["clicks"] * period_factor),
                            "conversions": int(campaign_results["conversions"] * period_factor),
                            "spend": round(campaign_results["spend"] * period_factor, 2)
                        }
                        
                        # Add derived metrics
                        year_metrics["ctr"] = year_metrics["clicks"] / year_metrics["impressions"] if year_metrics["impressions"] > 0 else 0
                        year_metrics["cpa"] = year_metrics["spend"] / year_metrics["conversions"] if year_metrics["conversions"] > 0 else 0
                        
                        analytics_data.append({
                            "campaign_id": campaign_id,
                            "date": current_date.strftime(date_format),
                            "metrics": year_metrics
                        })
                        
                        # Move to next year
                        current_date = current_date.replace(year=current_date.year + 1)
        
        return analytics_data
    
    def _run_platform_simulation(self, days, speed_factor):
        """Run LinkedIn Ads-specific simulation."""
        total_impressions = 0
        total_clicks = 0
        total_conversions = 0
        total_spend = 0.0
        
        for campaign in self.campaigns:
            campaign_id = campaign["id"]
            campaign_data = campaign["data"]
            campaign_type = campaign_data.get("type", "single_image_sponsored_content")
            campaign_objective = campaign_data.get("objective", "WEBSITE_VISITS")
            daily_budget = campaign_data.get("daily_budget", 100.0)
            total_budget = campaign_data.get("total_budget", daily_budget * days)
            bid_strategy = campaign_data.get("bid_strategy", "AUTO")
            bid_amount = campaign_data.get("bid_amount", 0.0)
            
            # Initialize campaign metrics
            campaign_impressions = 0
            campaign_clicks = 0
            campaign_conversions = 0
            campaign_spend = 0.0
            
            # Skip inactive campaigns
            if campaign["status"] != "active":
                continue
            
            # Process targeting
            targeting = campaign_data.get("targeting", {})
            targeting_score = self._targeting_match_score(targeting)
            
            # Process creatives
            if "creatives" not in campaign or not campaign["creatives"]:
                # Skip campaigns with no creatives
                continue
                
            active_creatives = [c for c in campaign["creatives"] 
                              if c["status"] == "active" 
                              and c["review_status"] == "approved"]
            
            if not active_creatives:
                # Skip if no active and approved creatives
                continue
            
            # Get ad format data
            format_data = self.ad_formats.get(campaign_type, self.ad_formats["single_image_sponsored_content"])
            
            # Calculate bid competitiveness
            if bid_strategy == "AUTO":
                # Auto bidding uses market average
                bid_competitiveness = 0.7
            else:
                bid_competitiveness = self._calculate_bid_competitiveness(bid_amount, campaign_type)
            
            # Iterate through days
            current_date = datetime.now()
            for day in range(days):
                # Stop if total budget is exhausted
                if campaign_spend >= total_budget:
                    break
                    
                daily_date = current_date + timedelta(days=day)
                daily_impressions = 0
                daily_clicks = 0
                daily_conversions = 0
                daily_spend = 0.0
                
                # Day of week factor (weekends have less activity on LinkedIn)
                day_of_week = daily_date.weekday()  # 0-6 (Mon-Sun)
                day_factor = 1.0 if day_of_week < 5 else 0.4
                
                # Calculate daily base impressions based on targeting
                base_impressions = int(1000 * targeting_score * bid_competitiveness * day_factor)
                
                # Add some random variation
                daily_variation = random.uniform(0.8, 1.2)
                potential_impressions = int(base_impressions * daily_variation)
                
                # Process each creative
                for creative in active_creatives:
                    # Skip if daily budget is exhausted
                    if daily_spend >= daily_budget:
                        break
                        
                    # Calculate creative quality score (0-1)
                    creative_quality = random.uniform(0.5, 1.0)
                    
                    # Calculate share of impressions for this creative
                    creative_impressions = int(potential_impressions / len(active_creatives) * creative_quality)
                    
                    # Calculate CTR based on format, targeting, and creative quality
                    base_ctr = 0.004  # LinkedIn base CTR is lower than other platforms
                    format_multiplier = format_data["ctr_multiplier"]
                    ctr = base_ctr * format_multiplier * targeting_score * creative_quality
                    
                    # Add some random variation to CTR
                    ctr_variation = random.uniform(0.8, 1.2)
                    actual_ctr = ctr * ctr_variation
                    
                    # Calculate clicks
                    creative_clicks = int(creative_impressions * actual_ctr)
                    
                    # Calculate CPM and spend
                    base_cpm = format_data["cpm_base"]
                    targeting_premium = 1.0 + (targeting_score * 0.5)  # More targeted = more expensive
                    actual_cpm = base_cpm * targeting_premium * random.uniform(0.9, 1.1)
                    
                    # Calculate creative spend
                    creative_spend = (creative_impressions / 1000) * actual_cpm
                    
                    # Apply budget constraints
                    remaining_budget = min(daily_budget - daily_spend, total_budget - campaign_spend)
                    if creative_spend > remaining_budget:
                        ratio = remaining_budget / creative_spend
                        creative_impressions = int(creative_impressions * ratio)
                        creative_clicks = int(creative_clicks * ratio)
                        creative_spend = remaining_budget
                    
                    # Calculate conversions based on objective
                    conversion_rate_multipliers = {
                        "LEAD_GENERATION": 0.08,
                        "WEBSITE_CONVERSIONS": 0.05,
                        "WEBSITE_VISITS": 0.03,
                        "BRAND_AWARENESS": 0.01,
                        "VIDEO_VIEWS": 0.02,
                        "ENGAGEMENT": 0.04,
                        "JOB_APPLICANTS": 0.06
                    }
                    multiplier = conversion_rate_multipliers.get(campaign_objective, 0.03)
                    
                    conversion_rate = multiplier * targeting_score * creative_quality
                    creative_conversions = int(creative_clicks * conversion_rate)
                    
                    # Simulate lead form submissions if this is a lead gen campaign
                    if campaign_objective == "LEAD_GENERATION" and creative_conversions > 0:
                        # Create some sample leads (for webhook simulation)
                        for _ in range(min(creative_conversions, 5)):  # Limit to 5 sample leads max per day
                            if random.random() > 0.7:  # 30% chance to generate a webhook event
                                form_id = f"form-{campaign_id}-{uuid.uuid4().hex[:8]}"
                                member_data = {
                                    "firstName": random.choice(["John", "Jane", "Michael", "Emma", "David"]),
                                    "lastName": random.choice(["Smith", "Johnson", "Williams", "Brown", "Jones"]),
                                    "email": f"lead_{uuid.uuid4().hex[:8]}@example.com",
                                    "company": random.choice(["Acme Inc", "Globex Corp", "Initech", "Wayne Enterprises"]),
                                    "jobTitle": random.choice(["Manager", "Director", "VP", "CEO", "Specialist"])
                                }
                                self.simulate_lead_form_submission(campaign_id, form_id, member_data)
                    
                    # Simulate message opens if this is a message ad
                    if campaign_type in ["message_ads", "conversation_ads"] and creative_clicks > 0:
                        for _ in range(min(creative_clicks, 3)):  # Limit to 3 sample opens max per day
                            if random.random() > 0.6:  # 40% chance to generate a webhook event
                                message_id = f"msg-{campaign_id}-{uuid.uuid4().hex[:8]}"
                                member_id = f"member-{uuid.uuid4().hex[:8]}"
                                self.simulate_message_open(message_id, member_id)
                    
                    # Accumulate daily metrics
                    daily_impressions += creative_impressions
                    daily_clicks += creative_clicks
                    daily_conversions += creative_conversions
                    daily_spend += creative_spend
                
                # Accumulate campaign metrics
                campaign_impressions += daily_impressions
                campaign_clicks += daily_clicks
                campaign_conversions += daily_conversions
                campaign_spend += daily_spend
                
                # Stop if daily budget is fully consumed for multiple days
                # (LinkedIn often stops campaigns that consistently max out budget)
                if daily_spend >= daily_budget * 0.99 and random.random() > 0.7:
                    break
            
            # Store campaign results
            self.results["campaigns"][campaign_id] = {
                "impressions": campaign_impressions,
                "clicks": campaign_clicks,
                "conversions": campaign_conversions,
                "spend": campaign_spend,
                "ctr": campaign_clicks / campaign_impressions if campaign_impressions > 0 else 0,
                "cpa": campaign_spend / campaign_conversions if campaign_conversions > 0 else 0,
            }
            
            # Accumulate total metrics
            total_impressions += campaign_impressions
            total_clicks += campaign_clicks
            total_conversions += campaign_conversions
            total_spend += campaign_spend
        
        # Update total metrics
        self.results["total_metrics"]["impressions"] = total_impressions
        self.results["total_metrics"]["clicks"] = total_clicks
        self.results["total_metrics"]["conversions"] = total_conversions
        self.results["total_metrics"]["spend"] = total_spend
