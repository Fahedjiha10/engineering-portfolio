import random
import string
from pathlib import Path

MAX_GUESSES = 6
WORDS_FILE = Path(__file__).with_name('words.txt')


def load_words(file_path: Path):
    """Load candidate words from words.txt and keep alphabetic words only."""
    if not file_path.exists():
        raise FileNotFoundError(f"Could not find {file_path.name}. Put words.txt in the same folder as hangman.py.")

    words = file_path.read_text(encoding="utf-8").split()
    clean_words = [word.lower() for word in words if word.isalpha()]

    if not clean_words:
        raise ValueError("words.txt does not contain any valid words.")

    return clean_words


def choose_secret_word():
    words = load_words(WORDS_FILE)
    return random.choice(words)


def get_display_word(secret_word, letters_guessed):
    return " ".join(letter if letter in letters_guessed else "_" for letter in secret_word)


def get_unique_letters(secret_word):
    return set(secret_word)


def is_word_guessed(secret_word, letters_guessed):
    return get_unique_letters(secret_word).issubset(set(letters_guessed))


def get_valid_guess(letters_guessed):
    while True:
        guess = input("Guess a letter: ").strip().lower()

        if len(guess) != 1 or guess not in string.ascii_lowercase:
            print("Please enter one letter from a to z.")
            continue

        if guess in letters_guessed:
            print("You already guessed that letter. Try again.")
            continue

        return guess


def main():
    # Game state variables
    secret_word = choose_secret_word()
    letters_guessed = []
    mistakes_made = 0

    print("Welcome to Hangman")
    print(f"You have {MAX_GUESSES} wrong guesses available.")

    while mistakes_made < MAX_GUESSES and not is_word_guessed(secret_word, letters_guessed):
        print("\nWord:", get_display_word(secret_word, letters_guessed))
        print("Letters guessed:", " ".join(letters_guessed) if letters_guessed else "None")
        print("Mistakes made:", mistakes_made)
        print("Guesses left:", MAX_GUESSES - mistakes_made)

        guess = get_valid_guess(letters_guessed)
        letters_guessed.append(guess)

        if guess in secret_word:
            print("Correct.")
        else:
            mistakes_made += 1
            print("Wrong guess.")

    print("\nFinal word:", " ".join(secret_word))

    if is_word_guessed(secret_word, letters_guessed):
        print("You win.")
    else:
        print("You lose.")


if __name__ == "__main__":
    main()
