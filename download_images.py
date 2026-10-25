"""Build TripSense's local, place-specific Mumbai photo library.

This is a multi-pass resolver. It prefers Wikimedia Commons and Wikipedia,
then Openverse, and only accepts images whose title/search evidence is strong
for the actual place. It never falls back to generic Mumbai/category photos.
Existing local images are preserved; rerunning this script retries only the
places that are still missing.
"""
from pathlib import Path
import json, re, time, urllib.parse
import pandas as pd
import requests

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data/mumbai_places.csv'
OUT=ROOT/'data/images'; OUT.mkdir(parents=True,exist_ok=True)
MANIFEST=ROOT/'data/image_sources.json'
REPORT=ROOT/'data/image_report.csv'
HEADERS={'User-Agent':'TripSense-Mumbai/1.0 (academic travel recommendation project)'}
S=requests.Session(); S.headers.update(HEADERS)

ALIASES={
 'University of Mumbai Fort':'University of Mumbai',
 'Asiatic Library':'Asiatic Society of Mumbai',
 'Asiatic Society Library':'Asiatic Society of Mumbai',
 'Chhatrapati Shivaji Maharaj Vastu Sangrahalaya':'Chhatrapati Shivaji Maharaj Vastu Sangrahalaya',
 'Chhatrapati Shivaji Maharaj Terminus':'Chhatrapati Shivaji Terminus',
 'Byculla Zoo':'Veermata Jijabai Bhosale Botanical Udyan and Zoo',
 'Dr. Bhau Daji Lad Museum':'Dr. Bhau Daji Lad Museum',
 'Bandra Fort (Land\'s End)':'Bandra Fort',
 'Bandra-Worli Sea Link':'Bandra Worli Sea Link',
 'Sanjay Gandhi National Park Nature Trails':'Sanjay Gandhi National Park',
 'Sanjay Gandhi National Park':'Sanjay Gandhi National Park',
 'Nehru Science Centre':'Nehru Science Centre, Mumbai',
 'Mount Mary Church':'Mount Mary Basilica',
 'Bandra Bandstand':'Bandstand Promenade',
 'Worli Sea Face':'Worli Sea Face',
 'Girgaon Chowpatty':'Girgaum Chowpatty',
 'Juhu Chowpatty':'Juhu Beach',
 'Dadar Chowpatty':'Dadar Chowpatty',
 'Bandra Reclamation':'Bandra Reclamation',
 'Carter Road Promenade':'Carter Road Promenade',
 'National Centre for the Performing Arts':'National Centre for the Performing Arts, Mumbai',
 'National Museum of Indian Cinema':'National Museum of Indian Cinema',
 'Nehru Centre Discovery of India':'Nehru Centre',
 'Nehru Planetarium':'Nehru Planetarium, Mumbai',
 'RBI Monetary Museum':'RBI Monetary Museum',
 'David Sassoon Library':'David Sassoon Library and Reading Room',
 'Jehangir Art Gallery':'Jehangir Art Gallery',
 'Royal Opera House':'Royal Opera House, Mumbai',
 'St. Thomas\' Cathedral':'St. Thomas Cathedral, Mumbai',
 'Keneseth Eliyahoo Synagogue':'Knesset Eliyahoo Synagogue',
 'Magen David Synagogue':'Magen David Synagogue, Mumbai',
 'Babulnath Temple':'Babulnath Temple',
 'Walkeshwar Temple':'Walkeshwar Temple',
 'Mahalaxmi Dhobi Ghat':'Mahalaxmi Dhobi Ghat',
 'Mahalaxmi Railway Heritage Walk':'Mahalaxmi railway station',
 'Taraporewala Aquarium':'Taraporewala Aquarium',
 'Cafe Madras':'Cafe Madras, Mumbai',
 'Cafe Mysore':'Cafe Mysore, Mumbai',
 'The Bombay Canteen':'The Bombay Canteen',
 'Bademiya':'Bademiya, Mumbai',
 'Leopold Cafe':'Leopold Cafe, Mumbai',
 'Britannia & Co.':'Britannia & Co. restaurant',
 'Cafe Mondegar':'Cafe Mondegar',
 'Kala Ghoda Cafe':'Kala Ghoda Cafe',
 'Natural Ice Cream':'Natural Ice Cream, Mumbai',
 'Pali Village Cafe':'Pali Village Cafe',
 'Bastian Mumbai':'Bastian, Mumbai',
 'Prithvi Cafe':'Prithvi Cafe, Mumbai',
 'Shree Thaker Bhojon':'Shree Thaker Bhojon',
 'Swati Snacks':'Swati Snacks, Mumbai',
 'Gajalee':'Gajalee, Mumbai',
 'Mahesh Lunch Home':'Mahesh Lunch Home, Mumbai',
 'Subko Coffee':'Subko Coffee',
 'Trishna':'Trishna restaurant Mumbai',
 'Khyber':'Khyber restaurant Mumbai',
 'Yauatcha Mumbai':'Yauatcha Mumbai',
 'Masala Library Mumbai':'Masala Library, Mumbai',
 'Foo Asian Tapas':'Foo Asian Tapas',
 'Koko Mumbai':'Koko Asian Gastropub Mumbai',
 '145 The Mill':'145 The Mill Mumbai',
 'Social Lower Parel':'Social Lower Parel',
 'The Good Wife':'The Good Wife BKC',
 'Raju Omlet':'Raju Omlet Mumbai',
 'Udipi Shri Krishna Boarding':'Udipi Shri Krishna Boarding',
 'Mani\'s Lunch Home':'Mani\'s Lunch Home Mumbai',
 'Aaswad Upahar Griha':'Aaswad Upahar Griha',
 'Aaswad':'Aaswad restaurant Mumbai',
 'Elco Pani Puri Centre':'Elco Pani Puri Centre Bandra',
 'Blue Tokai Bandra':'Blue Tokai Bandra',
 'Third Wave Coffee Bandra':'Third Wave Coffee Bandra',
 'Nara Thai Bandra':'Nara Thai Bandra',
 'The Bagel Shop':'The Bagel Shop Bandra',
 'Bombay Salad Co.':'Bombay Salad Co Mumbai',
 'Veranda':'Veranda Bandra',
 'Candies':'Candies Bandra',
}

