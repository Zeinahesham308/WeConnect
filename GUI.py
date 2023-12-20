from colorama import Fore, Style, init

# Initialize colorama
init()

def print_colored(message, color=Fore.WHITE, style=Style.RESET_ALL):
    print(f"{style}{color}{message}{Style.RESET_ALL}", end='')

# Example usage

