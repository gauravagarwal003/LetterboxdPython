import pandas as pd
import getDisplayName

df = pd.read_csv('movies.csv')
df_copy = df.copy()

filterCol = 'cast'
avgCol = 'avgRating'
topBottomNum = 5
minMovies = 15

if df.at[0, filterCol].startswith("[") and df.at[0, filterCol].endswith("]"):
    df_copy[filterCol] = df_copy[filterCol].apply(eval)  
    df_exploded = df_copy.explode(filterCol)
    movie_counts = df_exploded[filterCol].value_counts()
    valid_genres = movie_counts[movie_counts >= minMovies].index
    df_filtered = df_exploded[df_exploded[filterCol].isin(valid_genres)]
    average_ratings = df_filtered.groupby(filterCol)[avgCol].mean()
    sorted_ratings = average_ratings.sort_values(ascending=False)
    top = sorted_ratings.head(topBottomNum)
    bottom = sorted_ratings.tail(topBottomNum)
    
else:
    average_ratings = df.groupby(filterCol)[avgCol].agg(['mean', 'count'])
    valid_genres = average_ratings[average_ratings['count'] >= minMovies].index
    df_filtered = df[df[filterCol].isin(valid_genres)]
    average_ratings_filtered = df_filtered.groupby(filterCol)[avgCol].mean()
    sorted_ratings = average_ratings_filtered.sort_values(ascending=False)
    top = sorted_ratings.head(topBottomNum)
    bottom = sorted_ratings.tail(topBottomNum)


print()
print(f"{topBottomNum} highest rated movies by {filterCol} with at least {minMovies} movies:")
for name, rating in zip(top.index, top.values):
    print(f"{getDisplayName.getDisplayName(name)} with a {avgCol} of {round(rating,3)}")

print()
print(f"{topBottomNum} lowest rated movies by {filterCol} with at least {minMovies} movies:")
for name, rating in zip(bottom.index, bottom.values):
    print(f"{getDisplayName.getDisplayName(name)} with a {avgCol} of {round(rating,3)}")
