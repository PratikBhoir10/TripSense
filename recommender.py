import os
from pathlib import Path

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


# ============================================================
# TripSense — Mumbai recommender
#
# Rules:
#   1. Area is a HARD filter.
#   2. Interest/category is a HARD filter for direct matches.
#   3. Weather changes ranking; it does not replace the interest.
#   4. Rainy alternatives are separate recommendation types.
#   5. If the selected area has no places for the selected interest,
#      return an empty DataFrame instead of falling back or crashing.
# ============================================================

DATA_PATH = Path("data/mumbai_places.csv")
EMBEDDING_PATH = Path("data/place_embeddings.npy")
MODEL_NAME = "all-MiniLM-L6-v2"

ANY_AREA = "Anywhere in Mumbai"

RESULT_COLUMNS = [
    "place_id",
    "name",
    "description",
    "category_tags",
    "indoor_outdoor",
    "budget_level",
    "duration_hours",
    "latitude",
    "longitude",
    "primary_category",
    "area",
    "popularity_score",
    "review_count",
    "rain_suitability",
    "sunny_suitability",
    "similarity_score",
    "weather_score",
    "adjusted_score",
    "reason",
    "recommendation_type",
]


# ============================================================
# INTEREST -> PRIMARY CATEGORY
# ============================================================

INTEREST_MAP = {
    "religious": "Religious",
    "nature": "Nature",
    "heritage": "Heritage",
    "food": "Food",
    "beach": "Beach",
    "wildlife": "Wildlife",
    "shopping": "Shopping",
    "nightlife": "Nightlife",
    "entertainment": "Entertainment",
    "museum": "Museum",
    "scenic": "Scenic",
    "sports": "Sports",
    "art": "Art",
}


INTEREST_QUERIES = {
    "religious": (
        "religious spiritual places, temples, churches, mosques, "
        "dargahs, places of worship, prayer and devotion"
    ),
    "nature": (
        "nature, greenery, gardens, parks, lakes, forests, "
        "peaceful outdoor places and natural landscapes"
    ),
    "heritage": (
        "heritage, historical places, forts, monuments, historic "
        "landmarks, architecture and cultural sites"
    ),
    "food": (
        "food, restaurants, street food, local cuisine, cafes, "
        "bakeries, food streets and Mumbai culinary experiences"
    ),
    "beach": (
        "beaches, seashores, coastline, sea, waterfront, "
        "sunset and relaxing coastal places"
    ),
    "wildlife": (
        "wildlife, animals, zoo, national parks, forests, birds, "
        "nature reserves and animal experiences"
    ),
    "shopping": (
        "shopping, markets, bazaars, malls, street shopping, "
        "fashion, local markets and retail destinations"
    ),
    "nightlife": (
        "nightlife, bars, pubs, clubs, lounges, music, evening "
        "entertainment and late night experiences"
    ),
    "entertainment": (
        "entertainment, theatre, cinema, performing arts, shows, "
        "amusement and cultural entertainment"
    ),
    "museum": (
        "museums, galleries, exhibitions, art, history, science "
        "and indoor cultural collections"
    ),
    "scenic": (
        "scenic viewpoints, promenades, skyline, sea views, "
        "sunsets, photography and city landscapes"
    ),
    "sports": (
        "sports, stadiums, sporting venues, recreation and active "
        "outdoor or indoor activities"
    ),
    "art": (
        "art galleries, contemporary art, exhibitions, artists, "
        "creative spaces and visual culture"
    ),
}


# Only categories that have a sensible rainy-day substitute.
# These are alternatives, NOT replacements for the user's interest.
RAIN_ALTERNATIVES = {
    "Beach": {
        "categories": ["Museum", "Entertainment", "Food", "Shopping"],
        "query": (
            "indoor Mumbai attractions, museums, science, cinema, "
            "entertainment, food and indoor experiences suitable for rain"
        ),
    },
    "Nature": {
        "categories": ["Museum", "Entertainment", "Food"],
        "query": (
            "indoor Mumbai experiences related to nature, science, "
            "environment, culture and exploration suitable for rain"
        ),
    },
    "Wildlife": {
        "categories": ["Museum", "Entertainment"],
        "query": (
            "indoor Mumbai experiences related to animals, nature, "
            "science, environment and exploration suitable for rain"
        ),
    },
    "Scenic": {
        "categories": ["Museum", "Entertainment", "Shopping"],
        "query": (
            "indoor Mumbai attractions, culture, architecture, "
            "entertainment and interesting city experiences suitable for rain"
        ),
    },
    "Heritage": {
        "categories": ["Museum", "Entertainment", "Food"],
        "query": (
            "indoor Mumbai heritage, history, architecture, museums, "
            "culture and entertainment suitable for rainy weather"
        ),
    },
}


