# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import io
import os

from utils import infer_numeric_columns, infer_categorical_columns, apply_filters, summary_stats
from components import dataset_uploader, df_preview
import db
import auth

st.set_page_config(page_title='DataViz Tool', layout='wide')

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.user_id = None

if 'df' not in st.session_state:
    st.session_state.df = None
    st.session_state.df_name = None

# Authentication UI
if not st.session_state.authenticated:
    st.title('DataViz Tool - Login')
    
    tab1, tab2 = st.tabs(['Login', 'Sign Up'])
    
    with tab1:
        st.subheader('Login to your account')
        login_username = st.text_input('Username', key='login_username')
        login_password = st.text_input('Password', type='password', key='login_password')
        
        col1, col2 = st.columns([1, 3])
        if col1.button('Login', type='primary'):
            user_id = auth.authenticate(login_username, login_password)
            if user_id is not None:
                st.session_state.authenticated = True
                st.session_state.username = login_username
                st.session_state.user_id = user_id
                st.success(f'Welcome back, {login_username}!')
                st.rerun()
            else:
                st.error("Invalid username or password")

    
    with tab2:
        st.subheader('Create a new account')
        signup_username = st.text_input('Choose username', key='signup_username')
        signup_password = st.text_input('Choose password', type='password', key='signup_password')
        signup_password_confirm = st.text_input('Confirm password', type='password', key='signup_password_confirm')
        
        if st.button('Sign Up', type='primary'):
            if signup_password != signup_password_confirm:
                st.error('Passwords do not match')
            else:
                success = auth.create_user(signup_username, signup_password)
                if success:
                    st.success("Account created successfully! You can now login.")
                else:
                    st.error("Username already exists.")

    
    st.stop()

# Main Application (only shown if authenticated)
st.title('Data Visualization Tool')

# Logout button in sidebar
st.sidebar.markdown(f'**Logged in as:** {st.session_state.username}')
if st.sidebar.button('Logout'):
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.user_id = None
    st.session_state.df = None
    st.session_state.df_name = None
    st.rerun()

st.sidebar.markdown('---')
st.sidebar.header('Dataset')

# Load sample dataset
if st.sidebar.button('Load sample dataset'):
    sample_path = os.path.join('data', 'sample.csv')
    try:
        st.session_state.df = pd.read_csv(sample_path)
        st.session_state.df_name = 'sample.csv'
        st.success('Sample dataset loaded')
    except Exception as e:
        st.error(f'Could not load sample dataset: {e}')

# Show saved datasets
if st.sidebar.checkbox('Show saved datasets'):
    rows = db.list_datasets(st.session_state.user_id)
    if rows:
        st.sidebar.write(f'**Your datasets ({len(rows)}):**')
        for _id, name, uploaded_at in rows:
            cols = st.sidebar.columns([3, 1])
            if cols[0].button(f'📂 {name}', key=f'load_{name}_{_id}'):
                df_loaded = db.load_dataset(name, st.session_state.user_id)
                if df_loaded is not None:
                    st.session_state.df = df_loaded
                    st.session_state.df_name = name
                    st.success(f'Loaded dataset: {name}')
                    st.rerun()
            if cols[1].button('🗑️', key=f'del_{name}_{_id}'):
                db.delete_dataset(name, st.session_state.user_id)
                st.sidebar.success(f'Deleted: {name}')
                st.rerun()
    else:
        st.sidebar.info('No saved datasets yet.')

# File uploader
uploaded_df, uploaded_name = dataset_uploader()
if uploaded_df is not None:
    st.session_state.df = uploaded_df
    st.session_state.df_name = uploaded_name
    if st.sidebar.checkbox('Auto-save uploaded dataset to DB'):
        try:
            db.save_dataset(uploaded_name, uploaded_df, st.session_state.user_id)
            st.sidebar.success('Uploaded dataset saved to DB')
        except Exception as e:
            st.sidebar.error(f'Could not save dataset: {e}')

if st.session_state.df is None:
    st.info('📤 Upload a CSV or click "Load sample dataset" to begin.')
    st.stop()

