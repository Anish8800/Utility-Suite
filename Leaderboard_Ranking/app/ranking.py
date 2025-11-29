import numpy as np

def rank_players(players):
    # Step 1: sort by total points (descending)
    players.sort(key=lambda p: p.total_points, reverse=True)

    # Step 2: resolve ties by spending (ascending)
    i = 0
    while i < len(players)-1:
        j = i+1
        while j < len(players) and players[j].total_points == players[i].total_points:
            j += 1
        if j-i > 1:
            tied = players[i:j]
            tied.sort(key=lambda p: p.total_spent)
            # Step 3: countback system
            tied = sorted(tied, key=lambda p: countback_key(p), reverse=True)
            # Step 4: alphabetical if still tied
            tied.sort(key=lambda p: p.name)
            players[i:j] = tied
        i = j
    return players

def countback_key(player):
    # Highest scores first, then frequency of those scores
    scores = sorted(player.points, reverse=True)
    return tuple(scores)