def _empty_results():
    """Return a stable empty result with every column the UI may need."""
    return pd.DataFrame(columns=RESULT_COLUMNS)


def _normalise(value):
    return " ".join(str(value).strip().casefold().split())


def _ensure_columns(data):
    """Add optional columns when an older dataset does not contain them."""
    data = data.copy()

    defaults = {
        "place_id": "",
        "description": "",
        "category_tags": "",
        "indoor_outdoor": "",
        "budget_level": "",
        "duration_hours": np.nan,
        "latitude": np.nan,
        "longitude": np.nan,
        "area": "",
        "popularity_score": 0,
        "review_count": 0,
        "rain_suitability": 0,
        "sunny_suitability": 0,
    }

    for column, default in defaults.items():
        if column not in data.columns:
            data[column] = default

    required = ["name", "primary_category"]
    missing = [c for c in required if c not in data.columns]
    if missing:
        raise ValueError(
            "Dataset is missing required columns: " + ", ".join(missing)
        )

    for column in [
        "popularity_score",
        "review_count",
        "rain_suitability",
        "sunny_suitability",
        "duration_hours",
        "latitude",
        "longitude",
    ]:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    data["popularity_score"] = data["popularity_score"].fillna(0)
    data["review_count"] = data["review_count"].fillna(0)
    data["rain_suitability"] = data["rain_suitability"].fillna(0).clip(0, 5)
    data["sunny_suitability"] = data["sunny_suitability"].fillna(0).clip(0, 5)

    return data


def _build_embedding_text(row):
    return (
        f"Name: {row.get('name', '')}. "
        f"Description: {row.get('description', '')}. "
        f"Category: {row.get('primary_category', '')}. "
        f"Tags: {row.get('category_tags', '')}. "
        f"Area: {row.get('area', '')}. "
        f"Environment: {row.get('indoor_outdoor', '')}."
    )


# ============================================================
# LOAD DATA + EMBEDDINGS
# ============================================================

if not DATA_PATH.exists():
    raise FileNotFoundError(
        f"Could not find {DATA_PATH}. Run the app from the TripSense project folder."
    )

df = _ensure_columns(pd.read_csv(DATA_PATH))

# Keep one row per place where possible. Do not silently change the
# user's dataset ordering beyond removing exact duplicate rows.
df = df.drop_duplicates(subset=["name"], keep="first").reset_index(drop=True)

model = SentenceTransformer(MODEL_NAME)


def _load_or_build_embeddings():
    texts = [_build_embedding_text(row) for _, row in df.iterrows()]

    needs_rebuild = True
    embeddings = None

    if EMBEDDING_PATH.exists():
        try:
            embeddings = np.load(EMBEDDING_PATH)
            needs_rebuild = (
                embeddings.ndim != 2
                or embeddings.shape[0] != len(df)
            )
        except Exception:
            needs_rebuild = True

    if needs_rebuild:
        EMBEDDING_PATH.parent.mkdir(parents=True, exist_ok=True)
        embeddings = model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        np.save(EMBEDDING_PATH, embeddings)

    return np.asarray(embeddings)


place_embeddings = _load_or_build_embeddings()


# ============================================================
# FILTERS
# ============================================================

def _filter_area(data, area):
    """Exact area filter. Never substitute another locality."""
    if not area or _normalise(area) == _normalise(ANY_AREA):
        return data.copy()

    if "area" not in data.columns:
        return data.iloc[0:0].copy()

    wanted = _normalise(area)
    mask = data["area"].map(_normalise) == wanted
    return data.loc[mask].copy()


def _category_mask(data, category):
    return (
        data["primary_category"]
        .astype(str)
        .str.strip()
        .str.casefold()
        == category.casefold()
    )


# ============================================================
# SCORING
# ============================================================

def get_weather_score(row, weather):
    if weather == "Rainy":
        return float(row["rain_suitability"]) / 5.0
    if weather == "Sunny":
        return float(row["sunny_suitability"]) / 5.0
    return 1.0


def _popularity_score(series):
    """
    Convert popularity to 0..1 without letting one anomalous value
    dominate the ranking.
    """
    values = pd.to_numeric(series, errors="coerce").fillna(0.0)

    # Expected dataset scale is 0..10. If the source uses another
    # scale, min-max keeps the ranking meaningful.
    if values.max() <= 10 and values.min() >= 0:
        return (values / 10.0).clip(0, 1)

    low, high = values.min(), values.max()
    if high <= low:
        return pd.Series(0.5, index=values.index)

    return ((values - low) / (high - low)).clip(0, 1)


