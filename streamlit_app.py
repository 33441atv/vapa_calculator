import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="VAPA Overload Calculator", page_icon="📊")

st.title("VAPA Overload Calculator")

uploaded_file = st.file_uploader("Upload your Excel file", type=['xlsx', 'xls'])

if uploaded_file is not None:
    if 'vapa overload' not in uploaded_file.name.lower():
        st.error("File name must contain 'vapa overload'")
    else:
        with st.spinner('Processing file...'):
            # Read the Excel file
            df = pd.read_excel(uploaded_file)
            
            # Step 1: Delete columns C, G-L
            columns_to_delete = ['C', 'G', 'H', 'I', 'J', 'K', 'L']
            df = df.drop(columns=columns_to_delete, errors='ignore')

            # Step 2: Delete rows not containing specific words
            keywords = ['MUSIC', 'PHYS ED', 'ART', 'CREATIVE']
            df = df[df['Course Title'].str.contains('|'.join(keywords), case=False, na=False)]

            # Step 3: Delete rows where total students equals 0
            df = df[df['Total Students'] != 0]

            # Step 4: Add new columns
            df['Base Students'] = 0
            df['Max Students'] = 0
            df['Total Overload'] = 0
            df['Base Overload'] = 0
            df['Max Overload'] = 0

            # Step 5: Assign Base Students and Max Students based on conditions
            for index, row in df.iterrows():
                title = row['Course Title'].upper()
                if any(x in title for x in ['1', '2', '3']):
                    df.at[index, 'Base Students'] = 23
                    df.at[index, 'Max Students'] = 25
                elif any(x in title for x in ['4', '5']):
                    df.at[index, 'Base Students'] = 26
                    df.at[index, 'Max Students'] = 28
                elif any(x in title for x in ['KINDER', 'K']):
                    df.at[index, 'Base Students'] = 22
                    df.at[index, 'Max Students'] = 24

            # Step 6: Calculate Total Overload
            df['Total Overload'] = df['Total Students'] - df['Base Students']
            df['Total Overload'] = df['Total Overload'].apply(lambda x: max(0, x))

            # Step 7: Calculate Max Overload
            df['Max Overload'] = df['Total Students'] - df['Max Students']
            df['Max Overload'] = df['Max Overload'].apply(lambda x: max(0, x))

            # Step 8: Calculate Base Overload
            df['Base Overload'] = df.apply(lambda row: row['Total Overload'] if row['Total Overload'] <= 2 else row['Total Overload'] - row['Max Overload'], axis=1)

            # Step 9: Sort by Staff Name
            df = df.sort_values(by='Staff Name')

            # Step 10: Add blank rows and calculate totals
            results = []
            for staff_name, group in df.groupby('Staff Name'):
                results.append(group)
                blank_row = pd.Series('', index=group.columns)
                blank_row['Staff Name'] = staff_name
                blank_row['Base Overload'] = group['Base Overload'].sum()
                blank_row['Max Overload'] = group['Max Overload'].sum()
                results.append(blank_row)

            df = pd.concat(results, ignore_index=True)

            # Step 11: Add pay columns (keep as numbers for calculations)
            df['Base Overload Pay'] = df['Base Overload']
            df['Max Overload Pay'] = df['Max Overload'] * 1.5

            # Step 12: Calculate Total Monthly Overload first (while values are still numeric)
            df['Total Monthly Overload'] = (df['Base Overload Pay'] + df['Max Overload Pay']) * 30 / 8

            # Format all monetary columns as currency after calculations are complete
            for col in ['Base Overload Pay', 'Max Overload Pay', 'Total Monthly Overload']:
                df[col] = df[col].apply(lambda x: f"${x:.2f}" if pd.notnull(x) and x != '' else x)

            # Create download button
            output = BytesIO()
            df.to_excel(output, index=False)
            output.seek(0)
            
            st.success('File processed successfully!')
            st.download_button(
                label="Download Processed File",
                data=output,
                file_name=f"Processed_{uploaded_file.name}",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            # Show preview of processed data
            st.subheader("Preview of Processed Data")
            st.dataframe(df)