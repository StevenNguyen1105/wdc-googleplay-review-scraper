#The following liabraries to be installed
#pip install flask
#pip install flask_cors
#pip install google_play_scraper
#pip install TextBlob
#pip install googletrans
#now go into python terminal and run below
#import nltk
#nltk.download('stopwords')
#nltk.download('vader_lexicon')
#nltk.download('punkt')


from flask import Flask
from flask_cors import CORS
from google_play_scraper import Sort, reviews_all
import json
import datetime
from textblob import TextBlob
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from googletrans import Translator
translator = Translator()
#for tokenization and cleanup with stopwords
import re, string
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
sw = stopwords.words('english')
#from googleplay ends
#to get the parameter from url
from flask import request

app = Flask(__name__)
CORS(app)

#to translate into english and generate sentiment analysis
def translate_gen_sa_score(text):
    #translate part
    analysis = TextBlob(text)
    eng = ""
    try:
        eng = analysis.translate(to='en')
    except Exception as e:
        try:
            if str(e) =="HTTP Error 429: Too Many Requests":
                translated_text = translator.translate(text,src='vi',dest='en')
                #print(translated_text.origin, ' -> ', translated_text.text)
                eng = translated_text.text
        except Exception as e:
            print("Again exception" + str(e))
            eng = text
            pass
    #sentiment part
    sid = SentimentIntensityAnalyzer()
    ss = sid.polarity_scores(str(eng))
    return ss['compound'], str(eng)

#generate sentiment analysis
def gen_sa_score(text):
    sid = SentimentIntensityAnalyzer()
    ss = sid.polarity_scores(text)
    return ss['compound']
  
#to generate a random alphanumeric string of letters and digits
def get_random_string(length):
    # With combination of lower and upper case
    source = string.ascii_letters + string.digits
    result_str = ''.join(random.choice(source) for i in range(length))
    return result_str

#function to clean the text
#https://towardsdatascience.com/using-nlp-to-figure-out-what-people-really-think-e1d10d98e491
def clean_text(text):
    text = text.lower()
    text = re.sub('@', '', text)
    text = re.sub('\[.*?\]', '', text)
    text = re.sub('https?://\S+|www\.\S+', '', text)
    text = re.sub('<.*?>+', '', text)
    text = re.sub('[%s]' % re.escape(string.punctuation), '', text)
    text = re.sub('\n', '', text)
    text = re.sub('\w*\d\w*', '', text)
    #to keep VNese character
    #text = re.sub(r"[^a-zA-Z ]+", "", text)
    return text

#this is to avoid the json serialize due to date and time issue
def myconverter(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()

def make_text_cleaner(text):
    text = text.replace(',', ' ')
    text = text.replace("\n", "")
    text = text.replace("\r", "")
    return text


@app.route("/", methods=['GET'])
def fn_run():
  #getting parameter value
  app_name = request.args.get('app_name')
  #print(str(datetime.datetime.now()) +'-->Fetching '+app_name)
  #getting the review
  googleplay_app_review = reviews_all(
      app_name,       #'com.fecredit.cards',
      sleep_milliseconds=10, # defaults to 0
      lang='en', # defaults to 'en'
      country='us', # defaults to 'us'
      sort=Sort.MOST_RELEVANT, # defaults to Sort.MOST_RELEVANT, other values can be NEWEST, RATING
      #current bug on this as it does not return the consistent number of reviews with MOST_RELEVANT
      #https://githubmemory.com/repo/JoMingyu/google-play-scraper/activity?page=5
      #Press 'show more' in the review list until it can no longer be loaded, and compare it to the return of the reviews method 
      #and you will see the same thing. Since google play doesn't provide full review, it's not a bug in this library.
      # filter_score_with=5 # defaults to None(means all score)
  )
  googleplay_app_review = json.dumps(googleplay_app_review, default = myconverter, ensure_ascii=False)
  
  #now add entiment score and tokenization
  #convert a json_object_string to a dictionary
  googleplay_app_review_dict = json.loads(googleplay_app_review)
  #print(str(datetime.datetime.now()) +'-->No of review '+str(len(googleplay_app_review_dict)))
  for i in googleplay_app_review_dict:
    try:
        review_id = 'GooglePlayReview' + i["reviewId"]
        review_date = i['at']
        review_content = i['content']
        if review_content is not None:
            try:
                review_content = make_text_cleaner(review_content)
            except Exception as e:
                print("Except 4"+str(e))
                pass
        else:
            #go for next round
            review_content=''
        rating = i['score']
        replyContent = i['replyContent']
        if replyContent is not None:
            try:
                replyContent = make_text_cleaner(replyContent)
            except Exception as e:
                print("Except 3"+str(e))
        else:
            #go for next round
            replyContent=""

        repliedAt = i['repliedAt']
        if repliedAt is None:
            repliedAt = " "
        #Steven TEMP starts for add in translated English
        #sentiment_score, translated_review = translate_gen_sa_score(review_content)
        sentiment_score = gen_sa_score(review_content)
        username = i['userName']

        if username is not None:
            try:
                username = make_text_cleaner(username)
            except Exception as e:
                print("Except 5"+str(e))
                pass
        else:
            #go for next round
            username=''
        
        #now for tokenized review file and clean the comment
        #Steven 08JUL2021 starts
        #list_tokenized_words = word_tokenize(clean_text(i['content']))
        list_tokenized_words = word_tokenize(clean_text(review_content))
        #Steven 08JUL2021 ends
        # Remove stopwords, maybe this not apply for vnese, can be commented off
        list_tokenized_words = [w for w in list_tokenized_words if w not in sw]
        
        i['tokenized_words']=list_tokenized_words
        i['sentiment_score']=sentiment_score
        
    except Exception as e:
        print("Except 2"+ str(e) +"---"+i['content']+"---"+review_content)
        pass
        
  
#repack it
  updated_googleplay_app_review = json.dumps(googleplay_app_review_dict, default = myconverter, ensure_ascii=False)
  #print(str(datetime.datetime.now()) +'-->Completed scraping')
  return updated_googleplay_app_review  

if __name__ == "__main__":
  app.run(host='0.0.0.0', threaded=True)