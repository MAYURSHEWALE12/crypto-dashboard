import requests

def get_current_prices():
    try:
        # Example API call to get prices for multiple coins
        response = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,litecoin&vs_currencies=usd')
        response.raise_for_status()  # Raise an error for bad responses
        return response.json()  # Returns a dictionary with coin prices
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return {}
