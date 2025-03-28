from google import GoogleAdsSimulator
from facebook import FacebookAdsSimulator
from linkedin import LinkedInAdsSimulator
import json
import os

class AdSimulator:
    """
    Main utility class to manage digital twin simulations across multiple ad platforms.
    """
    
    def __init__(self, config_file=None):
        """
        Initialize the AdSimulator with optional configuration.
        
        Args:
            config_file (str, optional): Path to a JSON config file.
        """
        self.config = {}
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r') as f:
                self.config = json.load(f)
        
        # Initialize platform simulators
        self.google_simulator = GoogleAdsSimulator(self.config.get('google', {}))
        self.facebook_simulator = FacebookAdsSimulator(self.config.get('facebook', {}))
        self.linkedin_simulator = LinkedInAdsSimulator(self.config.get('linkedin', {}))
        
        # Store simulation results
        self.results = {
            'google': {},
            'facebook': {},
            'linkedin': {},
            'combined': {}
        }
    
    def configure_platforms(self, platform_configs):
        """
        Configure specific platforms with provided settings.
        
        Args:
            platform_configs (dict): Configuration settings for each platform.
        """
        if 'google' in platform_configs:
            self.google_simulator.config.update(platform_configs['google'])
        
        if 'facebook' in platform_configs:
            self.facebook_simulator.config.update(platform_configs['facebook'])
        
        if 'linkedin' in platform_configs:
            self.linkedin_simulator.config.update(platform_configs['linkedin'])
    
    def create_cross_platform_campaign(self, campaign_data, platforms=None):
        """
        Create a campaign across multiple platforms with platform-specific adjustments.
        
        Args:
            campaign_data (dict): Base campaign configuration
            platforms (list, optional): List of platforms to create the campaign on
                                       (default: all platforms)
        
        Returns:
            dict: Campaign IDs for each platform
        """
        if platforms is None:
            platforms = ['google', 'facebook', 'linkedin']
        
        campaign_ids = {}
        
        if 'google' in platforms:
            # Adjust campaign data for Google Ads specifics
            google_campaign = campaign_data.copy()
            if 'objective' in google_campaign:
                # Map generic objective to Google-specific one
                objective_mapping = {
                    'conversions': 'CONVERSION',
                    'traffic': 'SEARCH',
                    'awareness': 'DISPLAY',
                    'video_views': 'VIDEO'
                }
                google_campaign['objective'] = objective_mapping.get(
                    google_campaign['objective'].lower(), 
                    'CONVERSION'
                )
            
            # Create campaign on Google Ads
            google_id = self.google_simulator.create_campaign(google_campaign)
            campaign_ids['google'] = google_id
        
        if 'facebook' in platforms:
            # Adjust campaign data for Facebook Ads specifics
            fb_campaign = campaign_data.copy()
            if 'objective' in fb_campaign:
                # Map generic objective to Facebook-specific one
                objective_mapping = {
                    'conversions': 'CONVERSIONS',
                    'traffic': 'TRAFFIC',
                    'awareness': 'BRAND_AWARENESS',
                    'video_views': 'VIDEO_VIEWS'
                }
                fb_campaign['objective'] = objective_mapping.get(
                    fb_campaign['objective'].lower(), 
                    'CONVERSIONS'
                )
            
            # Create campaign on Facebook Ads
            fb_id = self.facebook_simulator.create_campaign(fb_campaign)
            campaign_ids['facebook'] = fb_id
        
        if 'linkedin' in platforms:
            # Adjust campaign data for LinkedIn Ads specifics
            li_campaign = campaign_data.copy()
            if 'objective' in li_campaign:
                # Map generic objective to LinkedIn-specific one
                objective_mapping = {
                    'conversions': 'WEBSITE_CONVERSIONS',
                    'traffic': 'WEBSITE_VISITS',
                    'awareness': 'BRAND_AWARENESS',
                    'video_views': 'VIDEO_VIEWS',
                    'leads': 'LEAD_GENERATION'
                }
                li_campaign['objective'] = objective_mapping.get(
                    li_campaign['objective'].lower(), 
                    'WEBSITE_CONVERSIONS'
                )
            
            # Create campaign on LinkedIn Ads
            li_id = self.linkedin_simulator.create_campaign(li_campaign)
            campaign_ids['linkedin'] = li_id
        
        return campaign_ids
    
    def run_campaigns(self, days=30, platforms=None):
        """
        Run campaign simulations across platforms.
        
        Args:
            days (int): Number of days to simulate
            platforms (list, optional): List of platforms to simulate
                                      (default: all platforms)
        
        Returns:
            dict: Combined simulation results
        """
        if platforms is None:
            platforms = ['google', 'facebook', 'linkedin']
        
        if 'google' in platforms:
            self.results['google'] = self.google_simulator.run_simulation(days)
        
        if 'facebook' in platforms:
            self.results['facebook'] = self.facebook_simulator.run_simulation(days)
        
        if 'linkedin' in platforms:
            self.results['linkedin'] = self.linkedin_simulator.run_simulation(days)
        
        # Combine results
        self._combine_results()
        
        return self.results
    
    def _combine_results(self):
        """Combine results from all platforms into a unified view."""
        combined = {
            'total_metrics': {
                'impressions': 0,
                'clicks': 0,
                'conversions': 0,
                'spend': 0.0,
                'ctr': 0.0,
                'cpa': 0.0
            },
            'platform_comparison': {},
            'campaigns': {}
        }
        
        # Aggregate total metrics
        for platform, result in self.results.items():
            if platform == 'combined' or not result:
                continue
                
            if 'total_metrics' in result:
                metrics = result['total_metrics']
                combined['total_metrics']['impressions'] += metrics.get('impressions', 0)
                combined['total_metrics']['clicks'] += metrics.get('clicks', 0)
                combined['total_metrics']['conversions'] += metrics.get('conversions', 0)
                combined['total_metrics']['spend'] += metrics.get('spend', 0.0)
                
                # Store platform-specific totals for comparison
                combined['platform_comparison'][platform] = metrics
        
        # Calculate overall CTR and CPA
        total_impressions = combined['total_metrics']['impressions']
        total_clicks = combined['total_metrics']['clicks']
        total_conversions = combined['total_metrics']['conversions']
        total_spend = combined['total_metrics']['spend']
        
        if total_impressions > 0:
            combined['total_metrics']['ctr'] = total_clicks / total_impressions
        
        if total_conversions > 0:
            combined['total_metrics']['cpa'] = total_spend / total_conversions
        
        self.results['combined'] = combined
    
    def export_results(self, output_dir='results'):
        """
        Export simulation results to JSON files.
        
        Args:
            output_dir (str): Directory to save result files
        """
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Export individual platform results
        for platform, result in self.results.items():
            if not result:
                continue
                
            filename = os.path.join(output_dir, f"{platform}_results.json")
            with open(filename, 'w') as f:
                json.dump(result, f, indent=2)
        
        print(f"Results exported to {output_dir}/")

