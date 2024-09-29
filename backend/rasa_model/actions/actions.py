# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import requests
import os
from dotenv import load_dotenv
import time
from datetime import datetime, timedelta
import logging
import requests.exceptions

# Load environment variables
load_dotenv()

OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

class RateLimiter:
    def __init__(self, max_calls, time_frame):
        self.max_calls = max_calls
        self.time_frame = time_frame
        self.calls = []

    def __call__(self, f):
        def wrapped(*args, **kwargs):
            now = time.time()
            self.calls = [c for c in self.calls if c > now - self.time_frame]
            if len(self.calls) >= self.max_calls:
                raise Exception("Rate limit exceeded")
            self.calls.append(now)
            return f(*args, **kwargs)
        return wrapped

# Define the rate limiters
weather_limiter = RateLimiter(max_calls=60, time_frame=3600)  # 60 calls per hour
news_limiter = RateLimiter(max_calls=100, time_frame=86400)  # 100 calls per day

class SimpleCache:
    def __init__(self, expire_after=timedelta(hours=1)):
        self.cache = {}
        self.expire_after = expire_after

    def get(self, key):
        if key in self.cache:
            value, timestamp = self.cache[key]
            if datetime.now() - timestamp < self.expire_after:
                return value
        return None

    def set(self, key, value):
        self.cache[key] = (value, datetime.now())

weather_cache = SimpleCache()
news_cache = SimpleCache(expire_after=timedelta(minutes=30))

@weather_limiter
def get_weather(city):
    cached_data = weather_cache.get(city)
    if cached_data:
        return cached_data

    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHERMAP_API_KEY}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        weather_data = {
            'description': data['weather'][0]['description'],
            'temperature': data['main']['temp']
        }
        weather_cache.set(city, weather_data)
        return weather_data
    else:
        raise Exception(f"Error fetching weather data: {response.status_code}")

@news_limiter
def get_news(topic):
    cached_data = news_cache.get(topic)
    if cached_data:
        return cached_data

    url = f"https://newsapi.org/v2/everything?q={topic}&apiKey={NEWS_API_KEY}&language=en&pageSize=3"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        news_data = [{'title': article['title']} for article in data['articles'][:3]]
        news_cache.set(topic, news_data)
        return news_data
    else:
        raise Exception(f"Error fetching news data: {response.status_code}")

class ActionGetWeather(Action):
    def name(self) -> Text:
        return "action_get_weather"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        city = tracker.get_slot("city")
        if not city:
            dispatcher.utter_message(text="I'm sorry, I couldn't determine the city. Can you please specify?")
            return []

        try:
            weather_data = get_weather(city)
            response = f"The current weather in {city} is {weather_data['description']} with a temperature of {weather_data['temperature']}°C."
            dispatcher.utter_message(text=response)
        except Exception as e:
            dispatcher.utter_message(text=f"I'm sorry, I couldn't fetch the weather information. Error: {str(e)}")

        return []

class ActionGetNews(Action):
    def name(self) -> Text:
        return "action_get_news"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        topic = tracker.get_slot("topic")
        if not topic:
            dispatcher.utter_message(text="I'm sorry, I couldn't determine the news topic. Can you please specify?")
            return []

        try:
            news_data = get_news(topic)
            response = f"Here are the latest news headlines for {topic}:\n\n"
            for article in news_data:
                response += f"- {article['title']}\n"
            dispatcher.utter_message(text=response)
        except Exception as e:
            dispatcher.utter_message(text=f"I'm sorry, I couldn't fetch the news. Error: {str(e)}")

        return []