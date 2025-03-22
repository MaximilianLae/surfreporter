# app.py
import streamlit as st
from search import SurfSpotRetriever
from forecast import get_weekend_forecast
from report_generator import SurfReportGenerator

def main():
    st.title("🏄 Weekend Surf Report Generator")
    
    # Input section
    col1, col2 = st.columns(2)
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
                    preferred_bottom=preferred_bottom
                )
                
                forecast = get_weekend_forecast()
                generator = SurfReportGenerator(spots, forecast)
                report = generator.generate_report(user_query)
                
                st.subheader("Your Personalized Surf Report")
                st.markdown(report)
                
                # Spot details expanders
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