df = st.session_state.df.copy()

st.sidebar.markdown('---')

st.sidebar.header('Explore & Filter')
numeric_cols = infer_numeric_columns(df)
cat_cols = infer_categorical_columns(df)

# Build filters
filters = []
with st.sidebar.expander('Add filters'):
    n_filters = st.number_input('Number of filters', min_value=0, max_value=6, value=0)
    for i in range(n_filters):
        col = st.selectbox(f'Filter {i+1} - column', options=df.columns, key=f'filter_col_{i}')
        dtype = 'numeric' if col in numeric_cols else 'categorical'
        if dtype == 'numeric':
            op = st.selectbox(f'Filter {i+1} - operator', options=['==', '!=', '>', '<', '>=', '<='], key=f'filter_op_{i}')
            val = st.text_input(f'Filter {i+1} - value', key=f'filter_val_{i}')
            if val != '':
                filters.append({'col': col, 'op': op, 'value': val})
        else:
            op = st.selectbox(f'Filter {i+1} - operator', options=['==', '!=', 'in', 'contains'], key=f'filter_op_{i}')
            if op == 'in':
                val = st.text_input(f'Filter {i+1} - comma separated values', key=f'filter_val_{i}')
                vals = [v.strip() for v in val.split(',') if v.strip()]
                if vals:
                    filters.append({'col': col, 'op': 'in', 'value': vals})
            else:
                val = st.text_input(f'Filter {i+1} - value', key=f'filter_val_{i}')
                if val != '':
                    filters.append({'col': col, 'op': op, 'value': val})

# Apply filters
filtered = apply_filters(df, filters) if filters else df.copy()
st.sidebar.write(f'Filtered rows: {len(filtered)}')

st.sidebar.header('Data Views')

# Show raw data
if st.sidebar.checkbox('Show raw data'):
    st.subheader("Raw Data")
    df_preview(df)

# Show filtered data
if st.sidebar.checkbox('Show filtered data'):
    st.subheader("Filtered Data")
    df_preview(filtered)

# Visualization controls
st.sidebar.header('Visualization')
chart_type = st.sidebar.selectbox('Chart type', ['Scatter', 'Line', 'Bar', 'Histogram', 'Box', 'Pie', 'Heatmap', 'Parallel Coordinates'])
x_col = st.sidebar.selectbox('X column', options=list(df.columns), index=0)
# default y selection tries to pick a different column when possible
default_y_idx = 1 if len(df.columns) > 1 else 0
if chart_type not in ['Histogram', 'Parallel Coordinates']:
    y_col = st.sidebar.selectbox('Y column', options=list(df.columns), index=default_y_idx)
else:
    y_col = None
color_col = st.sidebar.selectbox('Color', options=[None] + list(df.columns), index=0)
size_col = st.sidebar.selectbox('Size (scatter only)', options=[None] + list(numeric_cols), index=0)

# Aggregation
agg_func = st.sidebar.selectbox('Aggregation function (for grouping)', ['mean', 'sum', 'count', 'median'])
groupby_cols = st.sidebar.multiselect('Group by columns (optional)', options=list(df.columns))

