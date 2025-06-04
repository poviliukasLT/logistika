import streamlit as st
import pandas as pd
from io import BytesIO

st.title("Excel Failų Sujungimas ir Apskaičiavimas")

uploaded_file1 = st.file_uploader("Įkelk VENIPAK .xlsx failą", type=["xlsx"])
uploaded_file2 = st.file_uploader("Įkelk RIVILE .xlsx failą", type=["xlsx"])

if uploaded_file1 and uploaded_file2:
    # Įkeliame abu failus
    df1 = pd.read_excel(uploaded_file1, engine="openpyxl")
    df2 = pd.read_excel(uploaded_file2, engine="openpyxl")

    # Iš pirmo failo paimame reikiamus stulpelius
    df1_subset = df1[["Kl.Siuntos Nr.", "Kaina, EUR", "Gavėjas"]].copy()
    df1_subset["Kaina, EUR su priemoka"] = df1_subset["Kaina, EUR"] * 1.3

    # Iš antro failo paimame reikiamus stulpelius
    df2_subset = df2[["Dokumento Nr.", "Menedžeris", "Suma Be PVM"]].copy()
    df2_subset = df2_subset.rename(columns={
        "Dokumento Nr.": "Kl.Siuntos Nr.",
        "Suma Be PVM": "Pardavimas Be PVM"
    })

    # Sujungiame pagal "Kl.Siuntos Nr."
    df_merged = pd.merge(df1_subset, df2_subset, on="Kl.Siuntos Nr.", how="left")

    # Galutinė stulpelių tvarka
    df_final = df_merged[[
        "Kl.Siuntos Nr.",
        "Kaina, EUR su priemoka",
        "Gavėjas",
        "Menedžeris",
        "Pardavimas Be PVM"
    ]]

    # Pašaliname eilutes, kuriose bent vienas reikalingas stulpelis yra NaN arba tuščias
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

    # Funkcija failui sukurti
    def convert_df(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Sujungti Duomenys')
        return output.getvalue()

    st.success("✅ Duomenys sėkmingai apdoroti ir išfiltruoti!")
    st.dataframe(df_final)

    st.download_button(
        label="📥 Atsisiųsti rezultatą (.xlsx)",
        data=convert_df(df_final),
        file_name="sujungtas_rezultatas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
