import streamlit as st
import pandas as pd
from io import BytesIO

st.title("Excel Failų Sujungimas ir Apskaičiavimas")

uploaded_file1 = st.file_uploader("Įkelk VENIPAK .xlsx failą", type=["xlsx"])
uploaded_file2 = st.file_uploader("Įkelk RIVILE .xlsx failą", type=["xlsx"])

if uploaded_file1 and uploaded_file2:
    df1 = pd.read_excel(uploaded_file1, engine="openpyxl")
    df2 = pd.read_excel(uploaded_file2, engine="openpyxl")

    df1_subset = df1[["Kl.Siuntos Nr.", "Kaina, EUR", "Gavėjas"]].copy()
    df1_subset["Kaina, EUR su priemoka"] = df1_subset["Kaina, EUR"] * 1.3

    df2_subset = df2[["Dokumento Nr.", "Menedžeris", "Suma Be PVM"]].copy()
    df2_subset = df2_subset.rename(columns={
        "Dokumento Nr.": "Kl.Siuntos Nr.",
        "Suma Be PVM": "Pardavimas Be PVM"
    })

    df_merged = pd.merge(df1_subset, df2_subset, on="Kl.Siuntos Nr.", how="left")

    df_final = df_merged[[
        "Kl.Siuntos Nr.",
        "Kaina, EUR su priemoka",
        "Gavėjas",
        "Menedžeris",
        "Pardavimas Be PVM"
    ]]

    required_cols = [
        "Kl.Siuntos Nr.",
        "Kaina, EUR su priemoka",
        "Gavėjas",
        "Menedžeris",
        "Pardavimas Be PVM"
    ]

    df_final = df_final.dropna(subset=required_cols)
    df_final = df_final[
        df_final[required_cols].applymap(lambda x: str(x).strip() != "").all(axis=1)
    ]

    # Suvestinė
    summary = df_final.groupby("Menedžeris").agg({
        "Pardavimas Be PVM": "sum",
        "Kaina, EUR su priemoka": "sum"
    }).reset_index()

    summary["Logistika %"] = (
        summary["Kaina, EUR su priemoka"] / summary["Pardavimas Be PVM"]
    ).round(4)

    summary = summary.rename(columns={
        "Pardavimas Be PVM": "Pardavimas Be PVM (suma)",
        "Kaina, EUR su priemoka": "Logistikos išlaidos"
    })

    def convert_df_with_summary(df_main, df_summary):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_main.to_excel(writer, index=False, sheet_name='Sujungti Duomenys', startrow=0)
            startcol = 7
            df_summary.to_excel(writer, index=False, sheet_name='Sujungti Duomenys', startcol=startcol, startrow=0)

            workbook = writer.book
            worksheet = writer.sheets['Sujungti Duomenys']

            # Formatai
            percent_format = workbook.add_format({'num_format': '0.00%'})
            number_format = workbook.add_format({'num_format': '0.00'})

            # Stulpelių formatavimas
            col_map = {col: startcol + i for i, col in enumerate(df_summary.columns)}

            worksheet.set_column(col_map["Pardavimas Be PVM (suma)"], col_map["Pardavimas Be PVM (suma)"], 18, number_format)
            worksheet.set_column(col_map["Logistikos išlaidos"], col_map["Logistikos išlaidos"], 18, number_format)
            worksheet.set_column(col_map["Logistika %"], col_map["Logistika %"], 12, percent_format)

        return output.getvalue()

    st.success("✅ Duomenys apdoroti ir paruošti eksportui!")
    st.dataframe(df_final)

    st.download_button(
        label="📥 Atsisiųsti rezultatą su suvestine (.xlsx)",
        data=convert_df_with_summary(df_final, summary),
        file_name="sujungtas_rezultatas_su_suvestine.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
