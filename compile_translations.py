from babel.messages.frontend import CommandLineInterface
import sys
import os

if __name__ == "__main__":
    # Ensure we are in the project root
    print(f"Current directory: {os.getcwd()}")
    cli = CommandLineInterface()
    cli.run(['pybabel', 'compile', '-d', 'app/translations'])
    print("Translations compiled successfully!")
