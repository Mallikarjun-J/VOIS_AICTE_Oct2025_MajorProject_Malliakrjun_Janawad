import os
import io
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict

import pandas as pd
import numpy as np


@dataclass
class AnalysisData:
    df: pd.DataFrame
    df_year: pd.DataFrame
    annual: pd.DataFrame
    top_genres: pd.Series
    genre_year: pd.DataFrame
    top_countries: pd.Series


def load_netflix_dataset(path: Optional[str] = None, strict: bool = False) -> pd.DataFrame:
    """Load dataset from optional path, auto-detect common filenames, or use fallbacks.

    When strict=True, DO NOT use sample or online mirrors—only local files are allowed.

    Search order (local):
    1) Provided path (if exists)
    2) Common names in project root and CWD: 'Netflix Dataset.csv', 'netflix_titles.csv', 'netflix_dataset.csv', 'Netflix_Dataset.csv'
    3) Any CSV in those folders containing 'netflix' in the filename (case-insensitive)
    If strict=False only, then:
    4) Local sample: 'netflix_titles_sample.csv'
    5) Public mirrors (GitHub raw)
    """
    project_root = os.path.abspath(os.path.dirname(path)) if path else os.getcwd()
    cwd = os.getcwd()

    candidates: List[str] = []
    if path:
        candidates.append(path)

    common_names = [
        'Netflix Dataset.csv',
        'netflix_titles.csv',
        'netflix_dataset.csv',
        'Netflix_Dataset.csv',
    ]
    for root in {project_root, cwd}:
        for name in common_names:
            candidates.append(os.path.join(root, name))

    for root in {project_root, cwd}:
        try:
            for f in os.listdir(root):
                if f.lower().endswith('.csv') and 'netflix' in f.lower():
                    candidates.append(os.path.join(root, f))
        except Exception:
            pass

    seen: set = set()
    unique_candidates = [c for c in candidates if not (c in seen or seen.add(c))]

    for c in unique_candidates:
        if os.path.exists(c):
            try:
                return pd.read_csv(c)
            except Exception:
                continue

    if strict:
        raise FileNotFoundError("Strict mode: dataset not found locally. Place 'Netflix Dataset.csv' (or a CSV with 'netflix' in the name) in the project folder.")

    # Non-strict fallbacks
    sample = os.path.join(project_root, 'netflix_titles_sample.csv')
    if os.path.exists(sample):
        return pd.read_csv(sample)

    import requests
    mirrors = [
        'https://raw.githubusercontent.com/erikgregorywebb/Netflix-Data-Visualization/master/netflix_titles.csv',
        'https://raw.githubusercontent.com/abhi9146/datasets/master/netflix_titles.csv'
    ]
    for url in mirrors:
        try:
            r = requests.get(url, timeout=20)
            if r.ok and len(r.text) > 1000:
                return pd.read_csv(io.StringIO(r.text))
        except Exception:
            pass

    raise FileNotFoundError("Dataset not found. Place 'Netflix Dataset.csv' or 'netflix_titles.csv' in the project folder.")


