"""
Example script demonstrating the Continuum Digital Twin functionality.
"""

from ad_simulator import AdSimulator
from google import GoogleAdsSimulator
from facebook import FacebookAdsSimulator
from linkedin import LinkedInAdsSimulator
import requests
import json
import time

def run_simple_example():
    """Run a simple example of the digital twin simulation."""
    # Create a simulator instance
    simulator = AdSimulator()
    
    # Define common audience data
    audience_data = {
        "size": 10000000,
        "ctr_base": 0.025,
        "conversion_rate": 0.02,
        "demographics_match": 0.7,
        "interests_match": 0.6,
        "behaviors_match": 0.5
    }
    
    # Define audience for each platform
    simulator.google_simulator.define_audience("software_developers", audience_data)
    simulator.facebook_simulator.define_audience("software_developers", audience_data)
    simulator.linkedin_simulator.define_audience("software_developers", audience_data)
    
    # Create a campaign for each platform
    print("Creating campaigns...")
    
    # Google campaign
    google_campaign = {
        "name": "Google Dev Tools Promotion",
        "objective": "CONVERSION",
        "daily_budget": 1500.0,
        "targeting": {
            "audience": "software_developers"
        }
    }
    google_id = simulator.google_simulator.create_campaign(google_campaign)
    
    # Create ad groups for Google
    ad_group_id = simulator.google_simulator.create_ad_group(google_id, {
        "name": "Developer Tools",
        "ad_format": "search"
    })
    
    # Add keywords
    simulator.google_simulator.add_keyword(ad_group_id, "developer tools", "exact", 2.5)
    simulator.google_simulator.add_keyword(ad_group_id, "coding software", "phrase", 1.8)
    simulator.google_simulator.add_keyword(ad_group_id, "programming tools", "broad", 1.2)
    
    # Create ads
    simulator.google_simulator.create_ad(ad_group_id, {
        "headline1": "Professional Dev Tools",
        "headline2": "Increase Coding Efficiency",
        "description": "High-quality tools for professional developers. Try it today!"
    })
    
    # Facebook campaign
    facebook_campaign = {
        "name": "Facebook Dev Community Campaign",
        "objective": "CONVERSIONS",
        "budget": 2000.0,
        "targeting": {
            "audience": "software_developers"
        }
    }
    facebook_id = simulator.facebook_simulator.create_campaign(facebook_campaign)
    
    # Create ad sets for Facebook
    ad_set_id = simulator.facebook_simulator.create_ad_set(facebook_id, {
        "name": "Developer Community",
        "budget": 1000.0,
        "placements": ["feed", "instagram"],
        "targeting": {
            "age_range": {"min": 25, "max": 45},
            "gender": "all",
            "interests": ["programming", "software development", "coding"]
        }
    })
    
    # Create ads
    simulator.facebook_simulator.create_ad(ad_set_id, {
        "title": "Join Our Developer Community",
        "body": "Connect with other developers, share knowledge and grow your career.",
        "image_url": "https://example.com/dev_community.jpg",
        "call_to_action": "SIGN_UP"
    })
    
    # LinkedIn campaign
    linkedin_campaign = {
        "name": "LinkedIn Professional Tools Campaign",
        "objective": "LEAD_GENERATION",
        "type": "sponsored_content",
        "daily_budget": 200.0,
        "total_budget": 6000.0,
        "targeting": {
            "job_title": ["Software Engineer", "Developer", "Programmer"],
            "job_function": ["IT", "Engineering"],
            "seniority": ["Senior", "Manager", "Director"],
            "skills": ["Python", "Java", "JavaScript", "Cloud Computing"]
        }
    }
    linkedin_id = simulator.linkedin_simulator.create_campaign(linkedin_campaign)
    
    # Create LinkedIn creative
    simulator.linkedin_simulator.create_creative(linkedin_id, {
        "title": "Enterprise-Grade Development Tools",
        "body": "Boost your team's productivity with our professional development suite. Used by Fortune 500 companies.",
        "destination_url": "https://example.com/enterprise",
        "call_to_action": "LEARN_MORE"
    })
    
    # Run simulation for 30 days
    print("Running 30-day simulation...")
    results = simulator.run_campaigns(days=30)
    
    # Export results
    simulator.export_results()
    
    # Print summary
    print("\nSimulation Results Summary:")
    for platform, platform_results in simulator.results.items():
        if platform == 'combined':
            continue
            
        if 'total_metrics' in platform_results:
            metrics = platform_results['total_metrics']
            print(f"\n{platform.upper()} RESULTS:")
            print(f"  Impressions: {metrics.get('impressions', 0):,}")
            print(f"  Clicks: {metrics.get('clicks', 0):,}")
            print(f"  Conversions: {metrics.get('conversions', 0):,}")
            print(f"  Spend: ${metrics.get('spend', 0):,.2f}")
            
            # Calculate CTR and CPA
            impressions = metrics.get('impressions', 0)
            clicks = metrics.get('clicks', 0)
            conversions = metrics.get('conversions', 0)
            spend = metrics.get('spend', 0)
            
            ctr = clicks / impressions if impressions > 0 else 0
            cpa = spend / conversions if conversions > 0 else 0
            
            print(f"  CTR: {ctr*100:.2f}%")
            print(f"  CPA: ${cpa:.2f}")
    
    # Print combined results
    combined = results['combined']['total_metrics']
    print(f"\nOVERALL RESULTS:")
    print(f"  Total Impressions: {combined['impressions']:,}")
    print(f"  Total Clicks: {combined['clicks']:,}")
    print(f"  Total Conversions: {combined['conversions']:,}")
    print(f"  Total Spend: ${combined['spend']:,.2f}")
    print(f"  Overall CTR: {combined['ctr']*100:.2f}%")
    print(f"  Overall CPA: ${combined['cpa']:.2f}")

