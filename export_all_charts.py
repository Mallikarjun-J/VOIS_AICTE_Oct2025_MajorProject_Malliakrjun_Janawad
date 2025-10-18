"""
Export all 11 dashboard visualizations as PNG images for README
"""
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from src.analysis import (
    load_netflix_dataset, 
    clean_and_engineer, 
    explode_and_normalize_genres,
    ensure_reports_dir
)

# Create reports directory
reports_dir = ensure_reports_dir('reports')

# Load and prepare data
print("Loading dataset...")
df_raw = load_netflix_dataset(strict=True)
df = clean_and_engineer(df_raw)
print(f"Loaded {len(df)} titles")

# Set style
sns.set(style='whitegrid', context='notebook')
plt.rcParams['figure.figsize'] = (12, 6)

print("\nGenerating all 11 charts...")

# Chart 1: Movies vs TV Shows Distribution
print("1. Movies vs TV Shows Distribution...")
fig, ax = plt.subplots(figsize=(10, 6))
dist = df['type'].value_counts()
colors = sns.color_palette('Set2', n_colors=2)
dist.plot(kind='bar', color=colors, ax=ax)
ax.set_title('Movies vs TV Shows Distribution', fontsize=16, fontweight='bold')
ax.set_xlabel('Content Type', fontsize=12)
ax.set_ylabel('Count', fontsize=12)
ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
for i, v in enumerate(dist):
    ax.text(i, v + 50, str(v), ha='center', fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(reports_dir, 'chart1_movies_vs_tv.png'), dpi=150, bbox_inches='tight')
plt.close()

# Chart 2: Annual Additions by Type
print("2. Annual Additions by Type...")
df_year = df.dropna(subset=['year_added']).copy()
df_year['year_added'] = df_year['year_added'].astype(int)
annual = df_year.groupby(['year_added', 'type']).size().reset_index(name='count')
fig, ax = plt.subplots(figsize=(14, 6))
for content_type in annual['type'].unique():
    data = annual[annual['type'] == content_type]
    ax.plot(data['year_added'], data['count'], marker='o', linewidth=2, label=content_type)
ax.set_title('Annual Content Additions by Type', fontsize=16, fontweight='bold')
ax.set_xlabel('Year Added', fontsize=12)
ax.set_ylabel('Number of Titles', fontsize=12)
ax.legend(title='Type', fontsize=11)
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(reports_dir, 'chart2_annual_trends.png'), dpi=150, bbox_inches='tight')
plt.close()

# Chart 3: Top Genres
print("3. Top Genres...")
gdf = explode_and_normalize_genres(df)
top_genres = gdf['genre'].value_counts().head(15)
fig, ax = plt.subplots(figsize=(12, 8))
top_genres.sort_values().plot(kind='barh', color='steelblue', ax=ax)
ax.set_title('Top 15 Genres (Normalized)', fontsize=16, fontweight='bold')
ax.set_xlabel('Count', fontsize=12)
ax.set_ylabel('Genre', fontsize=12)
plt.tight_layout()
plt.savefig(os.path.join(reports_dir, 'chart3_top_genres.png'), dpi=150, bbox_inches='tight')
plt.close()

# Chart 4: Top Countries
print("4. Top Countries...")
countries = (df[['show_id', 'country']]
             .assign(country=lambda d: d['country'].str.split(','))
             .explode('country'))
countries['country'] = countries['country'].astype(str).str.strip()
top_countries = countries['country'].value_counts().head(20)
fig, ax = plt.subplots(figsize=(12, 8))
top_countries.sort_values().plot(kind='barh', color='coral', ax=ax)
ax.set_title('Top 20 Contributing Countries', fontsize=16, fontweight='bold')
ax.set_xlabel('Count', fontsize=12)
ax.set_ylabel('Country', fontsize=12)
plt.tight_layout()
plt.savefig(os.path.join(reports_dir, 'chart4_top_countries.png'), dpi=150, bbox_inches='tight')
plt.close()

# Chart 5: Content Rating Distribution
print("5. Content Rating Distribution...")
rating_counts = df['rating'].value_counts().head(10)
fig, ax = plt.subplots(figsize=(10, 6))
rating_counts.sort_values().plot(kind='barh', color='mediumseagreen', ax=ax)
ax.set_title('Top 10 Content Ratings', fontsize=16, fontweight='bold')
ax.set_xlabel('Count', fontsize=12)
ax.set_ylabel('Rating', fontsize=12)
plt.tight_layout()
plt.savefig(os.path.join(reports_dir, 'chart5_ratings.png'), dpi=150, bbox_inches='tight')
plt.close()

# Chart 6: Top Directors
print("6. Top Directors...")
directors = (df[['show_id', 'director']]
            .assign(director=lambda d: d['director'].str.split(','))
            .explode('director'))
directors['director'] = directors['director'].astype(str).str.strip()
directors = directors[directors['director'].notna() & 
                     (directors['director'] != 'Unknown') & 
                     (directors['director'] != 'nan')]
top_directors = directors['director'].value_counts().head(15)
fig, ax = plt.subplots(figsize=(12, 8))
top_directors.sort_values().plot(kind='barh', color='darkseagreen', ax=ax)
ax.set_title('Top 15 Most Prolific Directors', fontsize=16, fontweight='bold')
ax.set_xlabel('Number of Titles', fontsize=12)
ax.set_ylabel('Director', fontsize=12)
plt.tight_layout()
plt.savefig(os.path.join(reports_dir, 'chart6_top_directors.png'), dpi=150, bbox_inches='tight')
plt.close()

