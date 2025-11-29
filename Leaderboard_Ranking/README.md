#Leaderboard Points Ranking Service

![Python](https://img.shields.io/badge/python-3.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)

📖 Overview
This project processes the provided leaderboard.xlsx file to generate a ranked leaderboard for a championship series.
Players are ranked based on total points, with tiebreakers applied in order: spending, countback system, and finally alphabetical order.
The service demonstrates clean code structure, thoughtful decision-making, and operational awareness.

## 📦 Installation & Usage

### Prerequisites
- Python 3.11+

### Setup
```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
source .venv/bin/activate # Linux/Mac
bash run.sh
```

## 🧩 Ranking Criteria
- Total Points
- Highest total points ranks higher.
- Cells with D$Q or – are treated as zero.
- Spending (Asc)
- Among tied players, lower total spending ranks higher.
- Countback System
- Compare highest single-event scores among tied players.
- If still tied, compare frequency of those highest scores.
- Continue with second-highest, third-highest, etc.
- Alphabetical Order
- If still tied, players are sorted alphabetically and highlighted in red.

## 🔧 Further Tiebreaker Rationale
If all existing tiebreakers fail, a consistency metric may be applied:
- Average points per event (higher average ranks higher).
- Lowest variance in scores (more stable performance ranks higher).
- Most events participated in (rewarding steady contribution).
This ensures players who demonstrate reliability across the series are rewarded fairly.

## 📊 Sample Output (Top 5 Players)
Final Leaderboard:
1. Cocoa Pops - 1001 pts, Spent $139.27
2. Team Overbudget - 1080 pts, Spent $132.00
3. GSR Racing - 1060 pts, Spent $135.32
4. Wu Racing - 1029 pts, Spent $138.03
5. PetricaF1 - 921 pts, Spent $141.31

## 📈 Visual Output
Below is a bar chart of the Top 10 Players by Points.
The leader (Cocoa Pops) is highlighted in orange.
Top 10 Players by Points


![alt text](<Generated Image.png>)

## 📝 Assumptions
• 	 and  are treated as zero points/spending.
• 	Spending values are cumulative across events.
• 	Players may belong to multiple tied groups; rules apply recursively.
• 	Alphabetical sorting is case-insensitive.

## 🚀 Improvements with More Time
• 	Add unit tests for ranking logic and edge cases.
• 	Export results to CSV/Excel for easier sharing.
• 	Build a web API (FastAPI) to query rankings dynamically.
• 	Add visual dashboards (matplotlib/plotly) for interactive analysis.
• 	Integrate logging and monitoring for operational awareness.

## 📜 Dependencies

```pandas==2.2.2
openpyxl==3.1.2
matplotlib==3.9.2
pillow==10.4.0
```
## 📁 Project Structure

Leaderboard_Ranking/
├── .venv/                  # Virtual environment (ignored via .gitignore)
├── app/                    # Core application logic
│   ├── main.py             # Entry point for CLI or service
│   ├── models.py           # Data models and schema definitions
│   ├── ranking.py          # Ranking logic and tiebreaker implementation
│   ├── utils.py            # Helper functions (e.g., formatting, sorting)
├── Generated Image.png     # Visual output of leaderboard (bar chart)
├── requirements.txt        # Python dependencies
├── run.sh                  # Shell script to install and execute
└── README.md               # Project documentation

## 🧪 Testing

Tests are located in the `tests/` directory and cover ranking logic, export functions, and input validation.

```bash
pytest
```

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!  
Feel free to open an issue or submit a pull request.  
For major changes, please open an issue first to discuss what you would like to change.

## 🧑‍💻 Author

Developed by **Anish Wadatkar**

## 📜 License

This repository is licensed under the MIT License.
