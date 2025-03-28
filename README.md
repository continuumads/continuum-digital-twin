# Continuum Digital Twin

A digital twin simulation platform for advertising campaigns across multiple platforms including Google Ads, Facebook Ads, and LinkedIn Ads.

## Overview

The Continuum Digital Twin allows marketers to simulate ad campaign performance across multiple platforms before spending real budget. By creating a digital twin of your advertising ecosystem, you can test different budget allocations, targeting strategies, and creative approaches to predict performance.

## Features

- Simulate campaigns across Google, Facebook, and LinkedIn
- Test different budget allocations to optimize spend
- Evaluate targeting strategies to find the best audience approach
- Compare platform performance for your specific offerings
- API access for integration with other marketing tools

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Python Library

```python
from ad_simulator import AdSimulator

# Create a simulator
simulator = AdSimulator()

# Define audience
audience_data = {
    "size": 5000000,
    "ctr_base": 0.03,
    "conversion_rate": 0.02,
    "demographics_match": 0.8,
    "interests_match": 0.7
}

simulator.google_simulator.define_audience("tech_audience", audience_data)
simulator.facebook_simulator.define_audience("tech_audience", audience_data)
simulator.linkedin_simulator.define_audience("tech_audience", audience_data)

# Create campaigns
campaign_data = {
    "name": "Product Launch",
    "objective": "conversions",
    "daily_budget": 100.0,
    "targeting": {
        "audience": "tech_audience"
    }
}

campaign_ids = simulator.create_cross_platform_campaign(campaign_data)

# Run simulation
results = simulator.run_campaigns(days=30)

# Export results
simulator.export_results()
```

### API Usage

The platform includes a FastAPI-powered REST API that can be used to integrate with other tools:

```bash
# Start the API server
uvicorn api:app --reload
```

Example API request:

```python
import requests

# API credentials
headers = {
    "api-key": "YOUR_API_KEY",
    "Content-Type": "application/json"
}

# Create audience
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
    "http://localhost:8000/audiences",
    headers=headers,
    json=audience_data
)

# Create campaign
campaign_data = {
    "name": "API Test Campaign",
    "objective": "conversion",
    "daily_budget": 100.0,
    "targeting": {
        "audience": "tech_professionals"
    }
}

response = requests.post(
    "http://localhost:8000/campaigns/crossplatform",
    headers=headers,
    json=campaign_data
)

# Run simulation
simulation_data = {
    "days": 30,
    "platforms": ["all"]
}

response = requests.post(
    "http://localhost:8000/simulations",
    headers=headers,
    json=simulation_data
)

simulation_id = response.json()["simulation_id"]

# Get results
response = requests.get(
    f"http://localhost:8000/simulations/{simulation_id}/results",
    headers=headers
)

results = response.json()
```

See the API documentation at `http://localhost:8000/docs` after starting the server.

## Examples

The `example.py` file contains several examples of how to use the simulator:

1. Simple campaign example
2. Platform comparison
3. Budget optimization
4. Targeting optimization
5. API usage example

Run the examples:

```bash
python example.py
```

## License

MIT
