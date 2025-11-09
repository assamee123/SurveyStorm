#!/usr/bin/env python3
"""
DWD Weather Dashboard - Production Version for Web Deployment
Optimized for free hosting on Render, Railway, or Hugging Face Spaces
"""

import os
import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import json
from pathlib import Path
import hashlib
from typing import Dict, List, Optional

# Get port from environment variable (for cloud deployment)
port = int(os.environ.get("PORT", 8050))

# Default AOI: Hamburg coastal water area
DEFAULT_LAT = float(os.environ.get("DEFAULT_LAT", 53.55))
DEFAULT_LON = float(os.environ.get("DEFAULT_LON", 9.99))
DEFAULT_ZOOM = 10

# Use temporary directory for cloud deployments
CACHE_DIR = Path(os.environ.get("CACHE_DIR", "/tmp/cache_dwd_data"))
CACHE_DIR.mkdir(exist_ok=True)

class DWDDataFetcher:
    """Simplified DWD data fetcher for web deployment"""
    
    def __init__(self):
        self.stations_df = self.get_default_stations()
    
    def get_default_stations(self):
        """Return default stations for demo"""
        return pd.DataFrame([
            {'station_id': '00954', 'name': 'Hamburg-Fuhlsbüttel', 'lat': 53.6332, 'lon': 9.9881, 'height': 11},
            {'station_id': '01975', 'name': 'Hamburg-Neuwiedenthal', 'lat': 53.4777, 'lon': 9.8966, 'height': 3},
            {'station_id': '05516', 'name': 'Schleswig', 'lat': 54.5276, 'lon': 9.5490, 'height': 43},
            {'station_id': '00691', 'name': 'Bremen', 'lat': 53.0475, 'lon': 8.7981, 'height': 5},
            {'station_id': '00891', 'name': 'Cuxhaven', 'lat': 53.8706, 'lon': 8.7211, 'height': 5},
            {'station_id': '03032', 'name': 'Lübeck', 'lat': 53.8072, 'lon': 10.7083, 'height': 15},
            {'station_id': '01757', 'name': 'Kiel-Holtenau', 'lat': 54.3774, 'lon': 10.1424, 'height': 27},
        ])
    
    def find_nearest_station(self, lat: float, lon: float) -> Dict:
        """Find nearest weather station"""
        if self.stations_df.empty:
            return None
        
        distances = np.sqrt((self.stations_df['lat'] - lat)**2 + 
                          (self.stations_df['lon'] - lon)**2)
        nearest_idx = distances.idxmin()
        station = self.stations_df.loc[nearest_idx].to_dict()
        station['distance_km'] = distances[nearest_idx] * 111
        return station
    
    def generate_weather_data(self, station_id: str, hours: int = 72) -> Dict[str, pd.DataFrame]:
        """Generate realistic demo weather data"""
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=hours)
        date_range = pd.date_range(start=start_date, end=end_date, freq='H')
        n_hours = len(date_range)
        
        # Create realistic patterns
        hour_of_day = np.array([d.hour for d in date_range])
        day_progress = np.arange(n_hours) / n_hours
        
        data = {}
        
        # Temperature with daily cycle
        base_temp = 12 + 8 * np.sin(2 * np.pi * day_progress)
        daily_cycle = 5 * np.sin(2 * np.pi * (hour_of_day - 6) / 24)
        data['temperature'] = pd.DataFrame({
            'datetime': date_range,
            'temperature_c': base_temp + daily_cycle + np.random.normal(0, 1, n_hours)
        })
        
        # Precipitation (intermittent)
        rain_events = np.random.random(n_hours) < 0.2
        data['precipitation'] = pd.DataFrame({
            'datetime': date_range,
            'precipitation_mm': np.where(rain_events, np.random.exponential(2, n_hours), 0)
        })
        
        # Wind
        data['wind'] = pd.DataFrame({
            'datetime': date_range,
            'wind_speed_ms': 8 + 4 * np.sin(2 * np.pi * day_progress * 2) + np.random.normal(0, 2, n_hours)
        })
        
        # Sunshine
        daylight = (hour_of_day >= 6) & (hour_of_day <= 20)
        cloud_factor = np.random.beta(2, 5, n_hours)
        data['sunshine'] = pd.DataFrame({
            'datetime': date_range,
            'sunshine_minutes': np.where(daylight, 60 * (1 - cloud_factor), 0)
        })
        
        # Cloud cover
        data['cloudiness'] = pd.DataFrame({
            'datetime': date_range,
            'cloud_cover_oktas': 4 + 3 * np.sin(2 * np.pi * day_progress * 1.5) + np.random.normal(0, 1, n_hours)
        })
        
        return data

