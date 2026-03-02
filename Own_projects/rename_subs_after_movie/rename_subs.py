import os
from difflib import SequenceMatcher


def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()


def fuzzy_match(list1, list2, threshold=0.90):
    matches = []

    for item1 in list1:
        for item2 in list2:
            score = similarity(
                os.path.splitext(item1)[0].lower(),
                os.path.splitext(item2)[0].lower()
            )
            if score >= threshold:
                matches.append((item1, item2, round(score, 2)))
    return matches

def renames_subs_after_movies(path):
    path = os.path.abspath(path)
    movies = []
    subtitles = []

    for file in os.listdir(path):
        if file.endswith(".mkv"):
            movies.append(file)
        elif file.endswith(".srt"):
            subtitles.append(file)

    for movie in movies:
        movie_name = os.path.splitext(movie)[0]

        for sub in subtitles:
            sub_name = os.path.splitext(sub)[0]

            score = similarity(movie_name.lower(), sub_name.lower())

            if score >= 0.90:
                print(movie, "<->", sub, score)



if __name__ == "__main__":
    renames_subs_after_movies(r".")