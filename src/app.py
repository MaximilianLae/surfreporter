# app.py
import streamlit as st
from search import SurfSpotRetriever
from forecast import get_weekend_forecast
from report_generator import SurfReportGenerator

def main():
    st.title("🏄 Weekend Surf Report Generator")

    col1, col2, col3 = st.columns(3)
    with col1:
        preferred_direction = st.selectbox("Preferred Wave Direction", ["Right","Left","Left and right"])
    with col2:
        preferred_bottom = st.selectbox("Preferred Bottom Type", ["Reef","Sand","Sand with rocks"])
    with col3:
        top_k = st.number_input("Top-k Spots to Retrieve", 1, 10, 3)

    generation_model = st.selectbox("Generation Model", ["gpt-4o","o3-mini"])
    temperature = st.slider("Temperature", 0.0, 1.0, 0.3, 0.05)

    user_query = st.text_input("Describe your ideal surf session", "Fun right-handers with reef bottom")

    if st.button("Generate Report"):
        with st.spinner("Generating..."):
            retriever = SurfSpotRetriever()
            spots = retriever.retrieve_spots(
                user_query, preferred_direction, preferred_bottom, top_k
            )
            forecast = get_weekend_forecast()
            generator = SurfReportGenerator(
                spots, forecast, generation_model, temperature
            )
            report = generator.generate_report(user_query)

            st.subheader("Your Personalized Surf Report")
            st.markdown(report)

            st.subheader("Spot Details")
            for spot in spots:
                with st.expander(f"{spot['name']} ({spot['surf_level']})"):
                    st.write(f"**🌊 Wave Direction:** {spot['wave_direction']}")
                    st.write(f"**🏖️ Bottom Type:** {spot['bottom_type']}")
                    st.write(f"**👥 Crowd Factor:** {spot['crowd_factor']}")
                    st.write(spot['description'])

if __name__ == "__main__":
    main()
