import streamlit as st
import pandas as pd
import requests
import base64
import io

# GitHub Config
GITHUB_REPO = "ICT-Wenzel/foodtruck"  # Beispiel: "maxmustermann/foodtruck-plan"
GITHUB_FILE_PATH = "data.csv"
BRANCH = "main"
TOKEN = st.secrets["token"]

PASSWORT = st.secrets["passwort"]

def lade_daten():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}?ref={BRANCH}"
    headers = {"Authorization": f"token {TOKEN}"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        content = r.json()['content']
        decoded = base64.b64decode(content)
        df = pd.read_csv(io.BytesIO(decoded))
        # SHA für spätere Updates speichern
        st.session_state.sha = r.json()['sha']
        return df
    else:
        st.error(f"Fehler beim Laden der Datei von GitHub: {r.status_code}")
        return pd.DataFrame(columns=["Tag", "Ort", "Foodtruck", "Küche", "Zeit", "Website"])

def speichere_daten(df):
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    content = csv_buffer.getvalue()
    content_encoded = base64.b64encode(content.encode()).decode()

    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}"
    headers = {"Authorization": f"token {TOKEN}"}
    data = {
        "message": "Update CSV via Streamlit App",
        "content": content_encoded,
        "sha": st.session_state.get("sha"),
        "branch": BRANCH
    }
    r = requests.put(url, headers=headers, json=data)
    if r.status_code in [200, 201]:
        st.success("CSV erfolgreich auf GitHub aktualisiert!")
        # neuen SHA speichern
        st.session_state.sha = r.json()['content']['sha']
    else:
        st.error(f"Fehler beim Speichern auf GitHub: {r.json()}")

def uebersicht():
    st.title("🌮 Foodtruck Wochenplan Übersicht")

    df = lade_daten()
    if df.empty:
        st.warning("Keine Daten vorhanden.")
        return

    tage = df["Tag"].unique()
    for tag in tage:
        st.subheader(f"📅 {tag}")
        tag_daten = df[df["Tag"] == tag]

        orte = tag_daten["Ort"].unique()
        for ort in orte:
            st.markdown(f"**📍 Ort:** {ort}")
            ort_daten = tag_daten[tag_daten["Ort"] == ort].copy()
            st.dataframe(
                ort_daten[["Foodtruck", "Küche", "Zeit", "Website"]].reset_index(drop=True),
                hide_index=True,
                use_container_width=True
            )

def bearbeiten():
    st.title("✏️ Foodtruck Daten bearbeiten")

    df = lade_daten()

    if df.empty:
        st.warning("Keine Daten zum Bearbeiten vorhanden.")
        neu_hinzufuegen_form(df)
        return

    options = df.apply(lambda row: f"{row['Tag']} - {row['Ort']} - {row['Foodtruck']}", axis=1).tolist()
    selected = st.selectbox("Wähle einen Eintrag zum Bearbeiten:", options)
    selected_index = options.index(selected)
    zeile = df.iloc[selected_index]

    # Dropdown-Optionen vorbereiten
    tag_options = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
    ort_options = sorted(df["Ort"].dropna().unique())
    kueche_options = sorted(df["Küche"].dropna().unique())
    zeit_options = sorted(df["Zeit"].dropna().unique())

    tag = st.selectbox("Tag", tag_options, index=tag_options.index(zeile["Tag"]) if zeile["Tag"] in tag_options else 0)
    ort = st.selectbox("Ort", ort_options, index=ort_options.tolist().index(zeile["Ort"]) if zeile["Ort"] in ort_options else 0)
    foodtruck = st.text_input("Foodtruck", zeile["Foodtruck"])
    kueche = st.selectbox("Küche", kueche_options, index=kueche_options.tolist().index(zeile["Küche"]) if zeile["Küche"] in kueche_options else 0)
    zeit = st.selectbox("Zeit", zeit_options, index=zeit_options.tolist().index(zeile["Zeit"]) if zeile["Zeit"] in zeit_options else 0)
    website = st.text_input("Website (optional)", zeile.get("Website", ""))

    if st.button("Eintrag speichern"):
        df.iloc[selected_index] = [tag, ort, foodtruck, kueche, zeit, website]
        speichere_daten(df)

    st.markdown("---")
    neu_hinzufuegen_form(df)


def neu_hinzufuegen_form(df):
    st.header("➕ Neuen Eintrag hinzufügen")

    tag_options = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
    ort_options = sorted(df["Ort"].dropna().unique())
    kueche_options = sorted(df["Küche"].dropna().unique())
    zeit_options = sorted(df["Zeit"].dropna().unique())

    with st.form("hinzufuegen_form"):
        tag_new = st.selectbox("Tag", tag_options)

        ort_new = (
            st.selectbox("Ort", ort_options)
            if ort_options else st.text_input("Ort", "")
        )

        foodtruck_new = st.text_input("Foodtruck", "")

        kueche_new = (
            st.selectbox("Küche", kueche_options)
            if kueche_options else st.text_input("Küche", "")
        )

        zeit_new = (
            st.selectbox("Zeit", zeit_options)
            if zeit_options else st.text_input("Zeit", "")
        )

        website_new = st.text_input("Website (optional)", "")

        submit = st.form_submit_button("Neuen Eintrag hinzufügen")

        if submit:
            if tag_new and ort_new and foodtruck_new and kueche_new and zeit_new:
                neuer_eintrag = {
                    "Tag": tag_new,
                    "Ort": ort_new,
                    "Foodtruck": foodtruck_new,
                    "Küche": kueche_new,
                    "Zeit": zeit_new,
                    "Website": website_new
                }
                df = pd.concat([df, pd.DataFrame([neuer_eintrag])], ignore_index=True)
                speichere_daten(df)
            else:
                st.error("Bitte fülle alle Pflichtfelder aus (Tag, Ort, Foodtruck, Küche, Zeit).")


def login():
    if "eingeloggt" not in st.session_state:
        st.session_state.eingeloggt = False
    if "passwort_eingabe" not in st.session_state:
        st.session_state.passwort_eingabe = ""

    def pruefe_passwort():
        if st.session_state.passwort_eingabe == PASSWORT:
            st.session_state.eingeloggt = True
            st.success("✅ Login erfolgreich!")
        else:
            st.error("❌ Falsches Passwort.")

    if not st.session_state.eingeloggt:
        st.text_input("🔐 Passwort eingeben:", type="password", key="passwort_eingabe", on_change=pruefe_passwort)
        st.stop()

def main():
    st.set_page_config(
        page_title="Foodtruck Wochenplan",
        layout="wide",
        page_icon="🌮"
    )

    login()

    st.sidebar.title("Navigation")
    seite = st.sidebar.radio("Wähle eine Seite:", ["Übersicht", "Bearbeiten"])

    if seite == "Übersicht":
        uebersicht()
    else:
        bearbeiten()

if __name__ == "__main__":
    main()

