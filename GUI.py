from colorama import Fore, Style, init
import re

# Initialize colorama
init()


bold_pattern = r'\*\*(?=[^\s\*])(.*?)([^\s\*])\*\*'
italic_pattern = r'(?<!\S)_(?=\S)(.*?)(?<=\S)_(?!\S)'


def print_colored(message, color=Fore.WHITE, style=Style.RESET_ALL):
    print(f"{style}{color}{message}{Style.RESET_ALL}", end='')


def send_message_bold(message):
    # Use re.sub to replace bold matches with formatted text
    formatted_message = re.sub(bold_pattern, r"\033[1m\1\2\033[0m", message)
    return formatted_message


def send_message_Italic(message):
    formatted_message = re.sub(italic_pattern, r"\033[3m\1\033[0m", message)
    return formatted_message

# Example usage