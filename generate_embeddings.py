from pathlib import Path
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

DATA=Path('data/mumbai_places.csv'); OUT=Path('data/place_embeddings.npy')
df=pd.read_csv(DATA)
cols=['name','description','category_tags','primary_category','area','indoor_outdoor']
texts=df[cols].fillna('').astype(str).agg(' | '.join,axis=1).tolist()
model=SentenceTransformer('all-MiniLM-L6-v2')
emb=model.encode(texts,normalize_embeddings=True,show_progress_bar=True)
OUT.parent.mkdir(parents=True,exist_ok=True); np.save(OUT,emb)
print(f'Saved {emb.shape} to {OUT}')