# Chart 7: Movie Duration Distribution
print("7. Movie Duration Distribution...")
movies_only = df[df['type'] == 'Movie'].copy()
movies_only['duration_min'] = movies_only['duration'].astype(str).str.extract(r'(\d+)').astype(float)
movies_only = movies_only.dropna(subset=['duration_min'])
fig, ax = plt.subplots(figsize=(12, 6))
ax.hist(movies_only['duration_min'], bins=30, edgecolor='black', alpha=0.7, color='steelblue')
ax.axvline(movies_only['duration_min'].mean(), color='red', linestyle='--', 
            linewidth=2, label=f"Mean: {movies_only['duration_min'].mean():.1f} min")
ax.axvline(movies_only['duration_min'].median(), color='green', linestyle='--', 
            linewidth=2, label=f"Median: {movies_only['duration_min'].median():.1f} min")
ax.set_title('Movie Duration Distribution', fontsize=16, fontweight='bold')
ax.set_xlabel('Duration (minutes)', fontsize=12)
ax.set_ylabel('Number of Movies', fontsize=12)
ax.legend(fontsize=11)
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(reports_dir, 'chart7_movie_duration.png'), dpi=150, bbox_inches='tight')
plt.close()

# Chart 8: TV Show Seasons Distribution
print("8. TV Show Seasons Distribution...")
tv_only = df[df['type'] == 'TV Show'].copy()
tv_only['seasons'] = tv_only['duration'].astype(str).str.extract(r'(\d+)').astype(float)
tv_only = tv_only.dropna(subset=['seasons'])
season_counts = tv_only['seasons'].value_counts().sort_index().head(10)
fig, ax = plt.subplots(figsize=(10, 6))
season_counts.plot(kind='bar', color='indianred', ax=ax)
ax.set_title('TV Shows by Number of Seasons', fontsize=16, fontweight='bold')
ax.set_xlabel('Number of Seasons', fontsize=12)
ax.set_ylabel('Number of Shows', fontsize=12)
ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
plt.tight_layout()
plt.savefig(os.path.join(reports_dir, 'chart8_tv_seasons.png'), dpi=150, bbox_inches='tight')
plt.close()

# Chart 9: Genre Trends Over Time
print("9. Genre Trends Over Time...")
gdf_time = explode_and_normalize_genres(df)
gdf_time = gdf_time.dropna(subset=['year_added'])
top5_genres = gdf_time['genre'].value_counts().head(5).index.tolist()
gdf_top5 = gdf_time[gdf_time['genre'].isin(top5_genres)]
genre_year = gdf_top5.groupby(['year_added', 'genre']).size().reset_index(name='count')
fig, ax = plt.subplots(figsize=(14, 7))
for genre in top5_genres:
    genre_data = genre_year[genre_year['genre'] == genre]
    ax.plot(genre_data['year_added'], genre_data['count'], 
            marker='o', linewidth=2, label=genre)
ax.set_title('Top 5 Genre Evolution Over Time', fontsize=16, fontweight='bold')
ax.set_xlabel('Year Added', fontsize=12)
ax.set_ylabel('Number of Titles', fontsize=12)
ax.legend(title='Genre', fontsize=11, loc='best')
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(reports_dir, 'chart9_genre_trends.png'), dpi=150, bbox_inches='tight')
plt.close()

# Chart 10: Monthly Addition Patterns
print("10. Monthly Seasonality Patterns...")
df_with_dates = df.dropna(subset=['date_added']).copy()
df_with_dates['month'] = pd.to_datetime(df_with_dates['date_added'], errors='coerce').dt.month_name()
month_order = ['January', 'February', 'March', 'April', 'May', 'June',
              'July', 'August', 'September', 'October', 'November', 'December']
month_counts = df_with_dates['month'].value_counts().reindex(month_order)
fig, ax = plt.subplots(figsize=(14, 6))
month_counts.plot(kind='bar', color='mediumorchid', ax=ax)
ax.set_title('Content Additions by Month (Seasonality)', fontsize=16, fontweight='bold')
ax.set_xlabel('Month', fontsize=12)
ax.set_ylabel('Number of Titles Added', fontsize=12)
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(reports_dir, 'chart10_seasonality.png'), dpi=150, bbox_inches='tight')
plt.close()

# Chart 11: Content Type by Rating
print("11. Content Type by Rating (Bonus)...")
rating_type = df.groupby(['rating', 'type']).size().unstack(fill_value=0)
top_ratings = df['rating'].value_counts().head(8).index
rating_type_top = rating_type.loc[top_ratings]
fig, ax = plt.subplots(figsize=(12, 6))
rating_type_top.plot(kind='bar', stacked=False, ax=ax, color=['steelblue', 'coral'])
ax.set_title('Content Type Distribution by Rating', fontsize=16, fontweight='bold')
ax.set_xlabel('Rating', fontsize=12)
ax.set_ylabel('Count', fontsize=12)
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
ax.legend(title='Type', fontsize=11)
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(reports_dir, 'chart11_rating_by_type.png'), dpi=150, bbox_inches='tight')
plt.close()

print("\n✅ All 11 charts exported successfully!")
print(f"📁 Location: {reports_dir}/")
print("\nGenerated files:")
for i in range(1, 12):
    print(f"  - chart{i}_*.png")
