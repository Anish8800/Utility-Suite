# Utility Suite

![Python](https://img.shields.io/badge/python-3.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A modular collection of real-world tools built in **Python** and **C++**, designed for personal productivity, analytics, and geospatial intelligence.  
Each module is self-contained with its own README, dependencies, and documentation.

---

## 🧩 Modules

- **Expense Recording System**  
  Track, analyze, and report personal expenses with Excel integration and GUI support.

- **Leaderboard Ranking**  
  Dynamic score tracking and ranking system with CSV and image export capabilities.

- **Geofence Service**  
  Location-based alerts and zone monitoring using FastAPI, Shapely, and Pydantic.

---

## 📁 Folder Structure

```text
UTILITY-SUITE/
├── Expense_Recording_System/   # Personal expense tracker
├── Leaderboard_Ranking/        # Championship points ranking system
├── Geofence_Service/           # Vehicle geofence monitoring service
└── README.md                   # Root documentation
```

## 🚀 How to Use
Navigate into any module folder and follow its README instructions to set up and run the tool.

Example:
cd Geofence_Service
python -m venv .venv
.venv\Scripts\activate   # Windows
source .venv/bin/activate # Linux/Mac
pip install -r requirements.txt
python main.py 

## 🧪 Testing
Each module includes its own test suite. 
Run tests inside a module with:
pytest

## 🤝 Contributing
Contributions, issues, and feature requests are welcome! Feel free to open an issue or submit a pull request. For major changes, please open an issue first to discuss what you would like to change.

## 🧑‍💻 Author
Developed by **Anish Wadatkar**