import itertools
import hashlib
import string
def create_hash_for_password(password):
    sha256_hash = hashlib.sha256(password.encode()).hexdigest()
    with open(file,'w',encoding='utf8') as hashed_password:
        hashed_password.write(sha256_hash)
    print(f'SHA-256 Hash: {sha256_hash}')

def read_hash_password(file):
    with open(file, 'r', encoding='utf8') as hashed_password:
        lines = hashed_password.readlines()
        for line in lines:
            return line

def brute_force_hash(target_hash, max_length=4):
    characters = string.ascii_lowercase + string.digits # practic pune toate literele si cifrele pentru a crea o instanta din care sa aleaga
    # Attempt all combinations of characters up to the maximum length
    for length in range(1, max_length + 1):
        for guess in itertools.product(characters, repeat=length):# creaza o tupla de n,ex 5 caractere care incepe cu (a,a,a,a,a) apoi (a,a,a,a,b) etc
            # Convert the tuple from itertools.product to a string
            guess = ''.join(guess) # din tupla de mai sus ,le face join , ex aaaaa,aaaaab,aaaaac
            # Hash the guess using SHA-256
            guess_hash = hashlib.sha256(guess.encode()).hexdigest()
            # Check if the hashed guess matches the target hash
            if guess_hash == target_hash:
                return guess  # Password found
    return None  # Password not found within the given constraints
if __name__ == '__main__':
    file = './hashed.txt'
    create_hash_for_password('alexca')
    founded_hash = brute_force_hash(read_hash_password(file),max_length=6)
    if founded_hash:
        print(f'Found founded hash {founded_hash}')
    else:
        print('No founded hash')