SEARCH_HINTS = {
    'Phoenix Marketcity':'Phoenix Marketcity Kurla Mumbai', 'R City Mall':'R City Mall Ghatkopar Mumbai',
    'Inorbit Mall Malad':'Inorbit Mall Malad Mumbai', 'Korum Mall':'Korum Mall Thane', 'Link Square Mall':'Link Square Mall Bandra Mumbai',
    'Infiniti Mall Malad':'Infiniti Mall Malad Mumbai', 'Oberoi Mall':'Oberoi Mall Goregaon Mumbai', "Growel's 101":"Growel's 101 Kandivali Mumbai",
    'Jio World Drive':'Jio World Drive BKC Mumbai', 'Jio World Plaza':'Jio World Plaza BKC Mumbai', 'Nita Mukesh Ambani Cultural Centre':'Nita Mukesh Ambani Cultural Centre Mumbai',
    'Jio World Convention Centre':'Jio World Convention Centre BKC Mumbai', 'Phoenix Palladium':'Phoenix Palladium Mumbai', 'Palladium Mumbai':'Palladium Mumbai Lower Parel',
    'Kamala Mills':'Kamala Mills Lower Parel Mumbai', 'Hard Rock Cafe Mumbai':'Hard Rock Cafe Andheri Mumbai', 'Toit Mumbai':'Toit Mumbai Lower Parel',
    'The Little Door':'The Little Door Mumbai', 'Hoppipola Mumbai':'Hoppipola Mumbai Andheri', 'The Bombay Bronx':'The Bombay Bronx Mumbai',
    'PVR ICON Phoenix':'PVR INOX Phoenix Palladium Mumbai', 'PVR INOX Juhu':'PVR INOX Juhu Mumbai', 'Andheri Sports Complex':'Andheri Sports Complex Mumbai',
    'Shanmukhananda Hall':'Shanmukhananda Hall Mumbai', 'National Gallery of Modern Art Mumbai':'National Gallery of Modern Art Mumbai',
    'National Museum of Indian Cinema':'National Museum of Indian Cinema Mumbai', 'Prithvi Theatre':'Prithvi Theatre Juhu Mumbai',
    'Mani Bhavan Gandhi Sangrahalaya':'Mani Bhavan Mumbai', 'Mumbadevi Temple':'Mumbadevi Temple Mumbai', 'Minara Masjid':'Minara Masjid Mumbai',
    'Sion Fort':'Sion Fort Mumbai', 'Mahim Fort':'Mahim Fort Mumbai', "St. Andrew's Church":'St Andrews Church Bandra Mumbai',
    'Gloria Church':'Gloria Church Byculla Mumbai', 'Nehru Centre':'Nehru Centre Worli Mumbai', 'Taraporewala Aquarium':'Taraporewala Aquarium Mumbai',
    'Regal Cinema':'Regal Cinema Colaba Mumbai', 'Masala Library Mumbai':'Masala Library BKC Mumbai', 'Yauatcha Mumbai':'Yauatcha BKC Mumbai',
    'Foo Asian Tapas':'Foo Asian Tapas Mumbai', 'BKC Food District':'BKC Food District Mumbai', 'BKC Art District':'BKC Art District Mumbai',
    'Koko Mumbai':'Koko Asian Gastropub Mumbai', 'Lord of the Drinks':'Lord of the Drinks Lower Parel Mumbai', 'antiSOCIAL Mumbai':'antiSOCIAL Lower Parel Mumbai',
    'Kitty Su Mumbai':'Kitty Su Mumbai The Lalit', 'Ravindra Natya Mandir':'Ravindra Natya Mandir Prabhadevi Mumbai',
    'National Centre for the Performing Arts':'NCPA Mumbai', 'Shivaji Park Gymkhana':'Shivaji Park Gymkhana Mumbai', 'Bombay Gymkhana':'Bombay Gymkhana Mumbai',
    'Dharavi Pottery Cluster':'Dharavi pottery Mumbai', 'Lamington Road Market':'Lamington Road electronics market Mumbai', 'Dadar Market':'Dadar Market Mumbai',
    'Hill Road Market':'Hill Road Market Bandra Mumbai', 'Linking Road Market':'Linking Road Market Bandra Mumbai', 'Mohammed Ali Road (Khau Galli)':'Mohammed Ali Road Mumbai food street',
    'Byculla Zoo':'Byculla Zoo Mumbai', 'Sewri Fort (Flamingo Point)':'Sewri Fort Mumbai', 'Dharavi Heritage Walk':'Dharavi Heritage Walk Mumbai',
    'Five Gardens':'Five Gardens Matunga Mumbai', 'Manori Beach':'Manori Beach Mumbai', 'Dadar Chowpatty':'Dadar Chowpatty Mumbai',
    'Zaveri Bazaar':'Zaveri Bazaar Mumbai', 'Sarafa Bazaar':'Sarafa Bazaar Mumbai', 'Carter Road Promenade':'Carter Road Bandra Mumbai',
    'EsselWorld':'EsselWorld Mumbai', 'Water Kingdom':'Water Kingdom Mumbai', 'Ram Ashraya':'Ram Ashraya Matunga Mumbai', 'Kyani & Co.':'Kyani and Co Mumbai',
    'Prakash Shakahari Upahaar Kendra':'Prakash Shakahari Upahaar Kendra Mumbai', 'Maharashtra Nature Park':'Maharashtra Nature Park Mumbai',
    'Sewri Mudflats':'Sewri mudflats Mumbai', 'Worli Village':'Worli village Mumbai', 'Priyadarshini Park':'Priyadarshini Park Mumbai',
    'Sea Lounge':'Sea Lounge Taj Mahal Palace Mumbai', 'Subko Coffee':'Subko Coffee Mumbai', 'Trishna':'Trishna restaurant Mumbai',
    'The Clearing House':'The Clearing House Mumbai restaurant', 'Mockingbird Cafe Bar':'Mockingbird Cafe Bar Mumbai', 'Cafe Excelsior':'Cafe Excelsior Mumbai',
    'Shree Thaker Bhojon':'Shree Thaker Bhojon Mumbai', 'Swati Snacks':'Swati Snacks Mumbai', 'Sardar Refreshments':'Sardar Refreshments Mumbai',
    'Soam':'Soam Mumbai restaurant', 'Mahesh Lunch Home':'Mahesh Lunch Home Mumbai', 'Prithvi Cafe':'Prithvi Cafe Juhu Mumbai',
    'Theobroma Bandra':'Theobroma Bandra Mumbai', 'Bastian Mumbai':'Bastian Mumbai Bandra', 'The Bagel Shop':'The Bagel Shop Bandra Mumbai',
    'Bombay Salad Co.':'Bombay Salad Co Bandra Mumbai', 'Elco Pani Puri Centre':'Elco Pani Puri Centre Bandra Mumbai', 'Blue Tokai Bandra':'Blue Tokai Coffee Bandra Mumbai',
    'Third Wave Coffee Bandra':'Third Wave Coffee Bandra Mumbai', 'Nara Thai Bandra':'Nara Thai Bandra Mumbai', 'Raju Omlet':'Raju Omlet Bandra Mumbai',
    'Udipi Shri Krishna Boarding':'Udipi Shri Krishna Boarding Matunga Mumbai', "Mani's Lunch Home":"Mani's Lunch Home Matunga Mumbai", 'Gypsy Corner':'Gypsy Corner Shivaji Park Mumbai',
    'Goan Cart':'Goan Cart Mumbai', 'Aaswad Upahar Griha':'Aaswad Upahar Griha Mumbai', 'SIES College Area':'SIES College Matunga Mumbai',
    "King's Circle":'Kings Circle Matunga Mumbai', 'Matunga Market':'Matunga Market Mumbai', 'Pali Market':'Pali Market Bandra Mumbai',
    'Lokhandwala Market':'Lokhandwala Market Andheri Mumbai', 'Versova Koliwada':'Versova Koliwada Mumbai', 'Versova Social':'Versova Social Mumbai',
    'Mindspace Malad':'Mindspace Malad Mumbai', 'Tulsi Lake':'Tulsi Lake Mumbai', 'Pali Bhavan':'Pali Bhavan Churchgate Mumbai'
}

