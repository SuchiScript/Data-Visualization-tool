# utils.py
import pandas as pd
import numpy as np
from typing import Tuple, List, Any, Dict

def infer_numeric_columns(df: pd.DataFrame) -> List[str]:
    return df.select_dtypes(include=[np.number]).columns.tolist()

def infer_categorical_columns(df: pd.DataFrame) -> List[str]:
    return df.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()

def summary_stats(df: pd.DataFrame) -> pd.DataFrame:
    # Return a transposed summary for readability
    descr = df.describe(include='all').transpose()
    descr['missing'] = df.isna().sum()
    descr['unique'] = df.nunique()
    return descr

def apply_filters(df: pd.DataFrame, filters: List[Dict[str, Any]]) -> pd.DataFrame:
    # filters: list of {col, op, value}
    out = df.copy()
    for f in filters:
        col, op, val = f['col'], f['op'], f['value']
        if op == '==':
            out = out[out[col] == _parse_value(out[col], val)]
        elif op == '!=':
            out = out[out[col] != _parse_value(out[col], val)]
        elif op == '>':
            out = out[out[col] > float(val)]
        elif op == '<':
            out = out[out[col] < float(val)]
        elif op == '>=':
            out = out[out[col] >= float(val)]
        elif op == '<=':
            out = out[out[col] <= float(val)]
        elif op == 'in':
            # val expected as list
            out = out[out[col].isin(val)]
        elif op == 'contains':
            out = out[out[col].astype(str).str.contains(str(val), na=False, case=False)]
    return out

def _parse_value(series: pd.Series, val: Any):
    # Try to cast val to numeric if the series is numeric
    try:
        if pd.api.types.is_numeric_dtype(series):
            return float(val)
    except Exception:
        pass
    return val

def aggregate(df: pd.DataFrame, groupby: List[str], agg_col: str, agg_func: str):
    if not groupby:
        if agg_func == 'count':
            return pd.DataFrame({agg_col: [len(df)]})
        return pd.DataFrame({agg_col: [getattr(df[agg_col], agg_func)()]})
    return df.groupby(groupby).agg({agg_col: agg_func}).reset_index()