# Usage example
if __name__ == "__main__":
    # Create simulator
    simulator = AdSimulator()
    
    # Create an audience
    audience_data = {
        "size": 500000,
        "ctr_base": 0.03,
        "conversion_rate": 0.015,
        "demographics_match": 0.8,
        "interests_match": 0.7
    }
    
    simulator.google_simulator.define_audience("tech_professionals", audience_data)
    simulator.facebook_simulator.define_audience("tech_professionals", audience_data)
    simulator.linkedin_simulator.define_audience("tech_professionals", audience_data)
    
    # Create a cross-platform campaign
    campaign_data = {
        "name": "Product Launch Campaign",
        "objective": "conversions",
        "daily_budget": 100.0,
        "total_budget": 3000.0,
        "targeting": {
            "audience": "tech_professionals"
        }
    }
    
    campaign_ids = simulator.create_cross_platform_campaign(campaign_data)
    print("Created campaigns:", campaign_ids)
    
    # Run simulations
    results = simulator.run_campaigns(days=30)
    
    # Export results
    simulator.export_results()
    
    # Print summary
    combined = results['combined']['total_metrics']
    print(f"\nSimulation Summary:")
    print(f"Total Impressions: {combined['impressions']:,}")
    print(f"Total Clicks: {combined['clicks']:,}")
    print(f"Total Conversions: {combined['conversions']:,}")
    print(f"Total Spend: ${combined['spend']:,.2f}")
    print(f"Overall CTR: {combined['ctr']*100:.2f}%")
    print(f"Overall CPA: ${combined['cpa']:.2f}")
