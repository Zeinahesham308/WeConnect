from colorama import Fore, Style, init

# Initialize colorama
init()

def print_colored(message, color=Fore.WHITE, style=Style.RESET_ALL):
    print(f"{color}{style}{message}{Style.RESET_ALL}")

# Example usage
print_colored("Welcome to My CLI", Fore.CYAN, Style.BRIGHT)
print_colored("This is a message in bright cyan", Fore.GREEN)
print_colored("Another message in green")
print_colored("Error message!", Fore.RED, Style.BRIGHT)
