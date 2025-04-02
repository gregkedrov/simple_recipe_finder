# --- Step 1: Import Necessary Libraries ---
import os
import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request # Import Flask things
import re
# --- Step 2: Load Environment Variables & API Key ---
load_dotenv()
API_KEY = os.getenv("SPOONACULAR_API_KEY")

# Check if API key is loaded (same as before)
if not API_KEY:
    print("FATAL ERROR: Spoonacular API key not found in .env file.")
    print("The web application cannot start without it.")
    exit() # Stop the application if key is missing

# URLs (same as before)
SPOONACULAR_SEARCH_URL = "https://api.spoonacular.com/recipes/findByIngredients"
SPOONACULAR_RECIPE_INFO_URL = "https://api.spoonacular.com/recipes/{id}/information"

# --- Step 3: Initialize Flask Application ---
app = Flask(__name__) # Create an instance of the Flask class

# --- Step 4: Define Routes (Web Page URLs) ---

# Route for the main homepage (when someone visits "/")
@app.route('/')
def index():
    """Renders the main search page."""
    # Tells Flask to find 'index.html' in the 'templates' folder and show it
    return render_template('index.html')

# Route for handling the search form submission (listens to "/search")
# methods=['POST'] means this route only activates when a form is submitted, not just visited
@app.route('/search', methods=['POST'])
def search():
    """Handles the ingredient search form submission."""
    # Get the ingredients string submitted from the HTML form's input field named 'ingredients'
    ingredients_input = request.form.get('ingredients')

    if not ingredients_input:
        # If no ingredients were entered, maybe show an error or redirect back
        # For simplicity, we'll just render the results page with an error message
        return render_template('results.html', error="Please enter some ingredients.")

    ingredients_list = ingredients_input.strip()
    # Get selected cuisine and diet from the form (will be None if not submitted, or "" if '-- Any --' selected)
    selected_cuisine = request.form.get('cuisine')
    selected_diet = request.form.get('diet')
    # Prepare Spoonacular API parameters (same logic as before)
    params = {
        'apiKey': API_KEY,
        'ingredients': ingredients_list,
        'number': 10, # Let's ask for 10 results for the web page
        'ranking': 1,
        'ignorePantry': True
    }
 # --- ADD FILTER PARAMETERS ONLY IF SELECTED ---
    if selected_cuisine: # Only add if 'selected_cuisine' has a non-empty value
        params['cuisine'] = selected_cuisine

    if selected_diet: # Only add if 'selected_diet' has a non-empty value
        params['diet'] = selected_diet
    # --- END OF ADDED FILTER LOGIC ---
    # Call Spoonacular API (wrapped in try/except)
    found_recipes = [] # Initialize empty list to hold results
    api_error = None # Variable to hold any API error message

    try:
        response = requests.get(SPOONACULAR_SEARCH_URL, params=params)
        response.raise_for_status() # Check for HTTP errors
        recipes_data = response.json()

        if recipes_data:
            found_recipes = recipes_data # Store the list of recipes if found
        else:
            api_error = "No recipes found for those ingredients."

    except requests.exceptions.RequestException as e:
        print(f"Spoonacular API Error: {e}") # Log error to terminal
        api_error = f"Could not connect to recipe service: {e}"
    except Exception as e:
        print(f"Unexpected Error during search: {e}") # Log error to terminal
        api_error = "An unexpected error occurred during the search."

    # Render the 'results.html' template, passing the found recipes or error message to it
    return render_template('results.html', recipes=found_recipes, error=api_error, searched_ingredients=ingredients_list, selected_cuisine=selected_cuisine, # Pass cuisine filter
    selected_diet=selected_diet)      # Pass diet filter)

# Route for displaying recipe details (listens to "/recipe/RECIPE_ID")
@app.route('/recipe/<int:recipe_id>') # <int:recipe_id> captures the number from the URL
def recipe_details(recipe_id):
    """Fetches and displays details for a specific recipe ID."""
    recipe_info_url = SPOONACULAR_RECIPE_INFO_URL.format(id=recipe_id)
    info_params = {'apiKey': API_KEY}
    details = None
    api_error = None

    try:
        info_response = requests.get(recipe_info_url, params=info_params)
        info_response.raise_for_status()
        details = info_response.json()

        # Basic instruction cleaning (add import re at the top if you use this)
        if details.get('instructions'):
             import re # Add 'import re' at the top with other imports!
             details['cleaned_instructions'] = re.sub('<[^<]+?>', '', details['instructions'])
        elif details.get('analyzedInstructions') and details['analyzedInstructions'][0].get('steps'):
             # Combine steps into a single string for simple display
             steps = [f"{step.get('number', '')}. {step.get('step', '')}" for step in details['analyzedInstructions'][0]['steps']]
             details['cleaned_instructions'] = "\n".join(steps)
        else:
             details['cleaned_instructions'] = "No detailed instructions provided."


    except requests.exceptions.RequestException as e:
        print(f"Spoonacular Detail API Error: {e}")
        api_error = f"Could not fetch recipe details: {e}"
    except Exception as e:
        print(f"Unexpected Error fetching details: {e}")
        api_error = "An unexpected error occurred fetching details."

    return render_template('details.html', details=details, error=api_error)


# --- Step 5: Run the Flask Application ---
if __name__ == '__main__':
    # This makes the app run only when you execute `python app.py` directly
    # debug=True automatically restarts the server when you save changes (great for development)
    # Use host='0.0.0.0' to make it accessible from other devices on your network (optional)
    app.run(debug=True)