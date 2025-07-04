import streamlit as st
import pandas as pd

DATEI = "data.csv"
PASSWORT = "tuktukthai"

def lade_daten():
    return pd.read_csv(DATEI)

def speichere_daten(df):
    df.to_csv(DATEI, index=False)

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

    tag = st.text_input("Tag", zeile["Tag"])
    ort = st.text_input("Ort", zeile["Ort"])
    foodtruck = st.text_input("Foodtruck", zeile["Foodtruck"])
    kueche = st.text_input("Küche", zeile["Küche"])
    zeit = st.text_input("Zeit", zeile["Zeit"])
    website = st.text_input("Website (optional)", zeile.get("Website", ""))

    if st.button("Eintrag speichern"):
        df.iloc[selected_index] = [tag, ort, foodtruck, kueche, zeit, website]
        speichere_daten(df)
        st.success("Eintrag wurde gespeichert! Bitte lade die Seite neu, um die Änderungen zu sehen.")

    st.markdown("---")
    neu_hinzufuegen_form(df)

def neu_hinzufuegen_form(df):
    st.header("➕ Neuen Eintrag hinzufügen")
    with st.form("hinzufuegen_form"):
        tag_new = st.text_input("Tag", "")
        ort_new = st.text_input("Ort", "")
        foodtruck_new = st.text_input("Foodtruck", "")
        kueche_new = st.text_input("Küche", "")
        zeit_new = st.text_input("Zeit", "")
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
                st.success("Neuer Eintrag wurde hinzugefügt! Bitte lade die Seite neu, um die Änderungen zu sehen.")
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
        page_icon="🌮"  # Oder z. B. "favicon.png" falls du en eigene Datei hast
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
