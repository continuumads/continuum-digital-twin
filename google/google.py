import random
from datetime import datetime, timedelta
import sys
import os
import time
import json

# Add parent directory to path to import base_simulator
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_simulator import BaseAdSimulator

class GoogleAdsSimulator(BaseAdSimulator):
    """Digital twin simulator for Google Ads platform."""
    
    def __init__(self, config=None):
        super().__init__("GoogleAds", config)
        self.ad_formats = {
            "search": {"ctr_multiplier": 1.0, "cpc_base": 0.5},
            "display": {"ctr_multiplier": 0.3, "cpc_base": 0.2},
            "video": {"ctr_multiplier": 0.5, "cpc_base": 0.7},
            "shopping": {"ctr_multiplier": 1.2, "cpc_base": 0.6}
        }
        self.keyword_quality_scores = {}
        # Google Ads API specific attributes
        self.api_access = {
            "developer_token": None,
            "oauth_credentials": None,
            "access_level": "test",  # Options: test, basic, standard
            "daily_quota": 15000,    # Default for test/basic access
            "operations_used": 0,
            "last_quota_reset": datetime.now().date()
        }
        self.recommendation_types = [
            "KEYWORD", "BUDGET", "TEXT_AD", "TARGET_CPA_OPT_IN",
            "MAXIMIZE_CONVERSIONS_OPT_IN", "MAXIMIZE_CONVERSION_VALUE_OPT_IN",
            "IMPROVE_GOOGLE_TAG_COVERAGE", "PERFORMANCE_MAX_FINAL_URL_OPT_IN"
        ]
        # Track API calls for rate limiting simulation
        self.api_calls = []
        self.resources_metadata = self._initialize_resources_metadata()
        
    def _initialize_resources_metadata(self):
        """Initialize metadata about available resources in the API simulation."""
        return {
            "campaign": {
                "fields": ["id", "name", "status", "budget", "bidding_strategy", "targeting"],
                "metrics": ["impressions", "clicks", "conversions", "cost", "ctr", "cpa", "roas"]
            },
            "ad_group": {
                "fields": ["id", "name", "status", "campaign_id", "cpc_bid", "targeting"],
                "metrics": ["impressions", "clicks", "conversions", "cost", "ctr", "cpa"]
            },
            "ad": {
                "fields": ["id", "ad_group_id", "headline", "description", "status", "approval_status"],
                "metrics": ["impressions", "clicks", "conversions", "cost", "ctr", "cpa"]
            },
            "keyword": {
                "fields": ["id", "ad_group_id", "text", "match_type", "bid", "quality_score", "status"],
                "metrics": ["impressions", "clicks", "conversions", "cost", "ctr", "cpa", "position"]
            }
        }
        
    def set_api_credentials(self, developer_token, oauth_credentials, access_level="test"):
        """Simulate setting API credentials for authentication."""
        self.api_access["developer_token"] = developer_token
        self.api_access["oauth_credentials"] = oauth_credentials
        self.api_access["access_level"] = access_level
        
        # Set daily quota based on access level
        if access_level == "standard":
            self.api_access["daily_quota"] = float('inf')  # Unlimited for standard access
        else:
            self.api_access["daily_quota"] = 15000  # Default for test/basic access
            
        return {"status": "success", "message": f"API credentials set with {access_level} access level"}
    
    def _check_api_quota(self):
        """Check if the API quota has been exceeded."""
        # Reset daily quota if it's a new day
        today = datetime.now().date()
        if today > self.api_access["last_quota_reset"]:
            self.api_access["operations_used"] = 0
            self.api_access["last_quota_reset"] = today
            
        # Check if quota exceeded
        if self.api_access["operations_used"] >= self.api_access["daily_quota"]:
            return False
        return True
    
    def _track_api_call(self, endpoint, operations=1):
        """Track API calls and enforce rate limits."""
        if not self._check_api_quota():
            raise Exception("Google Ads API daily quota exceeded")
            
        # Record the API call
        call_time = datetime.now()
        self.api_calls.append({
            "endpoint": endpoint,
            "timestamp": call_time,
            "operations": operations
        })
        
        # Update operations used
        self.api_access["operations_used"] += operations
        
        # Simulate API rate limiting (max 20 queries per second)
        recent_calls = [call for call in self.api_calls 
                        if (call_time - call["timestamp"]).total_seconds() < 1]
        
        if len(recent_calls) > 20:
            time.sleep(0.1)  # Simulate backing off
            
        return True
        
    def create_ad_group(self, campaign_id, ad_group_data):
        """Create an ad group within a campaign."""
        self._track_api_call("AdGroupService.mutate")
        
        for campaign in self.campaigns:
            if campaign["id"] == campaign_id:
                if "ad_groups" not in campaign:
                    campaign["ad_groups"] = []
                
                ad_group_id = f"{campaign_id}-ag-{len(campaign['ad_groups']) + 1}"
                ad_group = {
                    "id": ad_group_id,
                    "data": ad_group_data,
                    "ads": [],
                    "keywords": [],
                    "status": "active",
                    "primary_status": "ELIGIBLE",
                    "primary_status_reasons": []
                }
                campaign["ad_groups"].append(ad_group)
                return ad_group_id
        
        raise ValueError(f"Campaign {campaign_id} not found")
    
    def add_keyword(self, ad_group_id, keyword, match_type="exact", bid=1.0):
        """Add a keyword to an ad group with a quality score."""
        self._track_api_call("KeywordService.mutate")
        
        for campaign in self.campaigns:
            if "ad_groups" not in campaign:
                continue
                
            for ad_group in campaign["ad_groups"]:
                if ad_group["id"] == ad_group_id:
                    keyword_id = f"{ad_group_id}-kw-{len(ad_group['keywords']) + 1}"
                    
                    # Generate a quality score (1-10)
                    quality_score = random.randint(1, 10)
                    self.keyword_quality_scores[keyword_id] = quality_score
                    
                    keyword_obj = {
                        "id": keyword_id,
                        "text": keyword,
                        "match_type": match_type,
                        "bid": bid,
                        "quality_score": quality_score,
                        "status": "active",
                        "first_page_bid": round(random.uniform(0.5, 3.0), 2)
                    }
                    ad_group["keywords"].append(keyword_obj)
                    return keyword_id
        
        raise ValueError(f"Ad group {ad_group_id} not found")
    
    def create_ad(self, ad_group_id, ad_data):
        """Create an ad within an ad group."""
        self._track_api_call("AdService.mutate")
        
        for campaign in self.campaigns:
            if "ad_groups" not in campaign:
                continue
                
            for ad_group in campaign["ad_groups"]:
                if ad_group["id"] == ad_group_id:
                    ad_id = f"{ad_group_id}-ad-{len(ad_group['ads']) + 1}"
                    ad = {
                        "id": ad_id,
                        "data": ad_data,
                        "status": "active",
                        "approval_status": "approved" if random.random() > 0.1 else "under_review",
                        "primary_status": "ELIGIBLE",
                        "primary_status_reasons": []
                    }
                    ad_group["ads"].append(ad)
                    return ad_id
        
        raise ValueError(f"Ad group {ad_group_id} not found")
    
    def generate_recommendations(self, customer_id, recommendation_types=None):
        """Simulate Google Ads API's RecommendationService.GenerateRecommendations method."""
        self._track_api_call("RecommendationService.GenerateRecommendations")
        
        if recommendation_types is None:
            recommendation_types = random.sample(self.recommendation_types, 3)
            
        recommendations = []
        
        for rec_type in recommendation_types:
            # Generate 1-3 recommendations of each requested type
            count = random.randint(1, 3)
            for _ in range(count):
                if rec_type == "KEYWORD":
                    recommendations.append({
                        "type": rec_type,
                        "keyword": {
                            "text": random.choice(["digital marketing", "online ads", "google advertising"]),
                            "match_type": random.choice(["BROAD", "PHRASE", "EXACT"]),
                            "recommended_cpc_bid": round(random.uniform(0.5, 2.0), 2)
                        }
                    })
                elif rec_type == "BUDGET":
                    recommendations.append({
                        "type": rec_type,
                        "budget": {
                            "current_budget": round(random.uniform(10, 100), 2),
                            "recommended_budget": round(random.uniform(50, 200), 2),
                            "estimated_additional_conversions": random.randint(1, 10)
                        }
                    })
                else:
                    recommendations.append({
                        "type": rec_type,
                        "impact": {
                            "base_metrics": {"clicks": random.randint(100, 500), "conversions": random.randint(5, 20)},
                            "potential_metrics": {"clicks": random.randint(150, 600), "conversions": random.randint(10, 30)}
                        }
                    })
                    
        return recommendations
    
    def get_change_history(self, customer_id, start_date, end_date):
        """Simulate retrieving change history for an account."""
        self._track_api_call("GoogleAdsService.Search(change_event)")
        
        # Generate random changes
        change_types = ["CAMPAIGN", "AD_GROUP", "AD", "KEYWORD", "BID", "BUDGET"]
        change_statuses = ["ADDED", "REMOVED", "CHANGED"]
        
        changes = []
        num_changes = random.randint(5, 20)
        
        for _ in range(num_changes):
            change_date = start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
            changes.append({
                "change_date": change_date.strftime("%Y-%m-%d"),
                "change_type": random.choice(change_types),
                "change_status": random.choice(change_statuses),
                "changed_by": "API" if random.random() > 0.5 else "USER",
                "resource_name": f"customers/{customer_id}/campaigns/{random.randint(1000, 9999)}"
            })
            
        return changes
    
    def search(self, query, customer_id=None):
        """Simulate Google Ads API's GoogleAdsService.Search method using GAQL."""
        self._track_api_call("GoogleAdsService.Search")
        
        # Basic GAQL parser simulation
        resource_type = None
        fields = []
        
        if "SELECT" in query and "FROM" in query:
            select_part = query.split("FROM")[0].replace("SELECT", "").strip()
            from_part = query.split("FROM")[1].split("WHERE")[0].strip() if "WHERE" in query else query.split("FROM")[1].strip()
            
            fields = [field.strip() for field in select_part.split(",")]
            resource_type = from_part
        
        results = []
        
        # Generate mock data based on resource type
        if resource_type == "campaign":
            for campaign in self.campaigns:
                result = {"campaign.id": campaign["id"], "campaign.name": campaign["data"]["name"]}
                for field in fields:
                    if field.startswith("metrics"):
                        metric_name = field.split(".")[1]
                        result[field] = self.results["campaigns"].get(campaign["id"], {}).get(metric_name, 0)
                results.append(result)
                
        elif resource_type == "ad_group":
            for campaign in self.campaigns:
                if "ad_groups" in campaign:
                    for ad_group in campaign["ad_groups"]:
                        result = {
                            "ad_group.id": ad_group["id"], 
                            "ad_group.name": ad_group["data"]["name"],
                            "campaign.id": campaign["id"]
                        }
                        results.append(result)
                        
        elif resource_type == "keyword":
            for campaign in self.campaigns:
                if "ad_groups" in campaign:
                    for ad_group in campaign["ad_groups"]:
                        if "keywords" in ad_group:
                            for keyword in ad_group["keywords"]:
                                result = {
                                    "keyword.id": keyword["id"],
                                    "keyword.text": keyword["text"],
                                    "keyword.match_type": keyword["match_type"],
                                    "ad_group.id": ad_group["id"]
                                }
                                results.append(result)
                                
        return results
    
    def _calculate_ad_rank(self, keyword, bid, quality_score):
        """Calculate the ad rank using Google's formula."""
        return bid * quality_score
    
    def _calculate_actual_cpc(self, competitor_ad_rank, quality_score, bid):
        """Calculate the actual CPC using Google's formula."""
        if quality_score == 0:
            return bid
        return (competitor_ad_rank / quality_score) + 0.01
    
    def _run_platform_simulation(self, days, speed_factor):
        """Run Google Ads-specific simulation."""
        total_impressions = 0
        total_clicks = 0
        total_conversions = 0
        total_spend = 0.0
        
        for campaign in self.campaigns:
            campaign_id = campaign["id"]
            campaign_budget = campaign["data"].get("daily_budget", 100.0) * days
            campaign_spend = 0.0
            campaign_impressions = 0
            campaign_clicks = 0
            campaign_conversions = 0
            
            # Skip inactive campaigns
            if campaign["status"] != "active":
                continue
            
            # Iterate through days
            current_date = datetime.now()
            for day in range(days):
                daily_date = current_date + timedelta(days=day)
                daily_impressions = 0
                daily_clicks = 0
                daily_conversions = 0
                daily_spend = 0.0
                
                # Process each ad group
                if "ad_groups" in campaign:
                    for ad_group in campaign["ad_groups"]:
                        # Skip inactive ad groups
                        if ad_group["status"] != "active":
                            continue
                            
                        ad_format = ad_group["data"].get("ad_format", "search")
                        format_data = self.ad_formats.get(ad_format, self.ad_formats["search"])
                        
                        # Process keywords and generate traffic
                        for keyword in ad_group["keywords"]:
                            # Base metrics
                            kw_quality = keyword["quality_score"]
                            kw_bid = keyword["bid"]
                            
                            # Calculate impressions based on quality score and match type
                            match_type_multiplier = {
                                "exact": 1.0,
                                "phrase": 2.0,
                                "broad": 4.0
                            }.get(keyword["match_type"], 1.0)
                            
                            # Daily impressions for this keyword
                            kw_impressions = int(kw_quality * match_type_multiplier * random.uniform(10, 50))
                            
                            # Calculate CTR based on quality score
                            base_ctr = 0.05 * (kw_quality / 10)
                            actual_ctr = base_ctr * format_data["ctr_multiplier"]
                            
                            # Calculate clicks
                            kw_clicks = int(kw_impressions * actual_ctr)
                            
                            # Calculate CPC
                            base_cpc = format_data["cpc_base"]
                            competitor_ad_rank = random.uniform(1, 10) * random.uniform(0.5, 2.0)
                            actual_cpc = self._calculate_actual_cpc(competitor_ad_rank, kw_quality, kw_bid)
                            
                            # Calculate spend
                            kw_spend = kw_clicks * actual_cpc
                            
                            # Calculate conversions
                            conv_rate = 0.02 * (kw_quality / 10)
                            kw_conversions = int(kw_clicks * conv_rate)
                            
                            # Apply daily budget limits
                            if daily_spend + kw_spend > campaign["data"].get("daily_budget", 100.0):
                                spend_ratio = (campaign["data"].get("daily_budget", 100.0) - daily_spend) / kw_spend
                                kw_clicks = int(kw_clicks * spend_ratio)
                                kw_conversions = int(kw_conversions * spend_ratio)
                                kw_spend = campaign["data"].get("daily_budget", 100.0) - daily_spend
                            
                            # Accumulate daily stats
                            daily_impressions += kw_impressions
                            daily_clicks += kw_clicks
                            daily_conversions += kw_conversions
                            daily_spend += kw_spend
                            
                            # Stop if we've exceeded the daily budget
                            if daily_spend >= campaign["data"].get("daily_budget", 100.0):
                                break
                
                # Accumulate campaign stats
                campaign_impressions += daily_impressions
                campaign_clicks += daily_clicks
                campaign_conversions += daily_conversions
                campaign_spend += daily_spend
                
                # Stop if we've exceeded the campaign budget
                if campaign_spend >= campaign_budget:
                    break
            
            # Store campaign results
            self.results["campaigns"][campaign_id] = {
                "impressions": campaign_impressions,
                "clicks": campaign_clicks,
                "conversions": campaign_conversions,
                "spend": campaign_spend,
                "ctr": campaign_clicks / campaign_impressions if campaign_impressions > 0 else 0,
                "cpa": campaign_spend / campaign_conversions if campaign_conversions > 0 else 0,
                "roas": (campaign_conversions * campaign["data"].get("conv_value", 10)) / campaign_spend if campaign_spend > 0 else 0
            }
            
            # Accumulate total stats
            total_impressions += campaign_impressions
            total_clicks += campaign_clicks
            total_conversions += campaign_conversions
            total_spend += campaign_spend
        
        # Update total metrics
        self.results["total_metrics"]["impressions"] = total_impressions
        self.results["total_metrics"]["clicks"] = total_clicks
        self.results["total_metrics"]["conversions"] = total_conversions
        self.results["total_metrics"]["spend"] = total_spend
        self.results["total_metrics"]["ctr"] = total_clicks / total_impressions if total_impressions > 0 else 0
        self.results["total_metrics"]["cpa"] = total_spend / total_conversions if total_conversions > 0 else 0
