import bcrypt

def generate_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

password = "admin123"  # Change this to your desired password
hashed_password = generate_hash(password)
print(f"Hashed password for '{password}':")
print(hashed_password)
