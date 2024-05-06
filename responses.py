import random

def get_response(message: str) -> str:
    processed_message = message.lower()

    if processed_message == 'hello':
        return 'Ahoy there!'
    
    if message == 'roll':
        return str(random.randint(1, 6))
    
    if processed_message == '!help':
        return '`This is a help message that you can modify.`'
    
    return 'I didn\'t understand your message. Try typing "!help".'