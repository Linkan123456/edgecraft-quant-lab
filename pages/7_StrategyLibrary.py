import streamlit as st
import pandas as pd


st.title("Strategy Library")
st.caption("Bibliotek över strategier som ska dokumenteras, kodas och valideras")

strategies = [
    {
        "Strategi": "OOPS Reversal",
        "Skapare": "Larry Williams",
        "Typ": "Reversal / Gap Reversal",
        "Status": "Research pågår",
        "Original dokumenterad": "Nej",
        "Kodad": "Nej",
        "Testad": "Nej",
        "Validerad": "Nej",
        "AI-optimerad": "Nej",
        "Kommentar": "Första strategin vi ska dokumentera exakt."
    },
    {
        "Strategi": "Double Seven",
        "Skapare": "Larry Connors",
        "Typ": "Mean Reversion",
        "Status": "Kodad och testbar",
        "Original dokumenterad": "Delvis",
        "Kodad": "Ja",
        "Testad": "Ja",
        "Validerad": "Delvis",
        "AI-optimerad": "Nej",
        "Kommentar": "Används som teknisk teststrategi i EdgeCraft."
    },
    {
        "Strategi": "Patrick Walker",
        "Skapare": "Patrick Walker",
        "Typ": "Trend / Breakout",
        "Status": "Ej startad",
        "Original dokumenterad": "Nej",
        "Kodad": "Nej",
        "Testad": "Nej",
        "Validerad": "Nej",
        "AI-optimerad": "Nej",
        "Kommentar": "Ska dokumenteras exakt innan kodning."
    },
    {
        "Strategi": "Sarid Harper",
        "Skapare": "Sarid Harper",
        "Typ": "Ej fastställd",
        "Status": "Ej startad",
        "Original dokumenterad": "Nej",
        "Kodad": "Nej",
        "Testad": "Nej",
        "Validerad": "Nej",
        "AI-optimerad": "Nej",
        "Kommentar": "Behöver research innan regler kan kodas."
    },
    {
        "Strategi": "Continuation",
        "Skapare": "EdgeCraft / Patrick",
        "Typ": "Trend continuation",
        "Status": "Ej kodad i EdgeCraft",
        "Original dokumenterad": "Delvis",
        "Kodad": "Nej",
        "Testad": "Nej",
        "Validerad": "Nej",
        "AI-optimerad": "Nej",
        "Kommentar": "Bygger på trend, box och breakout."
    }
]

df = pd.DataFrame(strategies)

st.subheader("Strategier")
st.dataframe(df, use_container_width=True)

st.subheader("Nästa strategi att arbeta med")

st.markdown("""
### OOPS Reversal

**Nästa steg:**
1. Samla exakta originalregler.
2. Låsa originalspecifikation.
3. Koda originalet.
4. Testa på flera marknader.
5. Testa flera timeframes.
6. Avgöra om strategin har edge.
7. Först därefter låta AI försöka förbättra den.
""")

st.info(
    "Regel: Ingen strategi optimeras eller förbättras förrän originalversionen är dokumenterad och testad."
)