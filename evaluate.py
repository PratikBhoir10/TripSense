import pandas as pd
from recommender import get_dataset_stats, get_recommendations, INTEREST_MAP

if __name__=='__main__':
    stats=get_dataset_stats(); print('=== TripSense dataset audit ==='); print(stats)
    rows=[]
    for interest in INTEREST_MAP:
        for weather in ['Any','Sunny','Rainy']:
            r=get_recommendations(interest.title(),weather=weather,top_k=6)
            direct=r[r.recommendation_type=='Direct match']
            rows.append([interest.title(),weather,len(r),len(direct)])
    print(pd.DataFrame(rows,columns=['interest','weather','returned','direct_count']).to_string(index=False))