def calculate_scores(candidate_df, candidate_indices, semantic_query, weather):
    if candidate_df.empty:
        return _empty_results()

    embeddings = place_embeddings[np.asarray(candidate_indices)]

    query_embedding = model.encode(
        [semantic_query],
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    similarities = cosine_similarity(
        query_embedding,
        embeddings,
    )[0]

    results = candidate_df.copy()
    results["similarity_score"] = similarities
    results["weather_score"] = results.apply(
        lambda row: get_weather_score(row, weather),
        axis=1,
    )

    results["popularity_normalized"] = _popularity_score(
        results["popularity_score"]
    )

    if weather in ("Rainy", "Sunny"):
        # Weather influences ranking, but semantic relevance remains
        # the dominant signal.
        results["adjusted_score"] = (
            0.60 * results["similarity_score"]
            + 0.25 * results["weather_score"]
            + 0.15 * results["popularity_normalized"]
        )
    else:
        results["adjusted_score"] = (
            0.75 * results["similarity_score"]
            + 0.25 * results["popularity_normalized"]
        )

    return results


# ============================================================
# EXPLANATIONS
# ============================================================

def direct_reason(row, user_interest, weather):
    category = str(row["primary_category"]).lower()

    if weather == "Rainy":
        suitability = float(row["rain_suitability"])
        if suitability >= 4:
            return (
                f"Direct {category} match for your {user_interest.lower()} "
                "interest, with good rainy-weather suitability."
            )
        if suitability <= 2:
            return (
                f"Direct {category} match for your {user_interest.lower()} "
                "interest. It is less suitable in rain, so check conditions."
            )
        return (
            f"Direct {category} match for your {user_interest.lower()} "
            "interest, with moderate rainy-weather suitability."
        )

    if weather == "Sunny":
        suitability = float(row["sunny_suitability"])
        if suitability >= 4:
            return (
                f"Direct {category} match for your {user_interest.lower()} "
                "interest, with good sunny-weather suitability."
            )
        if suitability <= 2:
            return (
                f"Direct {category} match for your {user_interest.lower()} "
                "interest. Sunny conditions are less suitable here."
            )
        return (
            f"Direct {category} match for your {user_interest.lower()} "
            "interest, with moderate sunny-weather suitability."
        )

    return (
        f"Direct {category} match for your {user_interest.lower()} interest."
    )


def alternative_reason(row, user_interest):
    return (
        f"Rainy-weather alternative to {user_interest.lower()}: "
        "an indoor experience that is more suitable when outdoor conditions "
        "are poor."
    )


def _finalise(results):
    if results is None or results.empty:
        return _empty_results()

    for column in RESULT_COLUMNS:
        if column not in results.columns:
            results[column] = np.nan

    return results[RESULT_COLUMNS].reset_index(drop=True)


# ============================================================
# MAIN RECOMMENDER
# ============================================================

def get_recommendations(
    user_interests,
    weather="Any",
    top_k=8,
    area=ANY_AREA,
):
    """
    Return recommendations for the selected interest, weather and area.

    Important behavior:
      - Interest is a hard requirement for direct matches.
      - Area is a hard requirement.
      - No cross-area fallback.
      - If direct matches do not exist in the selected area, return empty.
      - Rainy alternatives are only added when direct matches exist.
      - Alternatives remain inside the selected area.
    """
    interest = _normalise(user_interests)
    weather = str(weather).strip().title()

    if weather not in {"Any", "Rainy", "Sunny"}:
        weather = "Any"

    category = INTEREST_MAP.get(interest)
    if category is None:
        return _empty_results()

    try:
        top_k = max(1, int(top_k))
    except (TypeError, ValueError):
        top_k = 8

    # --------------------------------------------------------
    # 1. HARD AREA FILTER
    # --------------------------------------------------------
    area_df = _filter_area(df, area)

    if area_df.empty:
        return _empty_results()

    area_indices = area_df.index.to_numpy()

    # --------------------------------------------------------
    # 2. HARD INTEREST/CATEGORY FILTER
    # --------------------------------------------------------
    direct_mask = _category_mask(area_df, category)
    direct_df = area_df.loc[direct_mask].copy()

    # This is the critical empty-result guard.
    # Never call sort_values("adjusted_score") on an unscored empty frame.
    if direct_df.empty:
        return _empty_results()

    direct_indices = direct_df.index.to_numpy()

    # --------------------------------------------------------
    # 3. SEMANTIC + WEATHER + POPULARITY RANKING
    # --------------------------------------------------------
    direct_results = calculate_scores(
        direct_df,
        direct_indices,
        INTEREST_QUERIES[interest],
        weather,
    )

    if direct_results.empty:
        return _empty_results()

    direct_results["recommendation_type"] = "Direct match"
    direct_results["reason"] = direct_results.apply(
        lambda row: direct_reason(row, user_interests, weather),
        axis=1,
    )

    direct_results = (
        direct_results
        .sort_values(
            ["adjusted_score", "popularity_score"],
            ascending=[False, False],
        )
        .reset_index(drop=True)
    )

    # --------------------------------------------------------
    # 4. SUNNY / ANY = DIRECT RESULTS ONLY
    # --------------------------------------------------------
    if weather != "Rainy":
        return _finalise(direct_results.head(top_k))

    # --------------------------------------------------------
    # 5. RAINY = DIRECT RESULTS FIRST
    # --------------------------------------------------------
    alternative_config = RAIN_ALTERNATIVES.get(category)

    # No alternative mapping for this interest:
    # simply return direct matches.
    if alternative_config is None:
        return _finalise(direct_results.head(top_k))

    direct_count = min(len(direct_results), max(3, int(np.ceil(top_k * 0.60))))
    direct_top = direct_results.head(direct_count).copy()

    # --------------------------------------------------------
    # 6. RAINY ALTERNATIVES WITHIN THE SAME AREA ONLY
    # --------------------------------------------------------
    remaining = top_k - len(direct_top)

    if remaining <= 0:
        return _finalise(direct_top)

    alternative_mask = area_df["primary_category"].isin(
        alternative_config["categories"]
    )

    alternative_mask &= (
        pd.to_numeric(
            area_df["rain_suitability"],
            errors="coerce",
        ).fillna(0) >= 4
    )

    alternative_df = area_df.loc[alternative_mask].copy()

    if alternative_df.empty:
        return _finalise(direct_top)

    alternative_indices = alternative_df.index.to_numpy()

    alternative_results = calculate_scores(
        alternative_df,
        alternative_indices,
        alternative_config["query"],
        "Rainy",
    )

    if alternative_results.empty:
        return _finalise(direct_top)

    alternative_results["recommendation_type"] = (
        "Weather-friendly alternative"
    )
    alternative_results["reason"] = alternative_results.apply(
        lambda row: alternative_reason(row, user_interests),
        axis=1,
    )

    alternative_results = (
        alternative_results
        .sort_values(
            ["adjusted_score", "popularity_score"],
            ascending=[False, False],
        )
        .head(remaining)
    )

    return _finalise(
        pd.concat(
            [direct_top, alternative_results],
            ignore_index=True,
        )
    )


# ============================================================
# OPTIONAL HELPERS FOR THE UI
# ============================================================

def get_available_count(user_interests, area=ANY_AREA):
    """Number of direct-interest places available in the selected area."""
    interest = _normalise(user_interests)
    category = INTEREST_MAP.get(interest)

    if category is None:
        return 0

    area_df = _filter_area(df, area)
    if area_df.empty:
        return 0

    return int(_category_mask(area_df, category).sum())


def get_areas():
    """Return sorted area names for the UI."""
    if "area" not in df.columns:
        return [ANY_AREA]

    areas = (
        df["area"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    areas = sorted(
        [x for x in areas.unique() if x],
        key=str.casefold,
    )

    return [ANY_AREA] + areas


if __name__ == "__main__":
    print(f"Loaded {len(df)} places.")
    print(f"Areas available: {len(get_areas()) - 1}")

    tests = [
        ("Beach", "Sunny", ANY_AREA),
        ("Beach", "Rainy", ANY_AREA),
        ("Food", "Rainy", ANY_AREA),
        ("Religious", "Rainy", ANY_AREA),
        # This should return EMPTY if Matunga has no Beach rows.
        ("Beach", "Rainy", "Matunga"),
    ]

    for interest, weather, area in tests:
        result = get_recommendations(
            interest,
            weather=weather,
            area=area,
            top_k=8,
        )

        print(
            f"\n{interest} | {weather} | {area} "
            f"-> {len(result)} result(s)"
        )

        if result.empty:
            print("NO PLACES FOUND")
        else:
            print(
                result[
                    ["name", "primary_category", "area", "recommendation_type"]
                ].to_string(index=False)
            )

def get_dataset_stats():
    places = int(len(df))
    categories = []
    if "primary_category" in df.columns:
        vals = df["primary_category"].dropna().astype(str).str.strip()
        categories = sorted([v for v in vals.unique() if v], key=str.casefold)
    area_count = 0
    if "area" in df.columns:
        vals = df["area"].dropna().astype(str).str.strip()
        area_count = len([v for v in vals.unique() if v])
    return {"places": places, "total_places": places, "categories": categories,
            "category_count": len(categories), "total_categories": len(categories),
            "area_count": area_count, "total_areas": area_count}
