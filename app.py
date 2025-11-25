import streamlit as st
import base64
import requests
import json
import os
from datetime import datetime
from shap_e.diffusion.sample import sample_latents
from shap_e.util.notebooks import create_glb_from_latent
from shap_e.models.download import load_model

st.set_page_config(page_title="EDOL 3D Generator", layout="wide")

st.title("EDOL 3D Generator")

prompt = st.text_input("Beschrijf je EDOL (bv. 'een vliegende pizza met ogen en antennes')")

if st.button("Genereer 3D-model"):
    if not prompt:
        st.error("Geef een beschrijving in!")
        st.stop()

    with st.spinner("3D-model wordt gegenereerd..."):
        device = "cpu"

        xm = load_model("transmitter", device=device)
        model = load_model("text300M", device=device)

        latents = sample_latents(
            batch_size=1,
            model=model,
            guidance_scale=15.0,
            prompt=prompt,
            device=device
        )

        output_path = "edol_model.glb"
        create_glb_from_latent(xm, latents[0], output_path)

    st.success("3D-model is klaar!")

    with open(output_path, "rb") as f:
        glb_bytes = f.read()

    # Toon 3D viewer
    st.write("### Voorbeeldweergave:")
    st.write("Gebruik externe viewer zoals https://gltf-viewer.donmccurdy.com/")
    st.download_button("Download GLB", data=glb_bytes, file_name="edol.glb")

    # CLOUD UPLOAD NAAR GITHUB
    st.write("### Opslaan in de cloud...")

    github_repo = "USERNAME/REPO"
    github_path = f"edols/{datetime.now().strftime('%Y%m%d_%H%M%S')}.glb"
    github_token = st.secrets["GITHUB_TOKEN"]

    encoded = base64.b64encode(glb_bytes).decode("utf-8")
    url = f"https://api.github.com/repos/{github_repo}/contents/{github_path}"
    
    data = {
        "message": "upload new EDOL model",
        "content": encoded
    }

    res = requests.put(url, headers={
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github+json"
    }, json=data)

    if res.status_code in (200, 201):
        st.success(f"Opgeslagen als **{github_path}** in GitHub!")
    else:
        st.error(f"Upload mislukt: {res.text}")