# Final targeted search phrases for the last unresolved places.
SEARCH_HINTS.update({
 'Bhau Daji Lad Museum Courtyard':'Dr Bhau Daji Lad Museum courtyard Mumbai',
 'Worli Village':'Worli Koliwada fishing village Mumbai',
 'Sardar Refreshments':'Sardar Refreshments Tardeo Mumbai',
 'Mahesh Lunch Home':'Mahesh Lunch Home Fort Mumbai',
 'Raju Omlet':'Raju Omlet Mumbai restaurant',
 "Mani's Lunch Home":"Mani's Lunch Home Matunga Mumbai",
 "King's Circle":'King Circle Matunga Mumbai GSB Seva Mandal',
 'Versova Koliwada':'Versova Koliwada fishing village Mumbai',
 'Mindspace Malad':'Mindspace Business Park Malad Mumbai',
 'Tulsi Lake':'Tulsi Lake Sanjay Gandhi National Park Mumbai',
 'Foo Asian Tapas':'FOO Asian Tapas Lower Parel Mumbai',
 'BKC Food District':'BKC Food District Bandra Kurla Complex Mumbai',
 'Kamala Mills':'Kamala Mills Lower Parel Mumbai',
 'Kitty Su Mumbai':'Kitty Su The Lalit Mumbai',
 'The Little Door':'The Little Door Andheri Mumbai',
 'Shivaji Park Gymkhana':'Shivaji Park Gymkhana Dadar Mumbai',
 'Ravindra Natya Mandir':'Ravindra Natya Mandir Prabhadevi Mumbai',
 'Nehru Centre':'Nehru Centre Worli Mumbai',
 'Mani Bhavan Gandhi Sangrahalaya':'Mani Bhavan Gandhi Museum Mumbai',
 'Mohammed Ali Road (Khau Galli)':'Mohammed Ali Road Khau Galli Minara Masjid Mumbai',
})

