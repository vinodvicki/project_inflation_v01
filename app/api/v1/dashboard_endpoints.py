from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime # Added for inflation_impact default end_year

# Import services and models (actual Pydantic schemas for request/response later)
from app.services import compensation_analysis_service
from app.services import skill_analysis_service
from app.services import opportunity_discovery_service
from app.services import market_data_service # Import the new market data service
from app.db import get_db # For DB session dependency
from app.models.compensation import Compensation as CompensationModel
from app.models.user_skill import UserSkill as UserSkillModel
from app.core.auth import get_current_active_user, UserForAuth # UserForAuth for type hint

router = APIRouter()

# Placeholder for user authentication dependency
# In a real app, this would handle token validation and user retrieval
# async def get_current_user_placeholder(): # This is now replaced by get_current_active_user
#     # For MVP, we can simulate a user or raise an error if not implemented
#     # This should be replaced with actual authentication (Step 2 of plan)
#     print("Warning: Using placeholder authentication. No actual user is authenticated.")
#     class MockUser:
#         id: str = "mock_user_001" # Simulate a user ID
#         email: str = "user@example.com"
#     return MockUser()


@router.get("/dashboard/compensation-analysis",
            summary="Get User Compensation Analysis vs Market",
            # response_model=YourCompensationAnalysisResponseSchema # Define Pydantic schema later
            )
async def get_dashboard_compensation_analysis(
    role: str = Query(..., description="User's current or target job role"),
    location: str = Query(..., description="User's current or target location"),
    experience_level: Optional[str] = Query(None, description="User's experience level"),
    compensation_id: Optional[str] = Query(None, description="Specific compensation record ID to use; defaults to latest if not provided."),
    db: Session = Depends(get_db),
    current_user: UserForAuth = Depends(get_current_active_user)
):
    """
    Provides a comprehensive analysis of the user's compensation compared to market data,
    and includes an opportunity suggestion.
    """
    user_id = current_user.id

    # 1. Fetch user's compensation data from DB
    user_comp_query = db.query(CompensationModel).filter(CompensationModel.user_id == user_id)
    if compensation_id:
        user_comp_record = user_comp_query.filter(CompensationModel.id == compensation_id).first()
        if not user_comp_record:
            raise HTTPException(status_code=404, detail=f"Compensation record with id {compensation_id} not found for user.")
    else:
        user_comp_record = user_comp_query.order_by(CompensationModel.as_of_date.desc(), CompensationModel.created_at.desc()).first()

    if not user_comp_record:
        raise HTTPException(status_code=404, detail="No compensation records found for user. Please add your compensation details.")

    user_total_compensation = user_comp_record.calculated_total_compensation
    user_compensation_details = user_comp_record.to_dict()

    # 2. Fetch real market data using the market_data_service
    fetched_market_data = await market_data_service.fetch_market_compensation_data(
        role=role, location=location, experience_level=experience_level
    )

    market_data_for_response = None
    market_total_comp_benchmark = 0  # Default if no market data found
    gap_info = None
    opportunity_suggestion_text = "Market data not available for your query, so a full analysis cannot be provided."
    opportunity_action_type = "market_data_unavailable"

    if fetched_market_data and fetched_market_data.get("total_compensation_median") is not None:
        market_total_comp_benchmark = fetched_market_data["total_compensation_median"]

        # Prepare market_data_for_response based on fetched_market_data
        # This structure should align with what the frontend might expect or what we logged as mock_market_data_details
        market_data_for_response = {
            "role_matched": fetched_market_data.get("raw_response_preview", {}).get("role_matched", role),
            "location_matched": fetched_market_data.get("raw_response_preview", {}).get("location_matched", location),
            "experience_level_matched": experience_level or "N/A", # Or from fetched_market_data if available
            "source": fetched_market_data.get("source_description", "External Market Data"),
            "details": fetched_market_data # Contains medians for salary, bonus, stock, total_comp
        }

        # 3. Use the compensation_analysis_service
        gap_info = compensation_analysis_service.calculate_compensation_gap(
            user_total_compensation=user_total_compensation,
            market_total_compensation_benchmark=market_total_comp_benchmark
        )

        # 4. Fetch user's skills for Opportunity Finder
        user_skills_records = db.query(UserSkillModel.skill_name).filter(
            UserSkillModel.user_id == user_id, UserSkillModel.is_top_skill == True
        ).all()
        user_skill_names = [skill.skill_name for skill in user_skills_records]
        if not user_skill_names:
            user_skill_names = ["General Professional Skills"]

        skills_analysis_results_for_opp_finder = skill_analysis_service.analyze_user_skills(
            user_skills=user_skill_names, role_title=role
        )

        # 5. Construct data for opportunity_discovery_service
        compensation_analysis_data_for_opp = {
            "market_comparison": {
                "gap_analysis": gap_info,
                "market_total_compensation": {"p50_median": market_total_comp_benchmark},
                # Pass through more detailed market components if available and rules use them
                "market_salary_median": fetched_market_data.get("base_salary_median"),
                "market_bonus_median": fetched_market_data.get("bonus_annual_median"),
                "market_equity_median": fetched_market_data.get("stock_grant_annual_median"),
            },
            "user_compensation": user_compensation_details
        }

        opportunity_suggestion_obj = opportunity_discovery_service.find_next_opportunity_suggestion(
            compensation_analysis_data=compensation_analysis_data_for_opp,
            skills_analysis_data=skills_analysis_results_for_opp_finder
        )
        opportunity_suggestion_text = opportunity_suggestion_obj["suggestion_text"]
        opportunity_action_type = opportunity_suggestion_obj["action_type"]
    else:
        # Market data not found or incomplete, gap_info remains None
        # Use a default gap_info structure or indicate unavailability
        gap_info = {
            "user_total_compensation": user_total_compensation,
            "market_benchmark": 0,
            "gap_amount": user_total_compensation, # Or None, indicates user is "infinitely" above a 0 benchmark
            "gap_percentage": None, # Or some indicator of data missing
            "status": "market_data_unavailable"
        }
        # Opportunity suggestion already has a default message for this case

    return {
        "user_id": user_id,
        "query_params": {
            "role": role, "location": location, "experience_level": experience_level,
            "compensation_id": compensation_id
        },
        "user_compensation_details": user_compensation_details,
        "market_data_details": market_data_for_response, # This will be None if market data failed
        "compensation_gap_analysis": gap_info,
        "opportunity_suggestion": {
            "suggestion_text": opportunity_suggestion_text,
            "action_type": opportunity_action_type
        }
    }

