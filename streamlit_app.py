import streamlit as st
import pandas as pd
from io import BytesIO

st.title("Batch Spreadsheet Processor")

uploaded_files = st.file_uploader("Upload Excel files", accept_multiple_files=True, type=["xlsx"])

if uploaded_files:
    final_results = []
    for file in uploaded_files:
        df = pd.read_excel(file)

        cols_to_drop = ["C", "G", "H", "I", "J", "K", "L"]
        df.drop(columns=cols_to_drop, inplace=True, errors="ignore")

        df = df[df["Course Title"].str.contains("MUSIC|PHYS ED|ART|CREATIVE", case=False)]
        df = df[df["Total Students"] != 0]

        df["Base Students"] = 0
        df["Max Students"] = 0
        df["Total Overload"] = 0
        df["Base Overload"] = 0
        df["Max Overload"] = 0

        conditions = [
            df["Course Title"].str.contains("1|2|3", case=False),
            df["Course Title"].str.contains("4|5", case=False),
            df["Course Title"].str.contains("KINDER|K", case=False)
        ]
        base_values = [23, 26, 22]
        max_values = [25, 28, 24]

        for cond, b_val, m_val in zip(conditions, base_values, max_values):
            df.loc[cond, "Base Students"] = b_val
            df.loc[cond, "Max Students"] = m_val

        df["Total Overload"] = df.apply(lambda row: max(0, row["Total Students"] - row["Base Students"]), axis=1)
        df["Max Overload"] = df.apply(lambda row: max(0, row["Total Students"] - row["Max Students"]) if row["Total Overload"] > 2 else 0, axis=1)
        df["Base Overload"] = df.apply(lambda row: row["Total Overload"] if row["Total Overload"] <= 2 else row["Total Overload"] - row["Max Overload"], axis=1)

        df.sort_values("Staff Name", inplace=True)

        new_rows = []
        for staff_name, group in df.groupby("Staff Name"):
            total_base = group["Base Overload"].sum()
            total_max = group["Max Overload"].sum()
            new_rows.append({"Staff Name": staff_name, "Base Overload": total_base, "Max Overload": total_max})

        blank_rows = pd.DataFrame(new_rows)

        combined = []
        for staff_name, group in df.groupby("Staff Name"):
            combined.append(group)
            combined.append(blank_rows[blank_rows["Staff Name"] == staff_name])
        final_df = pd.concat(combined, ignore_index=True)

        final_df["Base Overload Pay"] = final_df["Base Overload"]
        final_df["Max Overload Pay"] = final_df["Max Overload"] * 1.5

        def calc_currency(x):
            return f"${x:.2f}"

        final_df["Base Overload Pay"] = final_df["Base Overload Pay"].apply(calc_currency)
        final_df["Max Overload Pay"] = final_df["Max Overload Pay"].apply(calc_currency)

        def calc_total_monthly(row):
            base_val = float(row["Base Overload Pay"].replace("$",""))
            max_val = float(row["Max Overload Pay"].replace("$",""))
            total = base_val + max_val
            monthly = (total * 30) / 8
            return f"${monthly:.2f}"

        final_df["Total Monthly Overload"] = final_df.apply(calc_total_monthly, axis=1)

        final_results.append(final_df)

    output = pd.concat(final_results, ignore_index=True)
    st.dataframe(output)

    buffer = BytesIO()
    with pd.ExcelWriter(buffer) as writer:
        output.to_excel(writer, index=False)
    st.download_button("Download Results", data=buffer.getvalue(), file_name="processed_results.xlsx")
