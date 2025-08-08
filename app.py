import streamlit as st
import pandas as pd
import requests
import base64
import io
import datetime

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
    selected = st.selectbox("Wähle einen Eintrag zum Bearbeiten oder Löschen:", options)
    selected_index = options.index(selected)
    zeile = df.iloc[selected_index]

    # Hilfsfunktion zur sicheren Indexsuche
    def safe_index(lst, value):
        try:
            return lst.index(value)
        except ValueError:
            return 0

    tag_options = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
    ort_options = sorted(df["Ort"].dropna().unique().tolist())
    kueche_options = sorted(df["Küche"].dropna().unique().tolist())
    zeit_options = sorted(df["Zeit"].dropna().unique().tolist())

    tag = st.selectbox("Tag", tag_options, index=safe_index(tag_options, zeile["Tag"]))
    ort = st.selectbox("Ort", ort_options, index=safe_index(ort_options, zeile["Ort"]))
    foodtruck = st.text_input("Foodtruck", zeile["Foodtruck"])
    kueche = st.selectbox("Küche", kueche_options, index=safe_index(kueche_options, zeile["Küche"]))
    zeit = st.selectbox("Zeit", zeit_options, index=safe_index(zeit_options, zeile["Zeit"]))
    website = st.text_input("Website (optional)", zeile.get("Website", ""))

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Eintrag speichern"):
            df.iloc[selected_index] = [tag, ort, foodtruck, kueche, zeit, website]
            speichere_daten(df)

    with col2:
        if st.button("Eintrag löschen"):
            df = df.drop(df.index[selected_index]).reset_index(drop=True)
            speichere_daten(df)
            st.success("Eintrag wurde gelöscht!")
            st.experimental_rerun()  # Seite neu laden, damit Auswahl aktualisiert wird

    st.markdown("---")
    neu_hinzufuegen_form(df)


def neu_hinzufuegen_form(df):
    st.header("➕ Neuen Eintrag hinzufügen")

    tag_options = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
    ort_options = sorted(df["Ort"].dropna().unique().tolist())
    kueche_options = sorted(df["Küche"].dropna().unique().tolist())

    with st.form("hinzufuegen_form"):
        tag_select = st.selectbox("Tag auswählen", tag_options)

        ort_select = st.selectbox("Ort auswählen", ort_options) if ort_options else None
        ort_new = st.text_input("Oder neuen Ort eingeben")

        foodtruck_new = st.text_input("Foodtruck", "")

        kueche_select = st.selectbox("Küche auswählen", kueche_options) if kueche_options else None
        kueche_new = st.text_input("Oder neue Küche eingeben")

        start_zeit = st.time_input("Startzeit", datetime.time(11, 0))
        end_zeit = st.time_input("Endzeit", datetime.time(14, 0))

        website_new = st.text_input("Website (optional)", "")

        submit = st.form_submit_button("Neuen Eintrag hinzufügen")

        if submit:
            zeit_new = f"{start_zeit.strftime('%H:%M')}-{end_zeit.strftime('%H:%M')}"
            tag_final = tag_new.strip() if tag_new.strip() else tag_select
            ort_final = ort_new.strip() if ort_new.strip() else ort_select
            kueche_final = kueche_new.strip() if kueche_new.strip() else kueche_select
            zeit_final = zeit_new.strip() if zeit_new.strip() else zeit_select

            if tag_final and ort_final and foodtruck_new and kueche_final and zeit_final:
                neuer_eintrag = {
                    "Tag": tag_final,
                    "Ort": ort_final,
                    "Foodtruck": foodtruck_new,
                    "Küche": kueche_final,
                    "Zeit": zeit_final,
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







