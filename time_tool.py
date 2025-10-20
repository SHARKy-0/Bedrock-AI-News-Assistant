from datetime import datetime

def get_current_time():
    now = datetime.utcnow().astimezone()
    return now.strftime("%Y-%m-%d %H:%M:%S %Z")