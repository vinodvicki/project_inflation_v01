import json # For mocking API responses, and example printing

# This would be replaced by actual API call logic in a real application
def _mock_skill_rank_api_call(user_skills: list[str], role_context: dict):
    """
    Mocks a call to the hypothetical SkillRank API.
    In a real scenario, this would involve HTTP requests, authentication, error handling, etc.
    """
    # print(f"Mock API Call to SkillRank: Skills: {user_skills}, Context: {role_context}") # For debugging

    mock_data = {
        "analyzed_skills": [],
        "summary": {
            "top_paying_skills_in_query": [],
            "overall_skill_set_strength": "Moderate" # Default
        }
    }

    # Define some keywords for mock analysis
    high_impact_keywords = ["machine learning", "ai", "artificial intelligence", "python", "go", "rust", "cloud computing", "aws", "azure", "gcp", "cybersecurity", "devops", "kubernetes", "blockchain"]
    medium_impact_keywords = ["data analysis", "sql", "project management", "product management", "java", "c#", ".net", "javascript", "typescript", "react", "angular", "vue", "node.js", "agile methodologies"]
    # Soft skills are important but their direct "pay impact" is harder for a simple mock
    soft_skills_keywords = ["communication", "teamwork", "leadership", "problem solving", "critical thinking"]


    top_paying_skills_found = []

    for skill_idx, skill_name in enumerate(user_skills):
        skill_lower = skill_name.lower()
        analysis = {
            "skill_name": skill_name,
            "normalized_skill": skill_name.capitalize(), # Simple normalization for mock
            "demand_score": 50 + (skill_idx % 10) * 2, # Base demand, with some variance
            "salary_impact_indicator": "Low",
            "category": "General"
        }

        is_high_impact = any(keyword in skill_lower for keyword in high_impact_keywords)
        is_medium_impact = any(keyword in skill_lower for keyword in medium_impact_keywords)
        is_soft_skill = any(keyword in skill_lower for keyword in soft_skills_keywords)

        if is_high_impact:
            analysis["demand_score"] = 90 + (skill_idx % 5) # Add some variance (0-4)
            analysis["salary_impact_indicator"] = "High"
            analysis["category"] = "Technical - High Impact"
            if len(top_paying_skills_found) < 3: # Limit to top N for summary
                 top_paying_skills_found.append(skill_name)
        elif is_medium_impact:
            analysis["demand_score"] = 75 + (skill_idx % 10) # Add some variance (0-9)
            analysis["salary_impact_indicator"] = "Medium"
            analysis["category"] = "Technical - Medium Impact"
        elif is_soft_skill:
            analysis["demand_score"] = 70 + (skill_idx % 10)
            analysis["salary_impact_indicator"] = "Varies" # Hard to quantify directly
            analysis["category"] = "Soft Skill"

        mock_data["analyzed_skills"].append(analysis)

    mock_data["summary"]["top_paying_skills_in_query"] = top_paying_skills_found

    if len(top_paying_skills_found) >= 2 and any(s["demand_score"] > 90 for s in mock_data["analyzed_skills"]):
        mock_data["summary"]["overall_skill_set_strength"] = "Strong"
    elif len(top_paying_skills_found) >= 1 and any(s["demand_score"] > 80 for s in mock_data["analyzed_skills"]):
        mock_data["summary"]["overall_skill_set_strength"] = "Good"

    # Sort skills by demand score for presentation
    mock_data["analyzed_skills"] = sorted(mock_data["analyzed_skills"], key=lambda x: x["demand_score"], reverse=True)

    return mock_data


def analyze_user_skills(user_skills: list[str], role_title: str, industry: str = None, experience_level: str = None):
    """
    Analyzes user's skills to identify in-demand and high-impact skills for their role.

    Args:
        user_skills (list[str]): A list of skills provided by the user.
        role_title (str): The user's job title.
        industry (str, optional): The user's industry.
        experience_level (str, optional): The user's experience level.

    Returns:
        dict: A dictionary containing the skill analysis results, including:
            - 'analyzed_skills': A list of dictionaries, each detailing a skill's
                                 demand and impact. (Sorted by demand_score desc)
            - 'top_paying_skills': A list of the user's skills identified as having
                                   high pay impact by the mock API.
            - 'summary_message': A brief summary message.
    """
    if not isinstance(user_skills, list) or not all(isinstance(s, str) for s in user_skills):
        raise TypeError("user_skills must be a list of strings.")
    if not user_skills:
        return {
            "analyzed_skills": [],
            "top_paying_skills": [],
            "summary_message": "No skills provided for analysis."
        }

    role_context = {"title": role_title}
    if industry:
        role_context["industry"] = industry
    if experience_level:
        role_context["experience_level"] = experience_level

    api_response = _mock_skill_rank_api_call(user_skills, role_context)

    processed_skills = api_response.get("analyzed_skills", [])
    top_paying_skills_from_api = api_response.get("summary", {}).get("top_paying_skills_in_query", [])

    strength_summary = api_response.get('summary', {}).get('overall_skill_set_strength', 'N/A')
    summary_message = (f"Skill analysis for '{role_title}' complete. "
                       f"Identified {len(top_paying_skills_from_api)} high-impact skill(s) from your list. "
                       f"Overall skill set strength for this role context: {strength_summary}.")

    return {
        "analyzed_skills": processed_skills,
        "top_paying_skills": top_paying_skills_from_api,
        "summary_message": summary_message
    }

if __name__ == '__main__':
    # Example Usage:
    example_skills_1 = ["Python", "Project Management", "Data Analysis", "Machine Learning", "Communication", "AWS"]
    example_role_1 = "Software Engineer"
    example_industry_1 = "Technology"
    results_1 = analyze_user_skills(example_skills_1, example_role_1, example_industry_1)
    print("--- Example 1 ---")
    print(json.dumps(results_1, indent=2))

    example_skills_2 = ["Strategic Planning", "Budgeting", "Microsoft Excel"]
    example_role_2 = "Accountant"
    results_2 = analyze_user_skills(example_skills_2, example_role_2)
    print("\n--- Example 2 ---")
    print(json.dumps(results_2, indent=2))

    example_skills_3 = ["Java", "Spring Boot", "Agile Methodologies"]
    example_role_3 = "Backend Developer"
    results_3 = analyze_user_skills(example_skills_3, example_role_3, "Finance")
    print("\n--- Example 3 ---")
    print(json.dumps(results_3, indent=2))
