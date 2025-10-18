import os
import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt

from src.analysis import load_netflix_dataset, clean_and_engineer, compute_views, compute_insights, export_key_charts, ensure_reports_dir, explode_and_normalize_genres

st.set_page_config(page_title='Netflix Content Trends', layout='wide')

st.title('📊 Netflix Content Trends — Interactive Dashboard')

# Let loader auto-detect common filenames (strict local files only)
DATA_PATH = st.sidebar.text_input('Dataset path (optional)', '')
TOP_N_GENRES = st.sidebar.slider('Top N Genres', 5, 30, 15, step=1)
if st.sidebar.button('Reload data'):
    st.rerun()

try:
    path_input = DATA_PATH if DATA_PATH.strip() else None
    df_raw = load_netflix_dataset(path_input, strict=True)
    df = clean_and_engineer(df_raw)
    analysis = compute_views(df)
    st.sidebar.success('Dataset loaded successfully')
except Exception as e:
    st.error(f"Failed to load dataset: {e}")
    st.stop()

st.sidebar.header('Filters')
min_year = int(analysis.df['year_added'].min()) if analysis.df['year_added'].notna().any() else 2008
max_year = int(analysis.df['year_added'].max()) if analysis.df['year_added'].notna().any() else 2025
year_range = st.sidebar.slider('Year added range', min_year, max_year, (min_year, max_year))

filtered = analysis.df.copy()
filtered = filtered[(filtered['year_added'].fillna(min_year).astype(int) >= year_range[0]) &
                    (filtered['year_added'].fillna(max_year).astype(int) <= year_range[1])]

# Overall distribution (Plotly)
with st.container():
    st.subheader('Movies vs TV Shows — Distribution')
    dist = filtered['type'].value_counts().reset_index()
    dist.columns = ['type', 'count']
    fig = px.bar(dist, x='type', y='count', color='type', text='count', color_discrete_sequence=px.colors.qualitative.Set2)
    st.plotly_chart(fig, use_container_width=True)

# Annual trend
with st.container():
    st.subheader('Additions per Year by Type')
    df_year = filtered.dropna(subset=['year_added']).copy()
    if not df_year.empty:
        annual = df_year.groupby(['year_added', 'type']).size().reset_index(name='count')
        fig2 = px.line(annual, x='year_added', y='count', color='type', markers=True)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info('No year data available for selected range.')

# Top genres
with st.container():
    st.subheader('Top Genres (Overall)')
    gdf = explode_and_normalize_genres(filtered)
    gcounts = gdf['genre'].value_counts().head(TOP_N_GENRES)
    top_genres = gcounts.reset_index()
    top_genres.columns = ['genre', 'count']
    total = gdf['genre'].shape[0] if gdf.shape[0] else 1
    top_genres['pct'] = (top_genres['count'] / total * 100).round(1)
    fig3 = px.bar(top_genres.sort_values('count'), y='genre', x='count', orientation='h',
                  text=top_genres['pct'].astype(str) + '%', color='count',
                  color_continuous_scale='Blues')
    fig3.update_layout(xaxis_title='Count', yaxis_title='Genre')
    st.plotly_chart(fig3, use_container_width=True)

# Top countries
with st.container():
    st.subheader('Top Countries (Overall)')
    countries = (filtered[['show_id', 'country']]
                 .assign(country=lambda d: d['country'].str.split(','))
                 .explode('country'))
    countries['country'] = countries['country'].astype(str).str.strip()
    top_countries = countries['country'].value_counts().head(20).reset_index()
    top_countries.columns = ['country', 'count']
    fig4 = px.bar(top_countries, y='country', x='count', orientation='h', color='count')
    st.plotly_chart(fig4, use_container_width=True)

# Content Rating Distribution
with st.container():
    st.subheader('Content Rating Distribution')
    rating_counts = filtered['rating'].value_counts().head(15).reset_index()
    rating_counts.columns = ['rating', 'count']
    fig5 = px.pie(rating_counts, values='count', names='rating', title='Distribution by Age Rating',
                  color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig5, use_container_width=True)

# Top Directors
with st.container():
    st.subheader('Top 15 Directors by Content Count')
    directors = (filtered[['show_id', 'director']]
                .assign(director=lambda d: d['director'].str.split(','))
                .explode('director'))
    directors['director'] = directors['director'].astype(str).str.strip()
    directors = directors[directors['director'].notna() & (directors['director'] != 'Unknown') & (directors['director'] != 'nan')]
    top_directors = directors['director'].value_counts().head(15).reset_index()
    top_directors.columns = ['director', 'count']
    fig6 = px.bar(top_directors.sort_values('count'), y='director', x='count', orientation='h',
                  color='count', color_continuous_scale='Greens')
    st.plotly_chart(fig6, use_container_width=True)

