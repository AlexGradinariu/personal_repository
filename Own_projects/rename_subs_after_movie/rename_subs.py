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
    movies = {}
    subtitles = {}

    for file in os.listdir(path):
        if file.endswith((".mkv",".mp4")):
            movie_name = os.path.splitext(file)[0]
            movie_suffix = os.path.splitext(file)[1]
            movies[movie_name] = movie_suffix

        elif file.endswith((".sub",".srt")):
            subtitles_name = os.path.splitext(file)[0]
            subtitles_suffix = os.path.splitext(file)[1]
            subtitles[subtitles_name] = subtitles_suffix

    for movie, movies_suffix in movies.items():
        for sub, sub_suffix in subtitles.items():
            score = similarity(movie.lower(), sub.lower())
            if score >= 0.88:
                print("Subtitle: ", sub, "->-> to be renamed into ->->", movie+sub_suffix, score)
                sub_path = os.path.join(path, sub)+sub_suffix
                # os.rename(sub_path, os.path.join(path, movie)+sub_suffix)
            else:
                print("to big difference between: ",movie, "and: ", sub)

if __name__ == "__main__":
    renames_subs_after_movies(r".")