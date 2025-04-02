# app.py

import streamlit as st
from search import SurfSpotRetriever
from forecast import get_weekend_forecast
from report_generator import SurfReportGenerator

def main():
    st.title("🏄 Weekend Surf Report Generator")
    
    # Input for retrieval parameters
    col1, col2, col3 = st.columns(3)
    with col1:
        preferred_direction = st.selectbox(
            "Preferred Wave Direction",
            options=["Right", "Left", "Left and right"],
            index=0
        )
    with col2:
        preferred_bottom = st.selectbox(
            "Preferred Bottom Type",
            options=["Reef", "Sand", "Sand with rocks"],
            index=0
        )
    with col3:
        top_k = st.number_input("Number of Top Spots to Retrieve", min_value=1, max_value=10, value=3, step=1)

    # Input for generation parameters
    generation_model = st.selectbox(
        "Generation Model",
        options=['gemini-2.0-flash-thinking-exp-01-21', 'gemini-1.5-pro']
    )
    temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.3, step=0.05)

    user_query = st.text_input(
        "Describe your ideal surf session",
        value="Fun right-handers with reef bottom"
    )
    
    if st.button("Generate Report"):
        retriever = SurfSpotRetriever()
        with st.spinner("Analyzing spots and weather conditions..."):
            try:
                spots = retriever.retrieve_spots(
                    user_query=user_query,
                    preferred_direction=preferred_direction,
                    preferred_bottom=preferred_bottom,
                    top_k=top_k  # Pass dynamic top_k
                )
                forecast = get_weekend_forecast()
                generator = SurfReportGenerator(
                    spots, forecast, generation_model=generation_model, temperature=temperature
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
            except Exception as e:
                st.error(f"Error generating report: {str(e)}")

if __name__ == "__main__":
    main()