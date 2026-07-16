import json
import urllib.request
from langchain_core.tools import tool

@tool
def get_current_city():
    """Calling this tool will return the current city of the user as string"""
    print("Getting current city")
    try:
        
        url = "http://ip-api.com/json/"
        response = urllib.request.urlopen(url)
        data = json.loads(response.read().decode())
        
        if data.get("status") == "success":
            return data.get("city")
        else:
            return "Location not found"
            
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    user_city = get_current_city()
    print(f"Current City: {user_city}")
