import streamlit as st
import pandas as pd
from io import BytesIO

# Set up the Streamlit app
st.title("Upload and Combine Excel Files")
st.write("Please upload three Excel files for processing and combining.")

# File upload widgets
uploaded_file1 = st.file_uploader("Upload Excel File 1", type=["xlsx", "xls"])
uploaded_file2 = st.file_uploader("Upload Excel File 2", type=["xlsx", "xls"])
uploaded_file3 = st.file_uploader("Upload Excel File 3", type=["xlsx", "xls"])

# Function to read and return the content of uploaded files
def process_file(file):
    if file:
        try:
            # Read the Excel file into a Pandas DataFrame
            return pd.read_excel(file)
        except Exception as e:
            st.error(f"An error occurred while processing the file: {e}")
            return None
    return None

# Process each uploaded file
file1_data = process_file(uploaded_file1)
file2_data = process_file(uploaded_file2)
file3_data = process_file(uploaded_file3)

# Combine the files if all are uploaded and valid
if file1_data is not None and file2_data is not None and file3_data is not None:
    # Concatenate the dataframes
    combined_data = pd.concat([file1_data, file2_data, file3_data], ignore_index=True)

    # Display a preview of the combined data
    st.write("Preview of Combined File:")
    st.write(combined_data.head())

    # Create a function to generate a downloadable Excel file
    def generate_excel_download(data):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            data.to_excel(writer, index=False, sheet_name='CombinedData')
        processed_data = output.getvalue()
        return processed_data

    # Generate the downloadable file
    processed_excel = generate_excel_download(combined_data)

    # Add a download button
    st.download_button(
        label="Download Combined Excel File",
        data=processed_excel,
        file_name="combined_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
else:
    st.info("Please upload all three Excel files to combine them.")