class WeatherAnalyzer:
    """Weather analysis for survey suitability"""
    
    @staticmethod
    def calculate_ssi(weather_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Calculate Survey Suitability Index"""
        
        # Merge all data
        merged = weather_data['temperature'].set_index('datetime')
        for key, df in weather_data.items():
            if key != 'temperature':
                merged = merged.join(df.set_index('datetime'), rsuffix=f'_{key}')
        
        scores = pd.DataFrame(index=merged.index)
        
        # Temperature score
        temp = merged['temperature_c']
        scores['temp_score'] = np.where(
            (temp >= 15) & (temp <= 25), 100,
            np.where((temp >= 10) & (temp <= 30), 75,
            np.where((temp >= 5) & (temp <= 35), 50, 25))
        )
        
        # Precipitation score
        precip = merged['precipitation_mm']
        scores['precip_score'] = np.clip(100 - precip * 10, 0, 100)
        
        # Wind score
        wind = merged['wind_speed_ms']
        scores['wind_score'] = np.clip(100 - (wind - 5) * 6.67, 0, 100)
        
        # Sunshine score
        sun = merged['sunshine_minutes']
        scores['sun_score'] = 25 + (sun / 60) * 75
        
        # Cloud score
        cloud = merged['cloud_cover_oktas'].clip(0, 8)
        scores['cloud_score'] = 100 - (cloud / 8) * 75
        
        # Calculate weighted SSI
        weights = {
            'temp_score': 0.15,
            'precip_score': 0.35,
            'wind_score': 0.30,
            'sun_score': 0.10,
            'cloud_score': 0.10
        }
        
        scores['SSI'] = sum(scores[col] * weights[col] for col in weights.keys())
        
        scores['category'] = pd.cut(scores['SSI'], 
                                   bins=[0, 40, 70, 100],
                                   labels=['Poor', 'Moderate', 'Good'])
        
        scores['color'] = scores['category'].map({
            'Poor': '#FF4444',
            'Moderate': '#FFA500', 
            'Good': '#44FF44'
        })
        
        return scores.reset_index()

# Initialize components
data_fetcher = DWDDataFetcher()
weather_analyzer = WeatherAnalyzer()

# Create Dash app
app = dash.Dash(__name__)
server = app.server  # Expose server for deployment

app.layout = html.Div([
    # Header
    html.Div([
        html.H1("🌤️ DWD Weather Dashboard for Survey Planning", 
                style={'textAlign': 'center', 'color': '#2c3e50'}),
        html.P("Click on the map to select your Area of Interest",
               style={'textAlign': 'center', 'color': '#7f8c8d'})
    ], style={'backgroundColor': '#ecf0f1', 'padding': '20px', 'marginBottom': '20px'}),
    
    # Main content
    html.Div([
        # Left panel - Map
        html.Div([
            dcc.Graph(
                id='aoi-map',
                style={'height': '400px'},
                config={'displayModeBar': False}
            ),
            
            html.Div(id='location-info', 
                    style={'padding': '10px', 'backgroundColor': '#f8f9fa',
                          'borderRadius': '5px', 'marginTop': '10px'}),
            
            html.Div([
                html.Button('🔄 Refresh Data', id='refresh-btn', 
                           style={'marginRight': '10px', 'padding': '10px 20px',
                                 'backgroundColor': '#3498db', 'color': 'white',
                                 'border': 'none', 'borderRadius': '5px',
                                 'cursor': 'pointer'}),
                dcc.Dropdown(
                    id='time-range',
                    options=[
                        {'label': '24 Hours', 'value': '24'},
                        {'label': '3 Days', 'value': '72'},
                        {'label': '7 Days', 'value': '168'},
                    ],
                    value='72',
                    style={'width': '120px', 'display': 'inline-block',
                          'marginLeft': '10px'}
                )
            ], style={'marginTop': '10px'})
            
        ], style={'width': '40%', 'display': 'inline-block', 
                 'verticalAlign': 'top', 'padding': '10px'}),
        
        # Right panel - Charts
        html.Div([
            html.Div([
                html.H3('📈 Survey Suitability Index'),
                dcc.Graph(id='ssi-chart', style={'height': '250px'})
            ]),
            
            html.Div([
                html.H3('🌡️ Weather Parameters'),
                dcc.Graph(id='weather-chart', style={'height': '400px'})
            ], style={'marginTop': '20px'})
            
        ], style={'width': '58%', 'display': 'inline-block', 'padding': '10px'})
    ]),
    
    # Hidden storage
    dcc.Store(id='selected-location', data={'lat': DEFAULT_LAT, 'lon': DEFAULT_LON})
])

@app.callback(
    [Output('aoi-map', 'figure'),
     Output('selected-location', 'data')],
    [Input('aoi-map', 'clickData')],
    [State('selected-location', 'data')]
)
def update_map(clickData, current_location):
    """Update map with selected location"""
    
    lat, lon = current_location['lat'], current_location['lon']
    
    if clickData and 'points' in clickData:
        point = clickData['points'][0]
        if 'lat' in point and 'lon' in point:
            lat, lon = point['lat'], point['lon']
    
    stations_df = data_fetcher.stations_df
    
    fig = go.Figure()
    
    # Add station markers
    fig.add_trace(go.Scattermapbox(
        lat=stations_df['lat'],
        lon=stations_df['lon'],
        mode='markers',
        marker=dict(size=8, color='lightblue'),
        text=stations_df['name'],
        hovertemplate='<b>%{text}</b><br>Lat: %{lat:.2f}<br>Lon: %{lon:.2f}<extra></extra>',
        name='Stations'
    ))
    
    # Add selected location
    fig.add_trace(go.Scattermapbox(
        lat=[lat],
        lon=[lon],
        mode='markers',
        marker=dict(size=15, color='red'),
        text=['Selected AOI'],
        name='Selected'
    ))
    
    fig.update_layout(
        mapbox=dict(
            style='open-street-map',
            center=dict(lat=lat, lon=lon),
            zoom=DEFAULT_ZOOM
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=True
    )
    
    return fig, {'lat': lat, 'lon': lon}

@app.callback(
    Output('location-info', 'children'),
    [Input('selected-location', 'data')]
)
def update_location_info(location):
    """Display location information"""
    
    lat, lon = location['lat'], location['lon']
    station = data_fetcher.find_nearest_station(lat, lon)
    
    if station:
        return html.Div([
            html.H4(f"📍 {station['name']}"),
            html.P(f"Distance: {station['distance_km']:.1f} km | Elevation: {station['height']:.0f} m")
        ])
    
    return html.Div([
        html.H4("📍 Selected Location"),
        html.P(f"Lat: {lat:.3f}°N, Lon: {lon:.3f}°E")
    ])

@app.callback(
    [Output('ssi-chart', 'figure'),
     Output('weather-chart', 'figure')],
    [Input('selected-location', 'data'),
     Input('refresh-btn', 'n_clicks'),
     Input('time-range', 'value')]
)
def update_charts(location, n_clicks, hours):
    """Update weather charts"""
    
    lat, lon = location['lat'], location['lon']
    station = data_fetcher.find_nearest_station(lat, lon)
    
    if not station:
        empty_fig = go.Figure()
        return empty_fig, empty_fig
    
    # Generate weather data
    weather_data = data_fetcher.generate_weather_data(
        station['station_id'], 
        int(hours)
    )
    
    # Calculate SSI
    ssi_data = weather_analyzer.calculate_ssi(weather_data)
    
    # SSI Chart
    ssi_fig = go.Figure()
    ssi_fig.add_trace(go.Scatter(
        x=ssi_data['datetime'],
        y=ssi_data['SSI'],
        mode='lines',
        line=dict(width=3, color='#3498db'),
        fill='tozeroy',
        fillcolor='rgba(52, 152, 219, 0.2)',
        name='SSI'
    ))
    
    ssi_fig.add_hline(y=70, line_dash="dash", line_color="green", 
                     annotation_text="Good")
    ssi_fig.add_hline(y=40, line_dash="dash", line_color="orange", 
                     annotation_text="Moderate")
    
    ssi_fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Survey Suitability Index",
        yaxis=dict(range=[0, 100]),
        margin=dict(l=40, r=20, t=20, b=40),
        hovermode='x unified'
    )
    
    # Weather Parameters Chart
    weather_fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Temperature (°C)', 'Wind Speed (m/s)',
                       'Precipitation (mm/h)', 'Sunshine (min/h)'),
        vertical_spacing=0.15
    )
    
    # Temperature
    weather_fig.add_trace(
        go.Scatter(x=weather_data['temperature']['datetime'],
                  y=weather_data['temperature']['temperature_c'],
                  mode='lines', line=dict(color='red'), name='Temp'),
        row=1, col=1
    )
    
    # Wind
    weather_fig.add_trace(
        go.Scatter(x=weather_data['wind']['datetime'],
                  y=weather_data['wind']['wind_speed_ms'],
                  mode='lines', line=dict(color='green'), name='Wind'),
        row=1, col=2
    )
    
    # Precipitation
    weather_fig.add_trace(
        go.Bar(x=weather_data['precipitation']['datetime'],
              y=weather_data['precipitation']['precipitation_mm'],
              marker_color='blue', name='Rain'),
        row=2, col=1
    )
    
    # Sunshine
    weather_fig.add_trace(
        go.Bar(x=weather_data['sunshine']['datetime'],
              y=weather_data['sunshine']['sunshine_minutes'],
              marker_color='gold', name='Sun'),
        row=2, col=2
    )
    
    weather_fig.update_layout(
        showlegend=False,
        height=400,
        margin=dict(l=40, r=20, t=40, b=40)
    )
    
    return ssi_fig, weather_fig

if __name__ == '__main__':
    # For local testing
    app.run_server(debug=False, host='0.0.0.0', port=port)