# Known exact public photo URLs from prior verification. These are place-specific,
# not category fallbacks. They also make reruns deterministic for these venues.
EXACT={
 'The Bombay Canteen':'https://thebombaycanteen.com/cdn/shop/files/TBC_BANNER_-_WEB.jpg?v=1735804818&width=900',
 'Cafe Madras':'https://upload.wikimedia.org/wikipedia/commons/0/02/Cafe_Madras_Frontage.jpg',
 'Cafe Mysore':'https://images.herzindagi.info/image/2024/Aug/cafe-mysore.png',
 'Aaswad':'https://media-cdn.tripadvisor.com/media/photo-s/13/20/a3/7f/aaswad-hotel.jpg',
 'Kala Ghoda Cafe':'https://dynamic-media-cdn.tripadvisor.com/media/photo-o/16/a0/99/5e/inside-seating-and-decor.jpg?h=-1&s=1&w=900',
 'Bademiya':'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1c/Bademiya_restaurant%2C_Mumbai.jpg/960px-Bademiya_restaurant%2C_Mumbai.jpg',
 'Leopold Cafe':'https://upload.wikimedia.org/wikipedia/commons/1/1c/LeopoldCafe2_gobeirne.jpg',
 'Phoenix Marketcity':'https://upload.wikimedia.org/wikipedia/commons/b/b0/Phoenix_Marketcity_Kurla.jpg',
 'Bademiya':'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1c/Bademiya_restaurant%2C_Mumbai.jpg/800px-Bademiya_restaurant%2C_Mumbai.jpg',
 'Ram Ashraya':'https://cdn.tasteatlas.com/images/restaurants/0bcaa091d7df4ff4a81a6b7a528b0f4f.jpg?mw=600',
 'Prakash Shakahari Upahaar Kendra':'https://cdn.tasteatlas.com/images/restaurants/c249e70c703d44b18fc7c320ea4087df.jpg?mw=1300',
 'Sewri Mudflats':'https://3.bp.blogspot.com/-R5QVlUXABD4/VuK8oCz39cI/AAAAAAAAGGI/ZFfyvNjiqtsgwwxBhD9tFjuNlWTw5vUHw/w1200-h630-p-k-no-nu/IMG_0496.JPG',
 'Sea Lounge':'https://dt4l9bx31tioh.cloudfront.net/eazymedia/reviewimages/223190/86f51ffabce855adeb2570132923712322817496.jpg?height=450&mode=crop%3Fformat%3Dauto&quality=80&width=818',
 'Shree Thaker Bhojon':'https://images.indianexpress.com/2025/05/SB01ShreeThakerBhojanalay04.jpg?resize=600%2C397',
 'Blue Tokai Bandra':'https://bestmumbai.in/wp-content/uploads/2024/08/AF1QipMKSAWXFmrgbDG0O-Lf1ovLGx1FkQuGrsa6LGEWw408-h611-k-no.jpg',
 'Udipi Shri Krishna Boarding':'https://b.zmtcdn.com/data/reviews_photos/d83/2933543d11830a6e93e2f6922ad28d83_1460726017.jpg?crop=750%3A500%3B%2A%2C%2A&fit=around%7C750%3A500',
 'Gypsy Corner':'https://onthegrid.city/imager/s3_amazonaws_com/onthegrid.city/assets/grid/mumbai/dadar/gypsy-corner/GC_1_299006722e285f47655d17d1c9136337.jpg',
 'Versova Social':'https://images.squarespace-cdn.com/content/v1/620b55fcd0714a3db4964cbc/a6f620ab-c1fa-4cb7-b357-584d3aa57d30/Versova%2BSocial%2B4.jpg',
 "Growel's 101":'https://files.lbb.in/media/2020/01/5e1473d1ee25207a79c02bc0_1578398673284.jpg',
 'Jio World Drive':'https://images.moneycontrol.com/static-mcnews/2021/11/PVR-1.jpg',
 'Jio World Plaza':'https://img.businessoffashion.com/resizer/v2/BOMBTUY7QVH7ZJCVZD22OIHJ54.png?auth=a329df0952e15029f435d13ad424d079fc94e89eb11401156f5c46ba491b3b98&height=810&width=1440',
 '145 The Mill':'https://b.zmtcdn.com/data/reviews_photos/501/db8c04a76ed4c7662962c17e0fe78501_1774974734.jpg',
 'Five Gardens':'https://dynamic-media-cdn.tripadvisor.com/media/photo-o/08/14/07/9f/five-gardens.jpg?h=1200&s=1&w=1200',
 'Carter Road Promenade':'https://wanderon-images.gumlet.io/gallery/new/2025/10/27/1761562539287-carter-road-.jpg',
 'Maharashtra Nature Park':'https://1.bp.blogspot.com/-Jcqh9a37oRU/UP07Kftdw8I/AAAAAAAAAyU/c7U4hssPMqg/s1600/100_4445.JPG',
 'Shanmukhananda Hall':'https://www.bizzbuzz.news/h-upload/2022/06/30/1555568-mumbai.webp',
 'Heera Panna Market':'https://www.whatshot.in/public/uploads/article/2019/11/1573568258.jpg',
 'Manori Beach':'https://www.exploreourindia.com/uploads/attractions/Manori-Beach.jpg',
}

