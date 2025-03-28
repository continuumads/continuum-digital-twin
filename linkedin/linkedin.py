import random
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path to import base_simulator
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_simulator import BaseAdSimulator

class LinkedInAdsSimulator(BaseAdSimulator):
    """Digital twin simulator for LinkedIn Ads platform."""
    
    def __init__(self, config=None):
        super().__init__("LinkedInAds", config)
        self.ad_formats = {
            "sponsored_content": {"ctr_multiplier": 1.0, "cpm_base": 8.5},
            "sponsored_inmails": {"ctr_multiplier": 3.0, "cpm_base": 25.0},
            "text_ads": {"ctr_multiplier": 0.5, "cpm_base": 5.0},
            "dynamic_ads": {"ctr_multiplier": 0.8, "cpm_base": 7.0}
        }
        self.targeting_dimensions = [
            "job_title", "job_function", "industry", "company_size",
            "seniority", "skills", "education", "interests", "groups"
        ]
    
    def create_creative(self, campaign_id, creative_data):
        """Create a creative within a campaign."""
        for campaign in self.campaigns:
            if campaign["id"] == campaign_id:
                if "creatives" not in campaign:
                    campaign["creatives"] = []
                
                creative_id = f"{campaign_id}-cr-{len(campaign['creatives']) + 1}"
                creative = {
                    "id": creative_id,
                    "data": creative_data,
                    "status": "active",
                    "review_status": "approved" if random.random() > 0.1 else "pending_review"
                }
                campaign["creatives"].append(creative)
                return creative_id
        
        raise ValueError(f"Campaign {campaign_id} not found")
    
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
        format_data = self.ad_formats.get(format_type, self.ad_formats["sponsored_content"])
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
    
    def _run_platform_simulation(self, days, speed_factor):
        """Run LinkedIn Ads-specific simulation."""
        total_impressions = 0
        total_clicks = 0
        total_conversions = 0
        total_spend = 0.0
        
        for campaign in self.campaigns:
            campaign_id = campaign["id"]
            campaign_data = campaign["data"]
            campaign_type = campaign_data.get("type", "sponsored_content")
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
            format_data = self.ad_formats.get(campaign_type, self.ad_formats["sponsored_content"])
            
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
                        "VIDEO_VIEWS": 0.02
                    }
                    multiplier = conversion_rate_multipliers.get(campaign_objective, 0.03)
                    
                    conversion_rate = multiplier * targeting_score * creative_quality
                    creative_conversions = int(creative_clicks * conversion_rate)
                    
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
