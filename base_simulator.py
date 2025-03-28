import random
import json
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

class BaseAdSimulator(ABC):
    """Base class for all ad platform simulators."""
    
    def __init__(self, platform_name, config=None):
        self.platform_name = platform_name
        self.config = config or {}
        self.campaigns = []
        self.audiences = {}
        self.results = {}
        
    def load_config(self, config_path):
        """Load configuration from a JSON file."""
        try:
            with open(config_path, 'r') as file:
                self.config = json.load(file)
            print(f"Loaded configuration for {self.platform_name}")
            return True
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return False
    
    def create_campaign(self, campaign_data):
        """Create a new ad campaign with the provided data."""
        campaign_id = f"{self.platform_name}-{len(self.campaigns) + 1}"
        campaign = {
            "id": campaign_id,
            "data": campaign_data,
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "metrics": {
                "impressions": 0,
                "clicks": 0,
                "conversions": 0,
                "spend": 0.0
            }
        }
        self.campaigns.append(campaign)
        return campaign_id
    
    def define_audience(self, audience_name, audience_params):
        """Define a simulated audience with specific behaviors."""
        if audience_name in self.audiences:
            print(f"Warning: Overwriting existing audience '{audience_name}'")
        
        self.audiences[audience_name] = {
            "params": audience_params,
            "size": audience_params.get("size", 10000),
            "ctr_base": audience_params.get("ctr_base", 0.02),
            "conversion_rate": audience_params.get("conversion_rate", 0.01)
        }
        return audience_name
    
    def run_simulation(self, days=30, speed_factor=1.0):
        """Run the simulation for the specified number of days."""
        print(f"Running {self.platform_name} simulation for {days} days...")
        
        # Initialize results
        self.results = {
            "platform": self.platform_name,
            "simulation_period": f"{days} days",
            "start_date": datetime.now().isoformat(),
            "end_date": (datetime.now() + timedelta(days=days)).isoformat(),
            "campaigns": {},
            "total_metrics": {
                "impressions": 0,
                "clicks": 0,
                "conversions": 0,
                "spend": 0.0,
                "ctr": 0.0,
                "cpa": 0.0
            }
        }
        
        # Run platform-specific simulation
        self._run_platform_simulation(days, speed_factor)
        
        # Calculate aggregated metrics
        total_clicks = self.results["total_metrics"]["clicks"]
        total_impressions = self.results["total_metrics"]["impressions"]
        total_conversions = self.results["total_metrics"]["conversions"]
        total_spend = self.results["total_metrics"]["spend"]
        
        if total_impressions > 0:
            self.results["total_metrics"]["ctr"] = total_clicks / total_impressions
        
        if total_conversions > 0:
            self.results["total_metrics"]["cpa"] = total_spend / total_conversions
            
        return self.results
    
    @abstractmethod
    def _run_platform_simulation(self, days, speed_factor):
        """Platform-specific simulation implementation."""
        pass
    
    def export_results(self, output_path=None):
        """Export simulation results to a JSON file."""
        if not output_path:
            output_path = f"{self.platform_name.lower()}_simulation_results.json"
            
        try:
            with open(output_path, 'w') as file:
                json.dump(self.results, file, indent=2)
            print(f"Results exported to {output_path}")
            return True
        except Exception as e:
            print(f"Error exporting results: {e}")
            return False
