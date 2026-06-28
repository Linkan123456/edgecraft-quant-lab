import streamlit as st

from engine.confidence import generate_confidence_report


st.title("EdgeCraft Dashboard v0.61")
st.caption("Samlad bedömning av Research, Walk Forward och Monte Carlo")

st.sidebar.header("Confidence-inställningar")

research_score = st.sidebar.number_input(
    "Research Score",
    value=0.0,
    step=1.0
)

walk_forward_score = st.sidebar.number_input(
    "Walk Forward Score",
    value=0.0,
    step=1.0
)

monte_carlo_score = st.sidebar.number_input(
    "Monte Carlo Score",
    value=0.0,
    step=1.0
)

run = st.sidebar.button("SKAPA CONFIDENCE REPORT")


if run:
    report = generate_confidence_report(
        research_score=research_score,
        walk_forward_score=walk_forward_score,
        monte_carlo_score=monte_carlo_score
    )

    st.subheader("EdgeCraft Confidence Report")
    st.text(report)

    st.download_button(
        "Ladda ner Confidence Report",
        report.encode("utf-8"),
        file_name="edgecraft_confidence_report.txt",
        mime="text/plain"
    )

else:
    st.info("Fyll i scores och tryck på SKAPA CONFIDENCE REPORT.")