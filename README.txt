TripSense — Final Image Accuracy Patch

This release combines the existing 222-place dataset/image library with the image-accuracy loader and verified overrides.

The app now:
- prioritizes verified place-specific overrides;
- blocks audited bad local images instead of showing an unrelated photo;
- uses a clean category placeholder when no verified replacement is available.

Keep the data files intact. No recommendation logic or UI behavior was changed.

Run: streamlit run app.py
