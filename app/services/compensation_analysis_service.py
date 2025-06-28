def calculate_compensation_gap(user_total_compensation: float, market_total_compensation_benchmark: float):
    """
    Calculates the gap between user's total compensation and a market benchmark.

    Args:
        user_total_compensation (float): The user's calculated total annual compensation.
        market_total_compensation_benchmark (float): The market total annual compensation
                                                     benchmark (e.g., median/p50) for a
                                                     comparable role.

    Returns:
        dict: A dictionary containing:
            - 'user_total_compensation': The user's total compensation.
            - 'market_benchmark': The market benchmark used.
            - 'gap_amount': The difference (market - user). Positive if user is below market.
            - 'gap_percentage': The percentage difference relative to the market benchmark.
                               Positive if user is below market.
            - 'status': A string indicating if the user is 'below_market', 'at_market', or 'above_market'.
                        Returns 'market_data_error' if market_total_compensation_benchmark is invalid.
    """
    if not isinstance(user_total_compensation, (int, float)):
        raise TypeError("user_total_compensation must be a number.")
    if not isinstance(market_total_compensation_benchmark, (int, float)):
        raise TypeError("market_total_compensation_benchmark must be a number.")

    if market_total_compensation_benchmark <= 0:
        # Avoid division by zero or meaningless percentages if market data is invalid
        return {
            "user_total_compensation": user_total_compensation,
            "market_benchmark": market_total_compensation_benchmark,
            "gap_amount": 0,
            "gap_percentage": 0,
            "status": "market_data_error"
        }

    gap_amount = market_total_compensation_benchmark - user_total_compensation

    gap_percentage = (gap_amount / market_total_compensation_benchmark) * 100

    status = ""
    # Using a small threshold for "at market" to account for minor floating point differences
    # or very small, negligible gaps.
    # Define epsilon relative to the market benchmark to scale appropriately.
    # For example, within 0.1% of market value might be considered "at market".
    epsilon_percentage = 0.1 # 0.1% threshold

    if abs(gap_percentage) < epsilon_percentage:
        status = "at_market"
    elif gap_amount > 0: # User is paid less than market
        status = "below_market"
    else: # gap_amount < 0, user is paid more than market
        status = "above_market"

    return {
        "user_total_compensation": round(user_total_compensation, 2),
        "market_benchmark": round(market_total_compensation_benchmark, 2),
        "gap_amount": round(gap_amount, 2),
        "gap_percentage": round(gap_percentage, 2),
        "status": status
    }
