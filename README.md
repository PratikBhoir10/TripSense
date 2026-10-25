# TripSense — Mumbai

Premium Streamlit Mumbai travel recommendation system with 200+ places, semantic recommendations, weather-aware ranking, area filtering, Google Maps/Route actions, and a local place-photo library.

## Run

```powershell
.\venv\Scripts\activate
pip install -r requirements.txt
python download_images.py
streamlit run app.py
```

`download_images.py` searches Wikimedia Commons/Wikipedia for **place-specific** images and stores them under `data/images/`. It never intentionally assigns a generic category photo to a different venue.

If a place has no sufficiently strong source match, it is listed in `data/image_report.csv` as unresolved rather than receiving an unrelated image.

## Project structure

- `app.py` — premium UI
- `recommender.py` — semantic + weather + popularity ranking
- `download_images.py` — builds the 200+ place image library
- `data/mumbai_places.csv` — 222-place Mumbai dataset
- `data/images/` — downloaded place-specific photos
- `data/image_sources.json` — image source manifest


Current-data note: Pali Village Cafe was replaced by Pali Bhavan because Pali Village Cafe is reported permanently closed in 2026; Pali Bhavan reopened at Churchgate.