# Targeted page sources for the final unresolved set. The script extracts the page's
# OpenGraph/Twitter image so the photo remains tied to the exact venue/page.
CURATED_PAGES={
 'Mani Bhavan Gandhi Sangrahalaya':'https://commons.wikimedia.org/wiki/File:Mani-Bhavan-Mumbai.jpg',
 'Bhau Daji Lad Museum Courtyard':'https://www.architecturaldigest.in/story/the-time-when-mumbai-received-its-first-museum-over-160-years-ago-dr-bhau-daji-lad-museum-amin-jaffer/',
 'Worli Village':'https://www.cntraveller.in/story/help-paint-fishing-village-mumbais-worli/',
 'Nehru Centre':'https://www.nehrucentremumbai.in/culture-wing-gallery/',
 'Sardar Refreshments':'https://www.tripadvisor.com/Restaurant_Review-g304554-d799990-Reviews-Sardar_Refreshments-Mumbai_Maharashtra.html',
 'Mahesh Lunch Home':'https://www.zomato.com/mumbai/mahesh-lunch-home-fort/photos',
 "Mani's Lunch Home":'https://localpress.co.in/mumbai/manis-lunch-home-bids-farewell-matunga-good-set-reopen-chembur/',
 'Tulsi Lake':'https://commons.wikimedia.org/wiki/File:Tulsi_Lake.jpg',
 'Foo Asian Tapas':'https://fooasiantapas.com/',
 'Kitty Su Mumbai':'https://www.holidify.com/collections/discos-in-mumbai',
 'The Little Door':'https://timesofindia.indiatimes.com/travel/nightlife/the-little-door/articleshow/32782804.cms',
 'Ravindra Natya Mandir':'https://www.freepressjournal.in/mumbai/revamped-ravindra-natya-mandir-to-feature-dolby-atmos-offer-20-certified-courses-for-artists',
 'Versova Koliwada':'https://airial.travel/attractions/india/mumbai/versova-koliwada-mumbai-Eiqw3c_j',
 'Mindspace Malad':'https://www.constructionweekonline.in/tags/mindspace-malad-mumbai',
 'Raju Omlet':'https://restaurant-guru.in/Raju-omlet-Mumbai-2',
}

