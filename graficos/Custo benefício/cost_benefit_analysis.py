# cost_benefit_analysis.py

def cost_benefit_analysis(costs, benefits):
    """
    Function to perform a simple cost-benefit analysis.
    
    Parameters:
    costs (list): A list of costs associated with a project.
    benefits (list): A list of benefits associated with a project.
    
    Returns:
    str: Evaluation of the cost-benefit analysis.
    """
    total_costs = sum(costs)
    total_benefits = sum(benefits)
    
    if total_benefits > total_costs:
        return "The project is beneficial."
    elif total_benefits < total_costs:
        return "The project is not beneficial."
    else:
        return "The project breaks even."

# Example usage
if __name__ == "__main__":
    costs = [1000, 2000, 3000]
    benefits = [6000, 5000, 4000]
    result = cost_benefit_analysis(costs, benefits)
    print(result)