def run_comparative_analysis():
    """Run a comparative analysis across platforms."""
    print("\n=== Running Platform Comparison Test ===")
    
    # Create fresh simulator instance
    simulator = AdSimulator()
    
    # Define same audience for all platforms
    identical_audience = {
        "size": 500000,
        "ctr_base": 0.02,
        "conversion_rate": 0.01
    }
    
    for platform_sim in [
        simulator.google_simulator, 
        simulator.facebook_simulator, 
        simulator.linkedin_simulator
    ]:
        platform_sim.define_audience("identical_audience", identical_audience)
    
    # Create identical campaign on each platform
    identical_campaign = {
        "name": "Platform Comparison Test",
        "daily_budget": 100.0,
        "targeting": {
            "audience": "identical_audience"
        }
    }
    
    # Create campaign on each platform with slight platform-specific adjustments
    google_id = simulator.google_simulator.create_campaign({
        **identical_campaign,
        "objective": "CONVERSION"
    })
    
    facebook_id = simulator.facebook_simulator.create_campaign({
        **identical_campaign,
        "objective": "CONVERSIONS"
    })
    
    linkedin_id = simulator.linkedin_simulator.create_campaign({
        **identical_campaign,
        "objective": "WEBSITE_CONVERSIONS",
        "type": "sponsored_content"
    })
    
    # Simple ad creation for each platform
    # Google
    ad_group_id = simulator.google_simulator.create_ad_group(google_id, {
        "name": "Comparison Group",
        "ad_format": "search"
    })
    simulator.google_simulator.add_keyword(ad_group_id, "platform comparison", "exact", 1.5)
    simulator.google_simulator.create_ad(ad_group_id, {
        "headline1": "Platform Comparison",
        "headline2": "Test Our Service",
        "description": "Same ad across platforms for accurate comparison."
    })
    
    # Facebook
    ad_set_id = simulator.facebook_simulator.create_ad_set(facebook_id, {
        "name": "Comparison Set",
        "placements": ["feed"]
    })
    simulator.facebook_simulator.create_ad(ad_set_id, {
        "title": "Platform Comparison",
        "body": "Same ad across platforms for accurate comparison."
    })
    
    # LinkedIn
    simulator.linkedin_simulator.create_creative(linkedin_id, {
        "title": "Platform Comparison",
        "body": "Same ad across platforms for accurate comparison."
    })
    
    # Run the simulation
    print("Running platform comparison simulation...")
    simulator.run_campaigns(days=14)
    
    # Print comparison results
    print("\nPLATFORM COMPARISON RESULTS:")
    platform_metrics = {}
    
    for platform, results in simulator.results.items():
        if platform == 'combined':
            continue
            
        if 'total_metrics' in results:
            metrics = results['total_metrics']
            impressions = metrics.get('impressions', 0)
            clicks = metrics.get('clicks', 0)
            conversions = metrics.get('conversions', 0)
            spend = metrics.get('spend', 0)
            
            # Safely calculate CTR and CPA with zero-checks
            ctr = clicks / impressions if impressions > 0 else 0
            cpa = spend / conversions if conversions > 0 else 0
            
            platform_metrics[platform] = {
                'impressions': impressions,
                'clicks': clicks,
                'conversions': conversions,
                'spend': spend,
                'ctr': ctr,
                'cpa': cpa
            }
    
    # Print side-by-side comparison
    metrics_to_show = ['impressions', 'clicks', 'conversions', 'spend', 'ctr', 'cpa']
    platforms = list(platform_metrics.keys())
    
    # Header
    print(f"{'Metric':<15}", end="")
    for platform in platforms:
        print(f"{platform:<15}", end="")
    print()
    
    # Data rows
    for metric in metrics_to_show:
        print(f"{metric:<15}", end="")
        for platform in platforms:
            value = platform_metrics[platform][metric]
            
            # Format based on metric type
            if metric in ['impressions', 'clicks', 'conversions']:
                formatted_value = f"{value:,}"
            elif metric == 'spend':
                formatted_value = f"${value:.2f}"
            elif metric == 'ctr':
                formatted_value = f"{value*100:.2f}%"
            elif metric == 'cpa':
                # Handle infinite CPA when there are no conversions
                if value == 0:
                    formatted_value = "$0.00"
                else:
                    formatted_value = f"${value:.2f}"
            else:
                formatted_value = str(value)
                
            print(f"{formatted_value:<15}", end="")
        print()