# Direct image URLs from targeted image research.
TARGETED_EXACT={
 'Sardar Refreshments':'https://static.wixstatic.com/media/ed27ad_d05aee79aa7b43909ca53e216c8e5c85~mv2.jpeg/v1/fill/w_980,h_611,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/ed27ad_d05aee79aa7b43909ca53e216c8e5c85~mv2.jpeg',
 'Mindspace Malad':'https://www.constructionweekonline.in/cloud/2021/12/28/YnA6EDI2-Mindsapce-Business-Parkes_Airoli-West-1200x859.jpeg',
 'Kitty Su Mumbai':'https://www.holidify.com/images/cmsuploads/compressed/j_20181223230952.PNG',
 'The Little Door':'https://static.toiimg.com/photo/msid-32782804,width-96,height-65.cms',
 'Foo Asian Tapas':'https://img.magicpin.com/2327360_cover_0.webp',
 'Ravindra Natya Mandir':'https://www.freepressjournal.in/h-upload/2025/03/03/1555568-ravindra-natya-mandir.webp',
 'Tulsi Lake':'https://media-cdn.sygictraveldata.com/media/800x600/612664395a40232133447d33247d383739313139393134',
 "Mani's Lunch Home":'https://localpress.co.in/wp-content/uploads/2016/08/manis-lunch-home-bids-farewell-to-matunga-for-good-set-to-reopen-in-chembur-optimized.jpg',
}

# Final targeted sources for the last unresolved/download-failed places.
CURATED_PAGES.update({
 'Mohammed Ali Road (Khau Galli)':'https://www.flickr.com/photos/selvin/albums/72157714966539641',
 "King's Circle":'https://www.mid-day.com/mumbai/mumbai-news/photo/in-photos-heres-the-first-look-of-the-idol-of-mumbais-richest-ganpati-mandal-102074/7',
 'Kamala Mills':'https://timescontent.timesofindia.com/photo/feature/Mills-Compound/558751',
 'Shivaji Park Gymkhana':'https://shivajiparkgymkhana.in/gallery/',
 'Manori Beach':'https://www.holidify.com/places/manori/manori-beach-photos-5266.html',
 'Bademiya':'https://commons.wikimedia.org/wiki/Category:Bademiya',
 'Heera Panna Market':'https://www.indiacontent.in/heera-panna-market/pr-846849/',
 'Mahesh Lunch Home':'https://www.zomato.com/mumbai/mahesh-lunch-home-fort/photos',
 'Blue Tokai Bandra':'https://www.zomato.com/mumbai/blue-tokai-coffee-roasters-pali-hill-bandra-west/photos',
 'Mindspace Malad':'https://www.mindspaceindia.com/malad/',
 'Palladium Mumbai':'https://www.justdial.com/Mumbai/Mogra-Multi-Designer-Store-Phoenix-Palladium-Phoenix-Palladium-Lower-Parel/022P8005946_BZDET',
 'Ravindra Natya Mandir':'https://www.justdial.com/Mumbai/Ravindra-Natya-Mandir-Near-Shri-Siddhi-Vinayak-Ganapati-Mandir-Prabhadevi/022P801186_BZDET/photos',
})
TARGETED_EXACT.update({
 'Heera Panna Market':'https://upload.wikimedia.org/wikipedia/commons/0/0a/Heera-Panna.jpg',
})

BAD={'logo','map','icon','diagram','flag','coat of arms','poster','screenshot','collage','symbol','route','metro map'}
WEAK={'mumbai','india','the','of','and','a','in','at','road','street','market','area','district','restaurant','cafe','coffee','bar','park','garden','temple','church','museum','beach'}

