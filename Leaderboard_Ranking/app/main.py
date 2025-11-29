import pandas as pd
from .utils import normalize_score, normalize_spending
from .models import Player
from .ranking import rank_players

def load_data():
    df_points = pd.read_excel("data/leaderboard.xlsx", sheet_name=0)
    df_spending = pd.read_excel("data/leaderboard.xlsx", sheet_name=1)

    players = []
    for _, row in df_points.iterrows():
        name = row["Player"]
        points = [normalize_score(v) for v in row[["R01","R02","R03","R04","R05","R06","R07","R08","R09","R10","R11","R12","R13","R14","R15","R16","R17","R18","R19","R20","R21","R22","R23","R24"]].tolist()]
        spend_row = df_spending[df_spending["Player"] == name].iloc[0]
        spending = [normalize_spending(v) for v in spend_row.drop(["Player","Spent ($m)","Budget ($m)","Bal ($m)"]).tolist()]
        players.append(Player(name, points, spending))
    return players

def main():
    players = load_data()
    ranked = rank_players(players)
    print("Final Leaderboard:")
    for pos, p in enumerate(ranked, start=1):
        print(f"{pos}. {p.name} - {p.total_points} pts, Spent ${p.total_spent:.2f}")

if __name__ == "__main__":
    main()