def run_budget_optimization_test():
    """Test budget optimization across platforms."""
    print("\n=== Running Budget Optimization Test ===")
    
    # Create simulator instance
    simulator = AdSimulator()
    
    # Define audience
    audience_data = {
        "size": 800000,
        "ctr_base": 0.03,
        "conversion_rate": 0.015
    }
    
    for platform_sim in [
        simulator.google_simulator, 
        simulator.facebook_simulator, 
        simulator.linkedin_simulator
    ]:
        platform_sim.define_audience("budget_test_audience", audience_data)
    
    # Test different budget allocations
    budget_allocations = [
        # Even split
        {'google': 0.33, 'facebook': 0.33, 'linkedin': 0.34},
        # Google heavy
        {'google': 0.6, 'facebook': 0.2, 'linkedin': 0.2},
        # Facebook heavy
        {'google': 0.2, 'facebook': 0.6, 'linkedin': 0.2},
        # LinkedIn heavy
        {'google': 0.2, 'facebook': 0.2, 'linkedin': 0.6}
    ]
    
    total_budget = 3000.0
    best_allocation = None
    best_conversions = 0
    best_cpa = float('inf')
    
    for i, allocation in enumerate(budget_allocations):
        print(f"\nTesting Budget Allocation #{i+1}:")
        for platform, percentage in allocation.items():
            print(f"  {platform}: {percentage*100:.1f}% (${total_budget * percentage:.2f})")
        
        # Create fresh simulator for this allocation
        simulator = AdSimulator()
        
        # Define audience for all platforms
        for platform_sim in [
            simulator.google_simulator, 
            simulator.facebook_simulator, 
            simulator.linkedin_simulator
        ]:
            platform_sim.define_audience("budget_test_audience", audience_data)
        
        # Create campaigns with this allocation
        for platform, percentage in allocation.items():
            platform_budget = total_budget * percentage
            campaign_data = {
                "name": f"Budget Test - Allocation #{i+1}",
                "daily_budget": platform_budget / 30,  # 30-day campaign
                "total_budget": platform_budget,
                "targeting": {
                    "audience": "budget_test_audience"
                }
            }
            
            # Add platform-specific objective
            if platform == 'google':
                campaign_data["objective"] = "CONVERSION"
                campaign_id = simulator.google_simulator.create_campaign(campaign_data)
                
                # Create ad group and ads
                ad_group_id = simulator.google_simulator.create_ad_group(campaign_id, {
                    "name": "Budget Test Group",
                    "ad_format": "search"
                })
                simulator.google_simulator.add_keyword(ad_group_id, "budget optimization", "exact", 1.5)
                simulator.google_simulator.create_ad(ad_group_id, {
                    "headline1": "Budget Test",
                    "headline2": "Optimize Your Spend",
                    "description": "Finding the best budget allocation across platforms."
                })
                
            elif platform == 'facebook':
                campaign_data["objective"] = "CONVERSIONS"
                campaign_id = simulator.facebook_simulator.create_campaign(campaign_data)
                
                # Create ad set and ads
                ad_set_id = simulator.facebook_simulator.create_ad_set(campaign_id, {
                    "name": "Budget Test Set",
                    "placements": ["feed", "instagram"]
                })
                simulator.facebook_simulator.create_ad(ad_set_id, {
                    "title": "Budget Optimization",
                    "body": "Finding the best budget allocation across platforms."
                })
                
            elif platform == 'linkedin':
                campaign_data["objective"] = "WEBSITE_CONVERSIONS"
                campaign_data["type"] = "sponsored_content"
                campaign_id = simulator.linkedin_simulator.create_campaign(campaign_data)
                
                # Create creative
                simulator.linkedin_simulator.create_creative(campaign_id, {
                    "title": "Budget Optimization",
                    "body": "Finding the best budget allocation across platforms."
                })
        
        # Run simulation
        results = simulator.run_campaigns(days=30)
        combined = results['combined']['total_metrics']
        
        total_conversions = combined['conversions']
        total_spend = combined['spend']
        
        # Calculate CPA safely
        cpa = total_spend / total_conversions if total_conversions > 0 else float('inf')
        
        print(f"  Results - Conversions: {total_conversions}, CPA: ${cpa:.2f}")
        
        # Check if this is the best allocation
        if total_conversions > best_conversions or (total_conversions == best_conversions and cpa < best_cpa):
            best_allocation = allocation
            best_conversions = total_conversions
            best_cpa = cpa
    
    # Print best allocation
    print(f"\nBEST BUDGET ALLOCATION:")
    for platform, percentage in best_allocation.items():
        print(f"  {platform}: {percentage*100:.1f}% (${total_budget * percentage:.2f})")
    print(f"  Total Conversions: {best_conversions}")
    
    # Format CPA to handle infinite values
    if best_cpa == float('inf'):
        cpa_display = "$0.00"  # Alternative: "$∞" or "N/A"
    else:
        cpa_display = f"${best_cpa:.2f}"
    
    print(f"  CPA: {cpa_display}")