@router.get("/dashboard/skills-analysis",
            summary="Get User Skills Analysis",
            # response_model=YourSkillsAnalysisResponseSchema # Define Pydantic schema later
            )
async def get_dashboard_skills_analysis(
    role: str = Query(..., description="User's current or target job role"),
    industry: Optional[str] = Query(None, description="User's industry"),
    experience_level: Optional[str] = Query(None, description="User's experience level"),
    # For future: user_skill_ids: Optional[List[str]] = Query(None, description="Specific UserSkill IDs to analyze."),
    db: Session = Depends(get_db),
    current_user: UserForAuth = Depends(get_current_active_user)
):
    """
    Analyzes the user's skills, highlighting top paying and in-demand ones.
    Fetches user's skills marked as 'is_top_skill = True' by default.
    """
    user_id = current_user.id

    # 1. Fetch user's skills from DB
    # For now, let's fetch skills marked as 'is_top_skill'.
    # Later, we could allow specifying skill IDs or fetching all skills.
    user_skill_records_query = db.query(UserSkillModel.skill_name).filter(
        UserSkillModel.user_id == user_id,
        UserSkillModel.is_top_skill == True # Or based on a query param
    )
    user_skill_records = user_skill_records_query.all()

    if not user_skill_records:
        # Return a standard response or raise HTTPException if no skills are found,
        # depending on desired behavior. For now, analyze an empty list.
        user_skill_names = []
        # Alternatively, could raise:
        # raise HTTPException(status_code=404, detail="No top skills found for user. Please add skills.")
    else:
        user_skill_names = [record.skill_name for record in user_skill_records]

    # 2. Call the skill_analysis_service
    skills_analysis_results = skill_analysis_service.analyze_user_skills(
        user_skills=user_skill_names, # Pass the fetched skill names
        role_title=role,
        industry=industry,
        experience_level=experience_level
    )

    return {
        "user_id": user_id,
        "query_context": {
            "role": role,
            "industry": industry,
            "experience_level": experience_level,
            "skills_source": "user_top_skills" # Indicate where the skills came from
        },
        "skills_analysis": skills_analysis_results
    }

# Inflation impact endpoint - placeholder, will require dedicated logic and data source
@router.get("/dashboard/inflation-impact",
            summary="Get Inflation Impact on Salary (Placeholder)",
            # response_model=YourInflationImpactResponseSchema
            )
async def get_dashboard_inflation_impact(
    salary_amount: float = Query(..., gt=0, description="Salary amount to analyze"),
    start_year: int = Query(..., ge=1900, le=datetime.now().year, description="Year the salary was set"),
    # end_year: Optional[int] = Query(None, description="Year to compare to, defaults to current year"),
    # region: Optional[str] = Query("US", description="Region for CPI data (e.g., US)"),
    current_user: dict = Depends(get_current_active_user) # Use the new auth dependency
):
    # This endpoint requires a CPI data source and calculation logic.
    # For MVP, this might be deferred or use very simplified/mocked data.
    return {
        "message": "Inflation impact endpoint is a placeholder.",
        "user_id": current_user.id,
        "params_received": {
            "salary_amount": salary_amount,
            "start_year": start_year,
            # "end_year": end_year or datetime.now().year,
            # "region": region
        },
        "data": "Actual inflation impact data will be calculated here."
    }
