import httpx
from typing import Optional, Dict, Any
from app.core.config import settings
import urllib.parse # For URL encoding parameters

# Define a Pydantic model for the expected structure of market data (optional but good practice)
# For now, returning a dict, but Pydantic would add validation.
# from pydantic import BaseModel
# class MarketCompensationData(BaseModel):
#     total_compensation_median: Optional[float] = None
#     base_salary_median: Optional[float] = None
#     stock_grant_annual_median: Optional[float] = None
#     bonus_annual_median: Optional[float] = None
#     source_description: str = "External Market Data"
#     # Add other fields like percentiles if needed

async def fetch_market_compensation_data(
    role: str,
    location: str,
    experience_level: Optional[str] = None
) -> Optional[Dict[str, Any]]: # Returning Optional[Dict] for now
    """
    Fetches market compensation data from the (hypothetical) external API.

    Args:
        role (str): The job role to query.
        location (str): The location to query.
        experience_level (Optional[str]): The experience level to query.

    Returns:
        Optional[Dict[str, Any]]: A dictionary containing structured market compensation data
                                  (e.g., medians for total_comp, salary, bonus, stock)
                                  or None if data cannot be fetched or is not found.
    """
    base_url = settings.MARKET_DATA_API_BASE_URL
    # Hypothetical endpoint: /salary_data (from our earlier simulation)
    # Example: https://api.levels.fyi/v1/salary_data
    endpoint = f"{base_url}/salary_data"

    params = {
        "role": role,
        "location": location,
    }
    if experience_level:
        params["level"] = experience_level # Assuming API uses 'level' for experience

    headers = {}
    if settings.MARKET_DATA_API_KEY and settings.MARKET_DATA_API_KEY != "your_api_key_here_if_needed":
        headers["Authorization"] = f"Bearer {settings.MARKET_DATA_API_KEY}"
        # Or "X-Api-Key": settings.MARKET_DATA_API_KEY, depending on API spec

    try:
        async with httpx.AsyncClient() as client:
            print(f"Fetching market data from: {endpoint} with params: {params}") # Logging
            response = await client.get(endpoint, params=params, headers=headers, timeout=10.0)
            response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)

            api_response_data = response.json()
            print(f"Market data API response: {api_response_data}") # Logging

            # Based on our HYPOTHETICAL Levels.fyi response structure:
            # {
            #   "data": {
            #     "compensation_summary": {
            #       "total_compensation": { "median": 275000, ... },
            #       "base_salary": { "median": 180000, ... },
            #       "stock_grant_annual": { "median": 70000, ... },
            #       "bonus_annual": { "median": 25000, ... }
            #     }, ...
            #   }
            # }

            # Transform the hypothetical API response into our desired internal format
            # This part is highly dependent on the actual API's response structure.
            if "data" in api_response_data and "compensation_summary" in api_response_data["data"]:
                summary = api_response_data["data"]["compensation_summary"]

                transformed_data = {
                    "total_compensation_median": summary.get("total_compensation", {}).get("median"),
                    "base_salary_median": summary.get("base_salary", {}).get("median"),
                    "stock_grant_annual_median": summary.get("stock_grant_annual", {}).get("median"),
                    "bonus_annual_median": summary.get("bonus_annual", {}).get("median"),
                    "source_description": api_response_data.get("data",{}).get("source_url", "Levels.fyi (simulated)"),
                    "raw_response_preview": { # For debugging, maybe remove in prod
                        "role_matched": api_response_data.get("data",{}).get("role_display_name"),
                        "location_matched": api_response_data.get("data",{}).get("location_display_name")
                    }
                }
                # Filter out None values if we only want to return what's available
                transformed_data = {k: v for k, v in transformed_data.items() if v is not None}

                if not transformed_data or not transformed_data.get("total_compensation_median"):
                    # If essential data like total_compensation_median is missing after parsing
                    print("Essential market data (e.g., total_compensation_median) not found in API response.")
                    return None

                return transformed_data
            else:
                print("Market data API response does not contain expected 'data.compensation_summary' structure.")
                return None

    except httpx.HTTPStatusError as e:
        # Handle HTTP errors (e.g., 401 Unauthorized, 404 Not Found from external API, 5xx Server Error)
        print(f"HTTP error occurred while fetching market data: {e.response.status_code} - {e.response.text}")
        # Depending on the error, you might want to return None or raise a custom exception
        if e.response.status_code == 404: # If the specific query returned 404 from market API
            return None
        # For other errors like 401, 403, 5xx, it might be a configuration or API issue.
        # Consider logging more details or raising a specific service exception.
        # For now, returning None for simplicity on client errors, but this could be more nuanced.
        return None # Or re-raise a custom service exception
    except httpx.RequestError as e:
        # Handle other request errors (e.g., network issue, timeout)
        print(f"Request error occurred while fetching market data: {e}")
        return None # Or raise custom service exception
    except Exception as e:
        # Catch-all for other unexpected errors during processing
        print(f"An unexpected error occurred while fetching market data: {e}")
        return None # Or raise custom service exception


# Example usage (for testing this service directly, if needed)
# import asyncio
# async def main():
#     data = await fetch_market_compensation_data(role="Software Engineer", location="San Francisco, CA", experience_level="L5")
#     if data:
#         print("\n--- Fetched Market Data ---")
#         for key, value in data.items():
#             print(f"{key}: {value}")
#     else:
#         print("\n--- Could not fetch market data ---")

# if __name__ == "__main__":
#     asyncio.run(main())