def _first_existing(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    for c in candidates:
        if c in df.columns:
            return c
    return None

def _canonical_genre(label: str) -> Optional[str]:
    """Map raw Netflix genre labels to canonical categories. Return None to drop meta-buckets."""
    if not isinstance(label, str):
        return None
    s = label.strip()
    if not s:
        return None
    lower = s.lower()
    # Drop meta buckets that are not true genres
    if lower in {"movies", "tv shows", "tv show", "movie"}:
        return None

    # Canonical mapping (common Netflix categories and synonyms)
    mapping = {
        # Core genres
        "action & adventure": "Action & Adventure",
        "action": "Action & Adventure",
        "adventure": "Action & Adventure",
        "anime series": "Anime",
        "anime features": "Anime",
        "anime": "Anime",
        "british tv shows": "British",
        "children & family movies": "Kids & Family",
        "kids' tv": "Kids & Family",
        "kids & family": "Kids & Family",
        "comedies": "Comedies",
        "tv comedies": "Comedies",
        "stand-up comedy": "Comedies",
        "docuseries": "Documentary",
        "documentaries": "Documentary",
        "dramas": "Dramas",
        "tv dramas": "Dramas",
        "fantasy": "Sci-Fi & Fantasy",
        "sci-fi & fantasy": "Sci-Fi & Fantasy",
        "science fiction": "Sci-Fi & Fantasy",
        "horror": "Horror",
        "horror movies": "Horror",
        "independent movies": "Independent",
        "international tv shows": "International",
        "international movies": "International",
        "international": "International",
        "korean tv shows": "Korean",
        "k-dramas": "Korean",
        "music & musicals": "Music",
        "music": "Music",
        "mysteries": "Mystery",
        "crime tv shows": "Crime",
        "crime movies": "Crime",
        "reality tv": "Reality",
        "romance": "Romance",
        "romantic movies": "Romance",
        "romantic tv shows": "Romance",
        "science & nature tv": "Science & Nature",
        "sports movies": "Sports",
        "thrillers": "Thriller",
        "tv thrillers": "Thriller",
        "spanish-language tv shows": "Spanish-Language",
        "spanish-language movies": "Spanish-Language",
        "faith & spirituality": "Faith & Spirituality",
        "cult movies": "Cult",
    }

    # Exact match
    if lower in mapping:
        return mapping[lower]

    # Keep original label with titlecase if no mapping rule applies
    return s

def explode_and_normalize_genres(df: pd.DataFrame) -> pd.DataFrame:
    """Return DataFrame with columns [show_id, genre, year_added] after splitting and normalizing genres."""
    temp = (
        df[["show_id", "listed_in", "year_added"]]
        .assign(listed_in=lambda d: d["listed_in"].astype(str).str.split(","))
        .explode("listed_in")
    )
    temp["genre"] = temp["listed_in"].astype(str).str.strip().map(_canonical_genre)
    temp = temp.drop(columns=["listed_in"]) 
    temp = temp.dropna(subset=["genre"]).copy()
    return temp


def clean_and_engineer(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw.copy()
    # Standardize column names to snake_case lower
    df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]

    # Map flexible columns
    col_title = _first_existing(df, ['title', 'name'])
    # Check for Category first (if both Category and Type exist, Category is the content type)
    col_type = _first_existing(df, ['category', 'type', 'content_type'])
    col_date_added = _first_existing(df, ['date_added', 'dateadded', 'added_date', 'date_added_to_netflix', 'release_date'])
    col_release_year = _first_existing(df, ['release_year', 'year', 'year_released', 'releaseyear'])
    col_country = _first_existing(df, ['country', 'countries'])
    # If both Category and Type exist, Type column contains genres
    if 'category' in df.columns and 'type' in df.columns:
        col_listed_in = 'type'  # Type column has genres when Category exists
    else:
        col_listed_in = _first_existing(df, ['listed_in', 'genres', 'genre', 'categories', 'type'])
    col_duration = _first_existing(df, ['duration', 'runtime', 'duration_min'])
    col_rating = _first_existing(df, ['rating', 'age_rating', 'content_rating'])
    col_cast = _first_existing(df, ['cast', 'actors', 'starring'])
    col_director = _first_existing(df, ['director', 'directors'])
    col_show_id = _first_existing(df, ['show_id', 'id'])

    # Ensure core columns exist
    if col_show_id is None:
        df['show_id'] = [f's{i+1}' for i in range(len(df))]
        col_show_id = 'show_id'
    if col_title is None:
        df['title'] = 'Unknown'
        col_title = 'title'
    if col_type is None:
        df['type'] = 'Unknown'
        col_type = 'type'
    if col_country is None:
        df['country'] = 'Unknown'
        col_country = 'country'
    if col_listed_in is None:
        df['listed_in'] = 'Unknown'
        col_listed_in = 'listed_in'
    if col_duration is None:
        df['duration'] = 'Unknown'
        col_duration = 'duration'
    if col_rating is None:
        df['rating'] = 'Unknown'
        col_rating = 'rating'
    if col_cast is None:
        df['cast'] = 'Unknown'
        col_cast = 'cast'
    if col_director is None:
        df['director'] = 'Unknown'
        col_director = 'director'

    # Normalize fields to canonical names
    out = pd.DataFrame({
        'show_id': df[col_show_id],
        'title': df[col_title],
        'type': df[col_type],
        'country': df[col_country],
        'listed_in': df[col_listed_in],
        'rating': df[col_rating],
        'duration': df[col_duration],
        'cast': df[col_cast],
        'director': df[col_director],
    })

    # Add date_added and release_year if available
    if col_date_added is not None:
        out['date_added'] = pd.to_datetime(df[col_date_added], errors='coerce')
    else:
        out['date_added'] = pd.NaT

    if col_release_year is not None:
        out['release_year'] = pd.to_numeric(df[col_release_year], errors='coerce')
    else:
        out['release_year'] = np.nan

    # Derive year_added: prefer date_added year, else release_year
    out['year_added'] = out['date_added'].dt.year
    mask_missing_year = out['year_added'].isna() & out['release_year'].notna()
    out.loc[mask_missing_year, 'year_added'] = out.loc[mask_missing_year, 'release_year']

    # Month for seasonality analysis (optional)
    out['month_added'] = out['date_added'].dt.month

    # Fill textual NaNs
    for c in ['country', 'cast', 'director', 'listed_in', 'rating', 'duration', 'type', 'title']:
        out[c] = out[c].fillna('Unknown')

    # Primary country (first listed)
    out['primary_country'] = out['country'].apply(lambda x: x.split(',')[0].strip() if isinstance(x, str) else 'Unknown')

    # Parse duration
    def parse_duration(x):
        if not isinstance(x, str) or x == 'Unknown':
            return np.nan, 'Unknown'
        parts = x.split()
        # Handle formats like "90 min", "2 Seasons", "1 Season"
        try:
            val = int(parts[0])
        except Exception:
            val = np.nan
        unit = parts[1] if len(parts) > 1 else 'Unknown'
        return val, unit

    dur = out['duration'].apply(parse_duration)
    out['duration_int'] = dur.apply(lambda t: t[0])
    out['duration_type'] = dur.apply(lambda t: t[1])

    return out


def compute_views(df: pd.DataFrame) -> AnalysisData:
    df_year = df.dropna(subset=['year_added']).copy()
    if not df_year.empty:
        df_year['year_added'] = df_year['year_added'].astype(int)
    annual = (
        df_year.groupby(['year_added', 'type']).size().reset_index(name='count')
        if not df_year.empty else pd.DataFrame(columns=['year_added', 'type', 'count'])
    )

    genres = explode_and_normalize_genres(df)

    top_genres = genres['genre'].value_counts()
    focus_genres = top_genres.head(10).index.tolist()
    genre_year = (
        genres.dropna(subset=['year_added'])
        .query('genre in @focus_genres')
        .groupby(['year_added', 'genre'])
        .size()
        .reset_index(name='count')
        if 'year_added' in genres and not genres['year_added'].dropna().empty
        else pd.DataFrame(columns=['year_added', 'genre', 'count'])
    )

    countries = (
        df[['show_id', 'country', 'year_added']]
        .assign(country=lambda d: d['country'].astype(str).str.split(','))
        .explode('country')
    )
    countries['country'] = countries['country'].astype(str).str.strip()
    countries = countries.replace({'country': {'': 'Unknown', 'nan': 'Unknown'}})
    top_countries = countries['country'].value_counts()

    return AnalysisData(
        df=df,
        df_year=df_year,
        annual=annual,
        top_genres=top_genres,
        genre_year=genre_year,
        top_countries=top_countries,
    )


def compute_insights(analysis: AnalysisData) -> List[str]:
    insights: List[str] = []
    if not analysis.annual.empty:
        latest_year = int(analysis.annual['year_added'].max())
        latest = analysis.annual[analysis.annual['year_added'] == latest_year].sort_values('count', ascending=False)
        msg = 'Latest year with data: ' + str(latest_year) + "\n" + \
              "\n".join(f"  - {t}: {c}" for t, c in zip(latest['type'], latest['count']))
        insights.append('Annual additions — ' + msg)
    if not analysis.top_genres.empty:
        gmsg = ', '.join([f"{g} ({n})" for g, n in analysis.top_genres.head(5).items()])
        insights.append('Top genres overall: ' + gmsg)
    if not analysis.top_countries.empty:
        cmsg = ', '.join([f"{c} ({n})" for c, n in analysis.top_countries.head(5).items()])
        insights.append('Top contributing countries: ' + cmsg)
    return insights


def ensure_reports_dir(reports_dir: str = 'reports') -> str:
    os.makedirs(reports_dir, exist_ok=True)
    return reports_dir


def export_key_charts(analysis: AnalysisData, reports_dir: str = 'reports') -> Dict[str, str]:
    """Save key matplotlib charts as PNG files and return dict of paths."""
    import matplotlib.pyplot as plt
    import seaborn as sns

    ensure_reports_dir(reports_dir)
    saved: Dict[str, str] = {}

    # Movies vs TV Shows overall
    fig, ax = plt.subplots(figsize=(8, 4))
    order = ['Movie', 'TV Show']
    try:
        import seaborn as sns  # ensure available in scope
        sns.countplot(data=analysis.df, x='type', order=order, palette='Set2', ax=ax)
    except Exception:
        # Fallback: simple pandas plot
        analysis.df['type'].value_counts().reindex(order).plot(kind='bar', ax=ax)
    ax.set_title('Overall Distribution: Movies vs TV Shows')
    ax.set_xlabel('Type'); ax.set_ylabel('Count')
    path1 = os.path.join(reports_dir, 'overall_movies_vs_tv.png')
    fig.tight_layout(); fig.savefig(path1, dpi=150)
    plt.close(fig)
    saved['overall_movies_vs_tv'] = path1

    # Annual additions by type
    if not analysis.annual.empty:
        fig, ax = plt.subplots(figsize=(10, 4))
        sns.lineplot(data=analysis.annual, x='year_added', y='count', hue='type', marker='o', ax=ax)
        ax.set_title('Additions per Year by Type')
        ax.set_xlabel('Year added'); ax.set_ylabel('Titles added')
        path2 = os.path.join(reports_dir, 'annual_additions_by_type.png')
        fig.tight_layout(); fig.savefig(path2, dpi=150)
        plt.close(fig)
        saved['annual_additions_by_type'] = path2

    # Top genres
    if not analysis.top_genres.empty:
        fig, ax = plt.subplots(figsize=(10, 6))
        g = analysis.top_genres.head(15).sort_values()
        g.plot(kind='barh', color='#1f77b4', ax=ax)
        ax.set_title('Top 15 Genres (Overall)')
        ax.set_xlabel('Count'); ax.set_ylabel('Genre')
        path3 = os.path.join(reports_dir, 'top_genres.png')
        fig.tight_layout(); fig.savefig(path3, dpi=150)
        plt.close(fig)
        saved['top_genres'] = path3

    # Top countries
    if not analysis.top_countries.empty:
        fig, ax = plt.subplots(figsize=(10, 6))
        c = analysis.top_countries.head(15).sort_values()
        c.plot(kind='barh', color='#ff7f0e', ax=ax)
        ax.set_title('Top 15 Contributing Countries (Overall)')
        ax.set_xlabel('Count'); ax.set_ylabel('Country')
        path4 = os.path.join(reports_dir, 'top_countries.png')
        fig.tight_layout(); fig.savefig(path4, dpi=150)
        plt.close(fig)
        saved['top_countries'] = path4

    return saved