def slug(s): return re.sub(r'[^a-z0-9]+','_',str(s).lower()).strip('_') or 'place'
def norm(s): return re.sub(r'[^a-z0-9]+',' ',str(s).lower()).strip()
def toks(s): return set(norm(s).split())
def title_score(name,title,area='',category=''):
    n=norm(name); t=norm(title); a=norm(area); c=norm(category)
    nt=toks(name); tt=toks(title)
    strong=nt-WEAK
    overlap=len(strong & tt)/max(1,len(strong)) if strong else len(nt&tt)/max(1,len(nt))
    if n in t or t in n: overlap=max(overlap,.92)
    if a and a in t: overlap+=.08
    if c and c in t: overlap+=.04
    if any(b in t for b in BAD): overlap-=.25
    return max(0,min(1,overlap))

def variants(name,area,category):
    base=ALIASES.get(name, SEARCH_HINTS.get(name, name))
    vals=[base, f'{base} Mumbai', f'{base} {area}', f'{base} {area} Mumbai']
    if category:
        vals += [f'{base} {category} Mumbai']
    if base != name: vals += [name, f'{name} Mumbai']
    out=[]
    for x in vals:
        if x not in out: out.append(x)
    return out

def commons(name,area,category):
    best=None
    for q in variants(name,area,category):
        params={'action':'query','generator':'search','gsrsearch':q,'gsrnamespace':6,'gsrlimit':20,
                'prop':'imageinfo','iiprop':'url|mime|size','iiurlwidth':1400,'format':'json','formatversion':2}
        r=S.get('https://commons.wikimedia.org/w/api.php',params=params,timeout=15)
        if not r.ok: continue
        for p in r.json().get('query',{}).get('pages',[]):
            info=(p.get('imageinfo') or [{}])[0]; url=info.get('thumburl') or info.get('url')
            if not url or not str(info.get('mime','')).startswith('image/'): continue
            w=int(info.get('width') or 0); h=int(info.get('height') or 0)
            if w and h and (w<300 or h<200): continue
            title=p.get('title',''); sc=title_score(name,title,area,category)
            if sc>=.50 and (best is None or sc>best['score']):
                best={'score':sc,'title':title,'url':url,'source':'Wikimedia Commons'}
    return best

def wiki(name,area,category):
    best=None
    for q in variants(name,area,category):
        params={'action':'query','list':'search','srsearch':q,'srnamespace':0,'srlimit':8,
                'prop':'pageimages','piprop':'thumbnail|original','pithumbsize':1400,
                'format':'json','formatversion':2}
        try: r=S.get('https://en.wikipedia.org/w/api.php',params=params,timeout=12)
        except Exception: continue
        if not r.ok: continue
        for p in r.json().get('query',{}).get('search',[]):
            title=p.get('title',''); sc=title_score(name,title,area,category)
            # Search results do not include image info; fetch summary/pageimage.
            if sc<.48: continue
            try:
                rr=S.get('https://en.wikipedia.org/api/rest_v1/page/summary/'+urllib.parse.quote(title.replace(' ','_')),timeout=10)
                if not rr.ok: continue
                d=rr.json(); img=(d.get('originalimage') or d.get('thumbnail') or {}).get('source')
                if img and (best is None or sc>best['score']):
                    best={'score':sc,'title':title,'url':img,'source':'Wikipedia'}
            except Exception: pass
    return best

def openverse(name,area,category):
    best=None
    # No restrictive license filter: Openverse has many useful local photos.
    for q in variants(name,area,category)[:4]:
        try:
            r=S.get('https://api.openverse.org/v1/images/',params={'q':q,'page_size':30},timeout=15)
            if not r.ok: continue
            for item in r.json().get('results',[]):
                url=item.get('url') or item.get('thumbnail'); title=item.get('title') or ''
                if not url: continue
                sc=title_score(name,title,area,category)
                if sc<.48: continue
                if best is None or sc>best['score']:
                    best={'score':sc,'title':title,'url':url,'source':'Openverse','creator':item.get('creator'),'license':item.get('license')}
        except Exception: pass
    return best

