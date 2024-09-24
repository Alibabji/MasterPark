file_path = 'league_users.txt'

# Function to save user data
def save_user(discord_id, nickname):
    with open(file_path, 'a') as f:
        f.write(f"{discord_id}:{nickname}\n")

# Function to retrieve user data
def get_user(discord_id):
    try:
        with open(file_path, 'r') as f:
            for line in f:
                stored_id, stored_nickname = line.strip().split(":")
                if str(discord_id) == stored_id:
                    return stored_nickname
        return None
    except FileNotFoundError:
        return None
