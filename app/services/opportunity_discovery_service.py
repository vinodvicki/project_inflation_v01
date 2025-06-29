# app/services/opportunity_discovery_service.py

def find_next_opportunity_suggestion(compensation_analysis_data: dict, skills_analysis_data: dict):
    """
    Generates a single best action suggestion based on compensation and skills analysis.
    For MVP, this uses simplified rules.

    Args:
        compensation_analysis_data (dict): Expected to contain at least:
            {
                "market_comparison": {
                    "gap_analysis": {
                        "status": "below_market" | "at_market" | "above_market",
                        "gap_percentage": float
                    }
                }
                // Potentially user_compensation and market_benchmarks for more advanced rules later
            }
        skills_analysis_data (dict): Expected to contain at least:
            {
                "top_paying_skills": list[str], // User's skills that are high value
                "analyzed_skills": [ // List of dicts for all analyzed skills
                    { "skill_name": str, "salary_impact_indicator": "High"|"Medium"|"Low", "demand_score": int }, ...
                ]
            }

    Returns:
        dict: Containing 'suggestion_text' (str) and 'action_type' (str).
    """

    # Basic validation of input structure
    if not isinstance(compensation_analysis_data, dict) or \
       not isinstance(skills_analysis_data, dict):
        return {
            "suggestion_text": "Insufficient data to generate a suggestion. Please complete your profile.",
            "action_type": "review_data_error"
        }

    gap_analysis = compensation_analysis_data.get("market_comparison", {}).get("gap_analysis", {})
    if not gap_analysis:
        return {
            "suggestion_text": "Compensation analysis data is missing. Please calculate your market position first.",
            "action_type": "run_compensation_analysis"
        }

    market_status = gap_analysis.get("status")
    gap_percentage = gap_analysis.get("gap_percentage") # Can be None if status is e.g. market_data_error

    # Extract top skills information
    user_top_paying_skills_names = skills_analysis_data.get("top_paying_skills", [])

    # Fallback for top skills if specific list is empty but analysis exists
    if not user_top_paying_skills_names and skills_analysis_data.get("analyzed_skills"):
        analyzed_skills = skills_analysis_data.get("analyzed_skills", [])
        # Get up to 2 skills that are marked "High" impact, or have high demand score
        high_impact_or_demand = [
            s["skill_name"] for s in analyzed_skills
            if s.get("salary_impact_indicator", "").lower() == "high" or s.get("demand_score", 0) >= 85
        ]
        user_top_paying_skills_names = high_impact_or_demand[:2]

    skill_mention_str = ""
    if user_top_paying_skills_names:
        skill_mention_str = f"Highlighting your skills in {', '.join(user_top_paying_skills_names)} could strengthen your case."

    # --- Rule Engine ---

    # Extract user's compensation components for easier access
    user_comp_details = compensation_analysis_data.get("user_compensation", {})
    user_salary = user_comp_details.get("salary_annual", 0)
    user_bonus = user_comp_details.get("annual_bonus_amount_calculated", 0) # from property
    user_equity = user_comp_details.get("equity_value_annual", 0)

    # Extract market compensation components
    market_comp = compensation_analysis_data.get("market_comparison", {})
    market_salary_median = market_comp.get("market_salary_median") # Might be None
    market_bonus_median = market_comp.get("market_bonus_median")   # Might be None
    market_equity_median = market_comp.get("market_equity_median") # Might be None

    significant_component_gap_threshold = 0.10 # 10%

    if market_status == "market_data_error" or gap_percentage is None:
        return {
            "suggestion_text": "Could not determine market position due to data issues. Please try again or update your role/location.",
            "action_type": "review_market_data_input"
        }

    # Rule 0: Component-specific suggestions if user is below market overall
    if market_status == "below_market":
        # Check Salary Gap
        if market_salary_median and user_salary < market_salary_median * (1 - significant_component_gap_threshold):
            salary_gap_perc = ((market_salary_median - user_salary) / market_salary_median) * 100
            return {
                "suggestion_text": f"Your base salary appears to be about {salary_gap_perc:.0f}% below the market median of ${market_salary_median:,.0f}. Consider focusing on negotiating a salary increase. {skill_mention_str}",
                "action_type": "negotiate_salary"
            }
        # Check Bonus Gap
        if market_bonus_median and user_bonus < market_bonus_median * (1 - significant_component_gap_threshold):
            # Note: user_bonus might be 0 if not applicable. market_bonus_median could also be 0.
            bonus_gap_perc_text = ""
            if market_bonus_median > 0 : # Avoid division by zero if market bonus is 0
                bonus_gap_perc = ((market_bonus_median - user_bonus) / market_bonus_median) * 100
                bonus_gap_perc_text = f"about {bonus_gap_perc:.0f}% "
            return {
                "suggestion_text": f"Your bonus seems {bonus_gap_perc_text}lower than the typical market bonus of ${market_bonus_median:,.0f}. This could be an area for discussion. {skill_mention_str}",
                "action_type": "negotiate_bonus"
            }
        # Check Equity Gap
        if market_equity_median and user_equity < market_equity_median * (1 - significant_component_gap_threshold):
            equity_gap_perc_text = ""
            if market_equity_median > 0:
                equity_gap_perc = ((market_equity_median - user_equity) / market_equity_median) * 100
                equity_gap_perc_text = f"about {equity_gap_perc:.0f}% "
            return {
                "suggestion_text": f"Your annual equity value appears {equity_gap_perc_text}below the market median of ${market_equity_median:,.0f}. If seeking new roles or in reviews, aim for a more competitive equity package. {skill_mention_str}",
                "action_type": "negotiate_equity"
            }

    # Rule 1: Significantly Below Market Overall (>15%), no specific component stood out or component data was missing
    if market_status == "below_market" and gap_percentage > 15:
        return {
            "suggestion_text": f"Your total compensation appears to be {gap_percentage:.1f}% below the market median. This is a significant gap. Focus on negotiating a comprehensive increase. {skill_mention_str}",
            "action_type": "negotiate_total_compensation_significant"
        }

    # Rule 2: Moderately Below Market Overall (5-15%), no specific component stood out
    if market_status == "below_market" and gap_percentage > 5: # This will catch remaining "below_market" cases
        return {
            "suggestion_text": f"Your total compensation is about {gap_percentage:.1f}% below the market median. Consider discussing an adjustment with your manager. {skill_mention_str}",
            "action_type": "negotiate_total_compensation_moderate"
        }

    # Rule 3: Slightly Below Market or At Market, but with High-Impact Skills
    if (market_status == "at_market") or (market_status == "below_market" and gap_percentage <= 5): # Catches any remaining "below_market"
        high_impact_skills_from_analysis = [
            s["skill_name"] for s in skills_analysis_data.get("analyzed_skills", [])
            if s.get("salary_impact_indicator", "").lower() == "high"
        ]
        if not high_impact_skills_from_analysis:
            high_impact_skills_from_analysis = user_top_paying_skills_names

        if high_impact_skills_from_analysis:
            prefix = "You're currently compensated close to or at the market rate." if market_status == "at_market" else "Your compensation is slightly below market, or specific components may vary."
            return {
                "suggestion_text": f"{prefix} To enhance your earnings, focus on leveraging your valuable skills in {', '.join(high_impact_skills_from_analysis)}. Ensure these are visible and their impact is clear.",
                "action_type": "leverage_high_impact_skills"
            }
        if market_status == "at_market": # Fallback if at_market and no high-impact skills found by above
             return {
                "suggestion_text": "Your compensation is aligned with the current market. Continue to develop your skills and track achievements for future growth.",
                "action_type": "maintain_and_develop"
            }

    # Rule 4: At Market (general fallback if not caught by Rule 3)
    if market_status == "at_market":
        return {
            "suggestion_text": "Your compensation is aligned with the current market. Focus on continuous skill development and documenting your achievements.",
            "action_type": "maintain_and_develop"
        }

    # Rule 5: Above Market
    if market_status == "above_market":
        return {
            "suggestion_text": f"Congratulations! Your current compensation is approximately {abs(gap_percentage):.1f}% above the market median. Maintain your strong performance and continue skill development.",
            "action_type": "maintain_high_performance"
        }

    # Default / Catch-all: Should ideally not be reached if market_status is one of the expected values.
    return {
        "suggestion_text": "Please review your compensation and skills details to get the most accurate suggestions. Understanding your market position is key.",
        "action_type": "review_data_default"
    }

