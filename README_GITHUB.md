# 🌤️ DWD Weather Dashboard

[![Deploy on Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

Interactive weather dashboard for survey planning with real-time weather visualization and Survey Suitability Index (SSI) calculations.

## 🚀 Live Demo

**[View Live Dashboard](https://dwd-weather-dashboard.onrender.com)** *(may take 30s to wake up on free tier)*

## ✨ Features

- 🗺️ **Interactive Map** - Click to select any location
- 📊 **Survey Suitability Index** - AI-calculated optimal survey windows  
- 🌡️ **Multi-Parameter Analysis** - Temperature, wind, rain, sunshine
- 📈 **Real-time Visualization** - Interactive Plotly charts
- 🌊 **Marine Mode** - Specialized calculations for coastal operations
- 📱 **Responsive Design** - Works on desktop and mobile

## 🖼️ Screenshots

![Dashboard Preview](https://via.placeholder.com/800x400?text=DWD+Weather+Dashboard)

## 🏃 Quick Start

### Run Locally
```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/dwd-weather-dashboard.git
cd dwd-weather-dashboard

# Install dependencies
pip install -r requirements_prod.txt

# Run application
python app.py

# Open http://localhost:8050
```

### Deploy to Cloud (Free)

#### Option 1: Render (Recommended)
1. Fork this repository
2. Sign up at [render.com](https://render.com)
3. Click "New" → "Web Service"
4. Connect your GitHub repo
5. Deploy with these settings:
   - **Build**: `pip install -r requirements_prod.txt`
   - **Start**: `gunicorn app:server --bind 0.0.0.0:$PORT`

#### Option 2: Railway
1. Click [![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template)
2. Connect GitHub
3. Deploy automatically

#### Option 3: One-Click Deploy
- **Render**: [![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)
- **Heroku**: [![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

## 📋 Requirements

- Python 3.8+
- 512MB RAM minimum
- No database required

## 🛠️ Tech Stack

- **Framework**: Plotly Dash
- **Data**: DWD Open Data API
- **Maps**: OpenStreetMap
- **Hosting**: Render/Railway (free tier)

## 📊 Survey Suitability Index (SSI)

The SSI combines multiple weather factors:

| Factor | Weight | Optimal Range |
|--------|--------|---------------|
| Precipitation | 35% | 0 mm/h |
| Wind Speed | 30% | 0-5 m/s |
| Temperature | 15% | 15-25°C |
| Sunshine | 10% | 60 min/h |
| Cloud Cover | 10% | 0-2 oktas |

**SSI Categories:**
- 🟢 **Good** (70-100): Excellent conditions
- 🟡 **Moderate** (40-70): Proceed with caution
- 🔴 **Poor** (0-40): Not recommended

## 🌍 Environment Variables

```bash
DEFAULT_LAT=53.55    # Default latitude (Hamburg)
DEFAULT_LON=9.99     # Default longitude
PORT=8050           # Server port
```

## 📁 Project Structure

```
dwd-weather-dashboard/
├── app.py                 # Main application
├── requirements_prod.txt  # Python dependencies
├── Procfile              # Deployment config
├── render.yaml           # Render config
└── README.md             # This file
```

## 🤝 Contributing

Contributions welcome! Please feel free to submit a Pull Request.

## 📝 License

MIT License - Use freely for any purpose

## 🙏 Acknowledgments

- [Deutscher Wetterdienst](https://www.dwd.de) for weather data
- [Plotly Dash](https://plotly.com/dash/) for visualization framework
- Hamburg coastal region as default location

## 🔗 Links

- [Full Documentation](DEPLOY_GUIDE.md)
- [DWD Open Data](https://opendata.dwd.de)
- [Report Issues](https://github.com/YOUR_USERNAME/dwd-weather-dashboard/issues)

---

**Made with ❤️ for survey planning** | [Live Demo](https://dwd-weather-dashboard.onrender.com)