# Plot area
st.header(f'{chart_type} chart')
try:
    numeric_cols_df = filtered.select_dtypes(include=[np.number])
    if chart_type == 'Scatter':
        fig = px.scatter(filtered, x=x_col, y=y_col, color=color_col, size=size_col, title='Scatter plot')
    elif chart_type == 'Line':
        fig = px.line(filtered, x=x_col, y=y_col, color=color_col, title='Line chart')
    elif chart_type == 'Bar':
        if groupby_cols:
            agg = filtered.groupby(groupby_cols).agg({y_col: agg_func}).reset_index()
            # choose first group column for x-axis when multiple provided
            x_axis = groupby_cols[0]
            fig = px.bar(agg, x=x_axis, y=y_col, color=color_col, title='Grouped bar chart')
        else:
            fig = px.bar(filtered, x=x_col, y=y_col, color=color_col, title='Bar chart')
    elif chart_type == 'Histogram':
        nbins = st.sidebar.slider('Number of bins', 5, 200, 30)
        fig = px.histogram(filtered, x=x_col, nbins=nbins, color=color_col, title='Histogram')
    elif chart_type == 'Box':
        fig = px.box(filtered, x=x_col, y=y_col, color=color_col, title='Box plot')
    elif chart_type == 'Pie':
        # if y_col is None or non-numeric, count occurrences
        if y_col is None:
            fig = px.pie(filtered, names=x_col, title='Pie chart')
        else:
            try:
                fig = px.pie(filtered, names=x_col, values=y_col, title='Pie chart')
            except Exception:
                fig = px.pie(filtered, names=x_col, title='Pie chart')

    elif chart_type == "Heatmap":
        if x_col is None or y_col is None:
            st.error("Select both X and Y columns for Heatmap.")
            st.stop()

        value_col = color_col
        if value_col is None:
            if numeric_cols_df.empty:
                st.error("No numeric column available for heatmap coloring.")
                st.stop()
            value_col = numeric_cols_df.columns[0]

        if not pd.api.types.is_numeric_dtype(filtered[value_col]):
            aggfunc = "count"
        else:
            aggfunc = "mean"

        try:
            pivot = (
                filtered
                .groupby([y_col, x_col])[value_col]
                .agg(aggfunc)
                .unstack(fill_value=0)
            )

            fig = px.imshow(
                pivot,
                aspect="auto",
                labels={"x": x_col, "y": y_col, "color": value_col},
                title=f"Heatmap ({value_col})",
            )
        except Exception as e:
            st.error(f"Could not create heatmap: {e}")
            st.stop()

    elif chart_type == "Parallel Coordinates":
        if numeric_cols_df.shape[1] < 2:
            st.error("Need at least 2 numeric columns for parallel coordinates.")
            st.stop()

        color_column = color_col
        if color_column is None:
            color_column = numeric_cols_df.columns[0]

        # Convert non-numeric color column to numeric codes
        if not pd.api.types.is_numeric_dtype(filtered[color_column]):
            filtered["_color_code_"] = filtered[color_column].astype("category").cat.codes
            color_field = "_color_code_"
        else:
            color_field = color_column

        try:
            fig = px.parallel_coordinates(
                filtered,
                dimensions=numeric_cols_df.columns,
                color=color_field,
                color_continuous_scale="Blues",
                labels={color_field: color_column, **{col: col for col in numeric_cols_df.columns}},
                title=f"Parallel Coordinates (colored by {color_column})"
            )

            # Fix for first axis visibility
            fig.update_layout(
                margin=dict(l=80, r=80, t=80, b=80),
                plot_bgcolor="white",
                paper_bgcolor="white"
            )

            # Fix legend title to show the real color column name
            fig.update_coloraxes(colorbar_title=color_column)

            # Keep consistent color mapping
            fig.update_traces(
                line=dict(coloraxis="coloraxis")
            )

        except Exception as e:
            st.error(f"Could not create parallel coordinates: {e}")
            st.stop()

    st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.error(f'Could not create chart: {e}')

# Data download
st.sidebar.header('Export')
csv_bytes = filtered.to_csv(index=False).encode('utf-8')
st.sidebar.download_button('Download filtered CSV', data=csv_bytes, file_name='filtered_dataset.csv', mime='text/csv')

# Save dataset
st.sidebar.header('Save')
save_name = st.sidebar.text_input('Name to save current filtered dataset as (optional)')
if st.sidebar.button('💾 Save to DB'):
    if save_name:
        try:
            db.save_dataset(save_name, filtered, st.session_state.user_id)
            st.sidebar.success(f'Saved dataset "{save_name}" to DB')
        except Exception as e:
            st.sidebar.error(f'Could not save: {e}')
    else:
        st.sidebar.error('Please enter a name to save')

# Show summary
with st.expander('Data summary'):
    st.write(summary_stats(filtered))