def run_targeting_optimization_test():
    """Test different targeting approaches across platforms."""
    print("\n=== Running Targeting Optimization Test ===")
    
    # Create base audience
    base_audience = {
        "size": 1000000,
        "ctr_base": 0.025,
        "conversion_rate": 0.015
    }
    
    # Create different targeting strategies to test
    targeting_strategies = [
        {
            "name": "Broad targeting",
            "demographics_match": 0.4,
            "interests_match": 0.3,
            "behaviors_match": 0.3
        },
        {
            "name": "Demographic focused",
            "demographics_match": 0.9,
            "interests_match": 0.4,
            "behaviors_match": 0.3
        },
        {
            "name": "Interest focused",
            "demographics_match": 0.5,
            "interests_match": 0.9,
            "behaviors_match": 0.4
        },
        {
            "name": "Behavior focused",
            "demographics_match": 0.5, 
            "interests_match": 0.4,
            "behaviors_match": 0.9
        },
        {
            "name": "Balanced targeting",
            "demographics_match": 0.7,
            "interests_match": 0.7,
            "behaviors_match": 0.7
        }
    ]
    
    # Test results storage
    strategy_results = []
    
    # Loop through each strategy and platform
    platforms = ["google", "facebook", "linkedin"]
    
    for strategy in targeting_strategies:
        print(f"\nTesting targeting strategy: {strategy['name']}")
        strategy_data = {**base_audience, **strategy}
        
        platform_results = {}
        
        for platform in platforms:
            # Create a fresh simulator for each test
            simulator = AdSimulator()
            
            # Define audience with this targeting strategy
            audience_name = f"target_audience_{platform}"
            if platform == "google":
                simulator.google_simulator.define_audience(audience_name, strategy_data)
            elif platform == "facebook":
                simulator.facebook_simulator.define_audience(audience_name, strategy_data)
            elif platform == "linkedin":
                simulator.linkedin_simulator.define_audience(audience_name, strategy_data)
            
            # Create campaign with consistent settings
            campaign_data = {
                "name": f"{platform.capitalize()} - {strategy['name']}",
                "daily_budget": 100.0,
                "targeting": {
                    "audience": audience_name
                }
            }
            
            # Create platform-specific campaign
            if platform == "google":
                campaign_data["objective"] = "CONVERSION"
                campaign_id = simulator.google_simulator.create_campaign(campaign_data)
                
                # Create ad group and ads
                ad_group_id = simulator.google_simulator.create_ad_group(campaign_id, {
                    "name": "Targeting Test Group",
                    "ad_format": "search"
                })
                simulator.google_simulator.add_keyword(ad_group_id, "targeting optimization", "exact", 1.5)
                simulator.google_simulator.create_ad(ad_group_id, {
                    "headline1": "Targeting Test",
                    "headline2": "Optimize Your Audience",
                    "description": "Testing different targeting approaches."
                })
                
            elif platform == "facebook":
                campaign_data["objective"] = "CONVERSIONS"
                campaign_id = simulator.facebook_simulator.create_campaign(campaign_data)
                
                # Create ad set and ads with relevant targeting
                targeting_data = {
                    "name": "Targeting Test Set",
                    "placements": ["feed", "instagram"],
                    "targeting": {
                        "age_range": {"min": 25, "max": 55},
                        "gender": "all",
                        "interests": ["digital marketing", "online advertising", "business"]
                    }
                }
                
                # Adjust targeting based on strategy
                if strategy["name"] == "Demographic focused":
                    targeting_data["targeting"]["age_range"] = {"min": 30, "max": 45}
                    targeting_data["targeting"]["gender"] = "male"
                elif strategy["name"] == "Interest focused":
                    targeting_data["targeting"]["interests"] = ["digital marketing", "online advertising", 
                                                            "technology", "business strategy", "entrepreneurship"]
                
                ad_set_id = simulator.facebook_simulator.create_ad_set(campaign_id, targeting_data)
                simulator.facebook_simulator.create_ad(ad_set_id, {
                    "title": "Targeting Optimization",
                    "body": "Finding the best audience targeting approach."
                })
                
            elif platform == "linkedin":
                campaign_data["objective"] = "WEBSITE_CONVERSIONS"
                campaign_data["type"] = "sponsored_content"
                campaign_id = simulator.linkedin_simulator.create_campaign(campaign_data)
                
                # Create creative
                simulator.linkedin_simulator.create_creative(campaign_id, {
                    "title": "Targeting Optimization",
                    "body": "Finding the best audience targeting approach."
                })
            
            # Run simulation
            results = simulator.run_campaigns(days=14)
            
            # Extract platform results
            if platform == "google":
                platform_metrics = simulator.google_simulator.results.get("total_metrics", {})
            elif platform == "facebook":
                platform_metrics = simulator.facebook_simulator.results.get("total_metrics", {})
            elif platform == "linkedin":
                platform_metrics = simulator.linkedin_simulator.results.get("total_metrics", {})
            
            # Calculate metrics safely
            impressions = platform_metrics.get("impressions", 0)
            clicks = platform_metrics.get("clicks", 0)
            conversions = platform_metrics.get("conversions", 0)
            spend = platform_metrics.get("spend", 0)
            
            ctr = clicks / impressions if impressions > 0 else 0
            cpa = spend / conversions if conversions > 0 else float('inf')
            
            # Store results for this platform and strategy
            platform_results[platform] = {
                "impressions": impressions,
                "clicks": clicks,
                "conversions": conversions,
                "spend": spend,
                "ctr": ctr,
                "cpa": cpa
            }
            
            print(f"  {platform.capitalize()}: CTR: {ctr*100:.2f}%, CPA: ${cpa if cpa != float('inf') else 0:.2f}")
        
        # Calculate overall performance for this strategy
        total_impressions = sum(r["impressions"] for r in platform_results.values())
        total_clicks = sum(r["clicks"] for r in platform_results.values()) 
        total_conversions = sum(r["conversions"] for r in platform_results.values())
        total_spend = sum(r["spend"] for r in platform_results.values())
        
        overall_ctr = total_clicks / total_impressions if total_impressions > 0 else 0
        overall_cpa = total_spend / total_conversions if total_conversions > 0 else float('inf')
        
        strategy_results.append({
            "strategy": strategy["name"],
            "platform_results": platform_results,
            "total_impressions": total_impressions,
            "total_clicks": total_clicks,
            "total_conversions": total_conversions,
            "total_spend": total_spend,
            "overall_ctr": overall_ctr,
            "overall_cpa": overall_cpa
        })
    
    # Find the best performing strategy based on CTR if no conversions
    if all(r["total_conversions"] == 0 for r in strategy_results):
        best_strategy = max(strategy_results, key=lambda x: x["overall_ctr"])
    else:
        best_strategy = min(strategy_results, key=lambda x: x["overall_cpa"] if x["total_conversions"] > 0 else float('inf'))
    
    # Print summary of all strategies
    print("\nTARGETING STRATEGY RESULTS:")
    print(f"{'Strategy':<20} {'CTR':<8} {'CPA':<10} {'Conv.':<8}")
    print("-" * 50)
    
    for result in strategy_results:
        cpa_display = "$     inf" if result['overall_cpa'] == float('inf') else f"${result['overall_cpa']:8.2f}"
        print(f"{result['strategy']:<20} {result['overall_ctr']*100:6.2f}% {cpa_display} {result['total_conversions']:<8}")
    
    # Print best strategy results in detail
    print(f"\nBEST TARGETING STRATEGY: {best_strategy['strategy']}")
    print(f"  Overall CTR: {best_strategy['overall_ctr']*100:.2f}%")
    
    # Format CPA
    if best_strategy['overall_cpa'] == float('inf'):
        cpa_display = "$inf"
    else:
        cpa_display = f"${best_strategy['overall_cpa']:.2f}"
    
    print(f"  Overall CPA: {cpa_display}")
    print(f"  Total Conversions: {best_strategy['total_conversions']}")
    
    # Print platform-specific results for best strategy
    print("\nPlatform breakdown for best strategy:")
    for platform, metrics in best_strategy["platform_results"].items():
        cpa_display = "$0.00" if metrics['cpa'] == float('inf') else f"${metrics['cpa']:.2f}"
        print(f"  {platform.capitalize()}: CTR: {metrics['ctr']*100:.2f}%, CPA: {cpa_display}, Conv.: {metrics['conversions']}")