if __name__ == '__main__':
    # Example Usages:
    print("--- Example Suggestions ---")

    # Scenario 1: Significantly Below Market
    comp_data_1 = {"market_comparison": {"gap_analysis": {"status": "below_market", "gap_percentage": 20.0}}}
    skills_data_1 = {"top_paying_skills": ["Python", "AWS"], "analyzed_skills": [
        {"skill_name": "Python", "salary_impact_indicator": "High", "demand_score": 90},
        {"skill_name": "AWS", "salary_impact_indicator": "High", "demand_score": 88},
    ]}
    print(f"\nScenario 1 (Significantly Below): {find_next_opportunity_suggestion(comp_data_1, skills_data_1)}")

    # Scenario 2: At Market, with High Impact Skills
    comp_data_2 = {"market_comparison": {"gap_analysis": {"status": "at_market", "gap_percentage": -1.0}}} # Slightly above
    skills_data_2 = {"top_paying_skills": ["Machine Learning"], "analyzed_skills": [
        {"skill_name": "Machine Learning", "salary_impact_indicator": "High", "demand_score": 95},
        {"skill_name": "Communication", "salary_impact_indicator": "Medium", "demand_score": 80},
    ]}
    print(f"\nScenario 2 (At Market, High Skills): {find_next_opportunity_suggestion(comp_data_2, skills_data_2)}")

    # Scenario 3: Above Market
    comp_data_3 = {"market_comparison": {"gap_analysis": {"status": "above_market", "gap_percentage": -10.0}}}
    skills_data_3 = {"top_paying_skills": [], "analyzed_skills": []} # No specific skills to highlight
    print(f"\nScenario 3 (Above Market): {find_next_opportunity_suggestion(comp_data_3, skills_data_3)}")

    # Scenario 4: Moderately Below, no specific high impact skills from "top_paying_skills" but some in analyzed
    comp_data_4 = {"market_comparison": {"gap_analysis": {"status": "below_market", "gap_percentage": 8.0}}}
    skills_data_4 = {"top_paying_skills": [], "analyzed_skills": [
        {"skill_name": "Java", "salary_impact_indicator": "Medium", "demand_score": 88},
        {"skill_name": "SQL", "salary_impact_indicator": "Medium", "demand_score": 82},
    ]}
    print(f"\nScenario 4 (Moderately Below, general skills): {find_next_opportunity_suggestion(comp_data_4, skills_data_4)}")

    # Scenario 5: At Market, no particularly standout skills
    comp_data_5 = {"market_comparison": {"gap_analysis": {"status": "at_market", "gap_percentage": 0.0}}}
    skills_data_5 = {"top_paying_skills": [], "analyzed_skills": [
        {"skill_name": "Office Suite", "salary_impact_indicator": "Low", "demand_score": 60},
    ]}
    print(f"\nScenario 5 (At Market, average skills): {find_next_opportunity_suggestion(comp_data_5, skills_data_5)}")

    # Scenario 6: Market Data Error
    comp_data_6 = {"market_comparison": {"gap_analysis": {"status": "market_data_error", "gap_percentage": None}}}
    skills_data_6 = {"top_paying_skills": [], "analyzed_skills": []}
    print(f"\nScenario 6 (Market Data Error): {find_next_opportunity_suggestion(comp_data_6, skills_data_6)}")