# Duration Analysis for Movies
with st.container():
    st.subheader('Movie Duration Distribution')
    movies_only = filtered[filtered['type'] == 'Movie'].copy()
    if not movies_only.empty:
        # Extract minutes from duration
        movies_only['duration_min'] = movies_only['duration'].astype(str).str.extract(r'(\d+)').astype(float)
        movies_only = movies_only.dropna(subset=['duration_min'])
        if not movies_only.empty:
            fig7 = px.histogram(movies_only, x='duration_min', nbins=30, 
                               title='Movie Duration Distribution (minutes)',
                               labels={'duration_min': 'Duration (minutes)', 'count': 'Number of Movies'},
                               color_discrete_sequence=['#1f77b4'])
            fig7.update_layout(showlegend=False)
            st.plotly_chart(fig7, use_container_width=True)
        else:
            st.info('No duration data available for movies.')
    else:
        st.info('No movies in selected date range.')

# TV Show Seasons Distribution
with st.container():
    st.subheader('TV Show Seasons Distribution')
    tv_only = filtered[filtered['type'] == 'TV Show'].copy()
    if not tv_only.empty:
        tv_only['seasons'] = tv_only['duration'].astype(str).str.extract(r'(\d+)').astype(float)
        tv_only = tv_only.dropna(subset=['seasons'])
        if not tv_only.empty:
            season_counts = tv_only['seasons'].value_counts().sort_index().head(10).reset_index()
            season_counts.columns = ['seasons', 'count']
            fig8 = px.bar(season_counts, x='seasons', y='count', 
                         title='Number of TV Shows by Season Count',
                         labels={'seasons': 'Number of Seasons', 'count': 'Number of Shows'},
                         color='count', color_continuous_scale='Reds')
            st.plotly_chart(fig8, use_container_width=True)
        else:
            st.info('No season data available for TV shows.')
    else:
        st.info('No TV shows in selected date range.')

# Genre Trends Over Time
with st.container():
    st.subheader('Top 5 Genre Trends Over Time')
    gdf_time = explode_and_normalize_genres(filtered)
    gdf_time = gdf_time.dropna(subset=['year_added'])
    if not gdf_time.empty:
        # Get top 5 overall genres
        top5_genres = gdf_time['genre'].value_counts().head(5).index.tolist()
        gdf_top5 = gdf_time[gdf_time['genre'].isin(top5_genres)]
        genre_year = gdf_top5.groupby(['year_added', 'genre']).size().reset_index(name='count')
        fig9 = px.line(genre_year, x='year_added', y='count', color='genre', 
                      markers=True, title='Top 5 Genre Evolution Over Years')
        st.plotly_chart(fig9, use_container_width=True)
    else:
        st.info('No year data available for genre trends.')

# Monthly Addition Patterns (if date data available)
with st.container():
    st.subheader('Content Addition Patterns by Month')
    df_with_dates = filtered.dropna(subset=['date_added']).copy()
    if not df_with_dates.empty:
        try:
            df_with_dates['month'] = pd.to_datetime(df_with_dates['date_added'], errors='coerce').dt.month_name()
            month_counts = df_with_dates['month'].value_counts().reindex([
                'January', 'February', 'March', 'April', 'May', 'June',
                'July', 'August', 'September', 'October', 'November', 'December'
            ]).reset_index()
            month_counts.columns = ['month', 'count']
            fig10 = px.bar(month_counts, x='month', y='count', 
                          title='Content Additions by Month (All Years)',
                          color='count', color_continuous_scale='Viridis')
            fig10.update_xaxes(tickangle=45)
            st.plotly_chart(fig10, use_container_width=True)
        except:
            st.info('Unable to parse month data from date_added.')
    else:
        st.info('No date_added data available.')

# Insights
with st.expander('Automated Insights'):
    for line in compute_insights(analysis):
        st.write('- ' + line)

# Export key charts button
reports_dir = ensure_reports_dir('reports')
if st.button('Export key charts to reports/ folder'):
    saved = export_key_charts(analysis, reports_dir=reports_dir)
    st.success(f"Saved {len(saved)} charts to {reports_dir}")
    for name, path in saved.items():
        st.write(f"- {name}: {path}")