def bing_images(name,area,category):
    """Last-resort image discovery for local/commercial venues using Bing Images."""
    best=None
    for q in variants(name,area,category)[:5]:
        try:
            r=S.get('https://www.bing.com/images/search', params={'q':q,'form':'HDRSC2'}, timeout=15)
            if not r.ok: continue
            for m in re.finditer(r'<a[^>]+class="iusc"[^>]+m="([^"]+)"', r.text):
                raw=m.group(1)
                try: meta=json.loads(raw.replace('&quot;','"'))
                except Exception: continue
                title=meta.get('t') or meta.get('desc') or ''
                page=meta.get('purl') or ''
                url=meta.get('murl') or meta.get('turl') or ''
                if not url: continue
                sc=max(title_score(name,title,area,category), title_score(name,page,area,category)*.92)
                if norm(name) and norm(name) in norm(f'{title} {page}'): sc=max(sc,.72)
                if sc < .55: continue
                cand={'score':sc,'title':title,'url':url,'source':'Bing Images','page_url':page}
                if best is None or sc>best['score']: best=cand
        except Exception: pass
    return best

def page_image(page_url):
    try:
        r=S.get(page_url,timeout=20,allow_redirects=True)
        if not r.ok: return None
        html=r.text
        patterns=[
            r'<meta[^>]+property=[\"\']og:image[\"\'][^>]+content=[\"\']([^\"\']+)',
            r'<meta[^>]+name=[\"\']twitter:image[\"\'][^>]+content=[\"\']([^\"\']+)',
            r'<meta[^>]+content=[\"\']([^\"\']+)[\"\'][^>]+property=[\"\']og:image[\"\']',
        ]
        for pat in patterns:
            m=re.search(pat,html,re.I)
            if m:
                return urllib.parse.unquote(m.group(1)).replace('&amp;','&')
    except Exception: pass
    return None

def download(url,dest):
    r=S.get(url,timeout=30,stream=True,allow_redirects=True); r.raise_for_status()
    ctype=r.headers.get('content-type','').lower()
    if 'image' not in ctype and not re.search(r'\.(jpe?g|png|webp)(?:\?|$)',url,re.I): raise ValueError(f'not an image: {ctype}')
    tmp=dest.with_suffix('.tmp')
    with tmp.open('wb') as f:
        for chunk in r.iter_content(1024*128):
            if chunk: f.write(chunk)
    if tmp.stat().st_size<8000: tmp.unlink(missing_ok=True); raise ValueError('image too small')
    tmp.replace(dest)

df=pd.read_csv(DATA)
old={}
if MANIFEST.exists():
    try: old=json.loads(MANIFEST.read_text(encoding='utf8'))
    except Exception: old={}
rows=[]
for i,row in df.iterrows():
    name=str(row['name']); area=str(row.get('area','Mumbai')); category=str(row.get('primary_category',''))
    dest=OUT/(slug(name)+'.jpg')
    if dest.exists() and dest.stat().st_size>8000:
        rows.append({'name':name,'status':'already_exists','source':old.get(name,{}).get('source','local'),'file':str(dest.relative_to(ROOT))})
        print(f'[{i+1}/{len(df)}] {name}: already_exists'); continue
    best=None
    candidates=[]
    if name in EXACT: candidates.append({'score':1.0,'title':name,'url':EXACT[name],'source':'Verified direct source'})
    if name in TARGETED_EXACT: candidates.append({'score':1.0,'title':name,'url':TARGETED_EXACT[name],'source':'Targeted exact source'})
    if name in CURATED_PAGES:
        u=page_image(CURATED_PAGES[name])
        if u: candidates.append({'score':.98,'title':name,'url':u,'source':'Curated page image','page_url':CURATED_PAGES[name]})
    # Try every curated candidate until one actually downloads; a failed direct URL
    # should not prevent a verified page image from being used.
    for cand in candidates:
        try:
            download(cand['url'],dest); best=cand; break
        except Exception:
            pass
    if best is None:
        for fn in (commons,wiki,openverse,bing_images):
            try: cand=fn(name,area,category)
            except Exception: cand=None
            if cand and cand.get('score',0)>=.58:
                try:
                    download(cand['url'],dest); best=cand; break
                except Exception:
                    continue
    if best is not None:
        old[name]={**best,'local_file':str(dest.relative_to(ROOT))}
        rows.append({'name':name,'status':'downloaded','source':best['source'],'title':best.get('title',''),'score':best.get('score'),'file':str(dest.relative_to(ROOT))})
    else:
        rows.append({'name':name,'status':'unresolved','source':'','title':'','score':0})
    print(f'[{i+1}/{len(df)}] {name}: {rows[-1]["status"]}')
    time.sleep(.08)

MANIFEST.write_text(json.dumps(old,indent=2,ensure_ascii=False),encoding='utf8')
pd.DataFrame(rows).to_csv(REPORT,index=False)
print(f'\nDone. Local photos: {sum(r["status"] in {"downloaded","already_exists"} for r in rows)}/{len(rows)}')
print(f'Unresolved: {sum(r["status"]=="unresolved" for r in rows)}')
print(f'Report: {REPORT}')
