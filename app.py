import streamlit as st
import os
from datetime import datetime
from generate_edol_with_face_and_wings import create_edol_glb

st.set_page_config(page_title="EDOL", page_icon="🍕", layout="wide")
st.title("EDOL – Jouw vliegende pizza-vriend")

# Map voor GLB-bestanden
OUTPUT_DIR = "generated_models"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Voeg model-viewer script toe
st.components.v1.html("""
<script type="module" src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js"></script>
""", height=0)

st.header("Genereer jouw EDOL")

# Prompt input
prompt = st.text_input("Typ hier een korte beschrijving van je EDOL (bv. 'vliegende pizza'):")

if st.button("Genereer EDOL"):
    if not prompt.strip():
        st.warning("⚠️ Typ eerst een naam of beschrijving!")
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(OUTPUT_DIR, f"edol_{prompt.replace(' ','_')}_{timestamp}.glb")

        # Genereer GLB
        create_edol_glb(filename)
        st.success(f"✅ Je EDOL is gegenereerd: {filename}")

        # Toon GLB in browser
        st.markdown(
            f"""
            <model-viewer src="{filename}" alt="EDOL model" auto-rotate camera-controls background-color="#ffffff" style="width: 100%; height: 400px;">
            </model-viewer>
            """,
            unsafe_allow_html=True
        )

        # Mint knop (simulatie)
        if st.button("Mint als NFT op Base Testnet"):
            st.balloons()
            st.success("🚀 Je pizza-EDOL is nu een NFT (gesimuleerd) op Base Testnet!")
            st.info(f"Bestand opgeslagen in cloud: {filename} (of lokale demo opslag)")

st.caption("Gebouwd door Lijs – 25 november 2025 – Gratis demo versie")
