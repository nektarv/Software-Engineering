from flask import Flask, render_template
import requests
#from utils.map_generator import generate_map

app = Flask(__name__)
FASTAPI_URL = "https://localhost:9876"  # Your FastAPI backend

@app.route('/')
@app.route('/map')
def map_page():
    # Fetch chargers from FastAPI
    #response = requests.get(f"{FASTAPI_URL}/api/chargers")
    #chargers = response.json()
    
    # Generate Folium map HTML
    #map_html = generate_map(chargers)
    
    return render_template('map.html', 
                         #map_html=map_html, 
                         #chargers=chargers,
                         active_page='map')

@app.route('/list')
def list_page():
    #response = requests.get(f"{FASTAPI_URL}/api/chargers")
    #chargers = response.json()
    return render_template('list.html', 
                         #chargers=chargers,
                         active_page='list')

@app.route('/stats')
def stats_page():
    return render_template('stats.html', active_page='stats')

if __name__ == '__main__':
    app.run(debug=True, port=5000)