def run_api_example():
    """Example of using the Digital Twin API."""
    print("\n=== Running API Example ===")
    
    # Base URL of the API
    base_url = "http://localhost:8000"
    
    # API credentials - this would normally be stored securely
    api_key = "sk-continuum-123456789"
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json"
    }
    
    # Step 1: Define audiences
    print("1. Defining audiences...")
    audience_data = {
        "tech_professionals": {
            "size": 5000000,
            "ctr_base": 0.03,
            "conversion_rate": 0.02,
            "demographics_match": 0.8,
            "interests_match": 0.7,
            "behaviors_match": 0.6
        }
    }
    
    response = requests.post(
        f"{base_url}/audiences",
        headers=headers,
        json=audience_data
    )
    
    if response.status_code != 201:
        print(f"Error creating audiences: {response.text}")
        return
    
    print(f"Audiences created: {response.json()}")
    
    # Step 2: Create a cross-platform campaign
    print("\n2. Creating cross-platform campaign...")
    campaign_data = {
        "name": "API Test Campaign",
        "objective": "conversion",
        "daily_budget": 100.0,
        "total_budget": 3000.0,
        "targeting": {
            "audience": "tech_professionals"
        }
    }
    
    response = requests.post(
        f"{base_url}/campaigns/crossplatform",
        headers=headers,
        json=campaign_data
    )
    
    if response.status_code != 201:
        print(f"Error creating campaign: {response.text}")
        return
    
    campaign_ids = response.json()["campaign_ids"]
    print(f"Campaigns created: {campaign_ids}")
    
    # Step 3: Add platform-specific components
    
    # Google ad groups and ads
    print("\n3. Creating Google ad group, keywords and ads...")
    google_id = campaign_ids.get("google")
    
    ad_group_data = {
        "name": "API Test Ad Group",
        "ad_format": "search"
    }
    
    response = requests.post(
        f"{base_url}/campaigns/google/{google_id}/adgroups",
        headers=headers,
        json=ad_group_data
    )
    
    if response.status_code != 201:
        print(f"Error creating ad group: {response.text}")
    else:
        ad_group_id = response.json()["ad_group_id"]
        print(f"Ad group created: {ad_group_id}")
        
        # Add keywords
        keyword_data = {
            "text": "digital twin marketing",
            "match_type": "exact",
            "bid": 2.0
        }
        
        response = requests.post(
            f"{base_url}/campaigns/google/adgroups/{ad_group_id}/keywords",
            headers=headers,
            json=keyword_data
        )
        
        if response.status_code != 201:
            print(f"Error creating keyword: {response.text}")
        else:
            print(f"Keyword created: {response.json()['keyword_id']}")
        
        # Add ad
        ad_data = {
            "headline1": "Digital Twin Marketing",
            "headline2": "Simulate Before You Spend",
            "description": "Test marketing campaigns before spending real money. Try our digital twin today!"
        }
        
        response = requests.post(
            f"{base_url}/campaigns/google/adgroups/{ad_group_id}/ads",
            headers=headers,
            json=ad_data
        )
        
        if response.status_code != 201:
            print(f"Error creating ad: {response.text}")
        else:
            print(f"Ad created: {response.json()['ad_id']}")
    
    # Facebook ad sets and ads
    print("\n4. Creating Facebook ad set and ad...")
    facebook_id = campaign_ids.get("facebook")
    
    ad_set_data = {
        "name": "API Test Ad Set",
        "budget": 1500.0,
        "placements": ["feed", "instagram"],
        "targeting": {
            "age_range": {"min": 25, "max": 45},
            "gender": "all",
            "interests": ["digital marketing", "technology", "business"]
        }
    }
    
    response = requests.post(
        f"{base_url}/campaigns/facebook/{facebook_id}/adsets",
        headers=headers,
        json=ad_set_data
    )
    
    if response.status_code != 201:
        print(f"Error creating ad set: {response.text}")
    else:
        ad_set_id = response.json()["ad_set_id"]
        print(f"Ad set created: {ad_set_id}")
        
        # Add ad
        ad_data = {
            "title": "Marketing Simulation Platform",
            "body": "Test your marketing campaigns before investing. Our digital twin technology simulates real-world outcomes.",
            "image_url": "https://example.com/images/simulation.jpg",
            "call_to_action": "LEARN_MORE"
        }
        
        response = requests.post(
            f"{base_url}/campaigns/facebook/adsets/{ad_set_id}/ads",
            headers=headers,
            json=ad_data
        )
        
        if response.status_code != 201:
            print(f"Error creating ad: {response.text}")
        else:
            print(f"Ad created: {response.json()['ad_id']}")
    
    # LinkedIn creative
    print("\n5. Creating LinkedIn creative...")
    linkedin_id = campaign_ids.get("linkedin")
    
    creative_data = {
        "title": "Enterprise Marketing Simulation",
        "body": "Our digital twin technology helps marketing teams test campaigns before spending budget. Used by Fortune 500 companies to optimize ad spend.",
        "destination_url": "https://example.com/enterprise",
        "call_to_action": "LEARN_MORE"
    }
    
    response = requests.post(
        f"{base_url}/campaigns/linkedin/{linkedin_id}/creatives",
        headers=headers,
        json=creative_data
    )
    
    if response.status_code != 201:
        print(f"Error creating creative: {response.text}")
    else:
        print(f"Creative created: {response.json()['creative_id']}")
    
    # Step 4: Run a simulation
    print("\n6. Running simulation...")
    simulation_data = {
        "days": 30,
        "platforms": ["all"],
        "export_results": True
    }
    
    response = requests.post(
        f"{base_url}/simulations",
        headers=headers,
        json=simulation_data
    )
    
    if response.status_code != 200:
        print(f"Error starting simulation: {response.text}")
        return
    
    simulation_response = response.json()
    simulation_id = simulation_response["simulation_id"]
    print(f"Simulation started: {simulation_id}")
    
    # Wait for simulation to complete
    print("Waiting for simulation to complete...")
    max_wait = 60  # seconds
    wait_time = 0
    status = "pending"
    
    while status in ["pending", "running"] and wait_time < max_wait:
        time.sleep(5)
        wait_time += 5
        
        response = requests.get(
            f"{base_url}/simulations/{simulation_id}/status",
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"Error checking simulation status: {response.text}")
            break
        
        status = response.json()["status"]
        print(f"Simulation status: {status}")
    
    if status == "completed":
        # Get simulation results
        print("\n7. Getting simulation results...")
        response = requests.get(
            f"{base_url}/simulations/{simulation_id}/results",
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"Error getting simulation results: {response.text}")
            return
        
        results = response.json()
        
        # Print summary
        print("\nSimulation Results Summary:")
        overall = results["overall"]
        print(f"Total Impressions: {overall['impressions']:,}")
        print(f"Total Clicks: {overall['clicks']:,}")
        print(f"Total Conversions: {overall['conversions']:,}")
        print(f"Total Spend: ${overall['spend']:.2f}")
        print(f"Overall CTR: {overall['ctr']*100:.2f}%")
        print(f"Overall CPA: ${overall['cpa']:.2f}")
        
        # Platform breakdown
        print("\nPlatform Breakdown:")
        for platform, metrics in results["platforms"].items():
            print(f"\n{platform.upper()} RESULTS:")
            print(f"  Impressions: {metrics['impressions']:,}")
            print(f"  Clicks: {metrics['clicks']:,}")
            print(f"  Conversions: {metrics['conversions']:,}")
            print(f"  Spend: ${metrics['spend']:.2f}")
            print(f"  CTR: {metrics['ctr']*100:.2f}%")
            print(f"  CPA: ${metrics['cpa']:.2f}")
    else:
        print(f"Simulation did not complete within the timeout period. Final status: {status}")

if __name__ == "__main__":
    print("=== Continuum Digital Twin Example ===")
    print("\nThis example demonstrates the capabilities of the Continuum Digital Twin for ad platforms.\n")
    
    # Improved menu with more options
    print("Available examples:")
    print("1. Simple campaign example")
    print("2. Platform comparison")
    print("3. Budget optimization")
    print("4. Targeting optimization (NEW)")
    print("5. API example (NEW)")
    print("6. Run all examples")
    print("7. Exit")
    
    while True:
        choice = input("\nEnter choice (1-7): ")
        
        if choice == '1':
            run_simple_example()
            break
        elif choice == '2':
            run_comparative_analysis()
            break
        elif choice == '3':
            run_budget_optimization_test()
            break
        elif choice == '4':
            run_targeting_optimization_test()
            break
        elif choice == '5':
            run_api_example()
            break
        elif choice == '6':
            run_simple_example()
            run_comparative_analysis()
            run_budget_optimization_test()
            run_targeting_optimization_test()
            run_api_example()
            break
        elif choice == '7':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 7.")
