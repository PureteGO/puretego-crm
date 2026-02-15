from babel.messages.frontend import CommandLineInterface

print("Extracting messages...")
CommandLineInterface().run(['pybabel', 'extract', '-F', 'babel.cfg', '-k', '_', '-k', '_l', '-k', 'gettext', '-o', 'messages.pot', '.'])

print("Updating catalogs...")
CommandLineInterface().run(['pybabel', 'update', '-i', 'messages.pot', '-d', 'app/translations'])

print("Compiling catalogs...")
CommandLineInterface().run(['pybabel', 'compile', '-d', 'app/translations'])
