# components.py
import streamlit as st
import pandas as pd
from typing import Tuple

def dataset_uploader(key: str = 'uploader') -> Tuple[pd.DataFrame, str]:
    uploaded = st.file_uploader('Upload CSV', type=['csv'], key=key)
    if uploaded is not None:
        try:
            df = pd.read_csv(uploaded)
        except Exception:
            uploaded.seek(0)
            df = pd.read_csv(uploaded, encoding='utf-8', errors='replace')
        name = getattr(uploaded, 'name', 'uploaded_dataset')
        return df, name
    return None, None

def df_preview(df: pd.DataFrame):
    st.write(df.head())
    with st.expander('Show full data types and missing values'):
        st.write(pd.DataFrame({
            'dtype': df.dtypes.astype(str),
            'missing': df.isna().sum(),
            'unique': df.nunique()
        }))
