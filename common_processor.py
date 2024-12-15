import streamlit as st
import pandas as pd
import traceback


def load_the_spreadsheet(spreadsheetname, sh):
    """Load a worksheet and convert it to a pandas DataFrame"""
    worksheet = sh.worksheet(spreadsheetname)
    values = worksheet.get_all_values()
    df = pd.DataFrame(values[1:], columns=values[0])
    return df

def update_worksheet(existing_df, data, sheet_name, success_msg, sh, spread):
    """Common function to update worksheet with new data"""
    if not data.empty:
        spread.df_to_sheet(
            data,
            sheet=sheet_name,
            index=False,
            headers=False, 
            start=(len(existing_df)+2, 1),
            replace=False
        )
        st.sidebar.success(success_msg)
    else:
        st.sidebar.info(f'No {sheet_name} data to update')