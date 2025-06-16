import requests
import json

'''documentation:
https://www.weatherapi.com/docs/'''


class WeatherApp:
    def __init__(self, api_key, location):
        # self.api_key = "9003d7771bc44eaca0583640230211"
        self.api_key = api_key
        # self.location = "Valea Adanca,Romania"
        self.location = location
        self.current_weather = "http://api.weatherapi.com/v1/current.json"
        self.forecast_weather = "http://api.weatherapi.com/v1/forecast.json"
        self.alerts = "http://api.weatherapi.com/v1/alerts.json"
        self.token = "aqioije5jiex877tdp7fbbvhhd5eeh"
        self.user_key = "unjez5wivue53eb7ekfhyxrcxvavm6"
        self.notif_url = "https://api.pushover.net/1/messages.json"

    def fetch_current_weather(self):
        response = requests.get(f"{self.current_weather}?key={self.api_key}&q={self.location}")
        return response.json()

    def fetch_forecast_weather(self):
        response = requests.get(f"{self.forecast_weather}?key={self.api_key}&q={self.location}&days=3")
        return response.json()

    def get_current_weather(self):
        data = self.fetch_current_weather()
        date = data['location']['localtime']
        temperature = data['current']['temp_c']
        feels_like = data['current']['feelslike_c']
        wind_speed = data['current']['wind_kph']
        message = (
            f"Current date: {date}\n"
            f"Nor location: {self.location}\n"
            f"Current temperature: {temperature}C\n"
            f"Real feel: {feels_like}C\n"
            f"Wind speed: {wind_speed} km/h"
        )
        return message

    def get_forecast_weather(self):
        data = self.fetch_forecast_weather()
        forecast_days = data['forecast']['forecastday']
        forecast_message = "3-day weather forecast:\n"
        for day in forecast_days:
            date = day['date']
            max_temp = day['day']['maxtemp_c']
            min_temp = day['day']['mintemp_c']
            condition = day['day']['condition']['text']
            forecast_message += (
                f"Date: {date}, Max Temp: {max_temp}C, Min Temp: {min_temp}C, Condition: {condition}\n"
            )
        return forecast_message

    def send_notification(self, message):
        message = f"Weather: {message}"
        data = {
            "token": self.token,
            "user": self.user_key,
            "message": message
        }
        requests.post(self.notif_url, data=data,verify=False)

    def get_current_alerts(self):
        data = requests.get(f"{self.alerts}?key={self.api_key}&q={self.location}").json()
        if data['alerts']['alert'] :
            alert_message = "Current weather alerts:\n"
            for alert in data['alerts']:
                alert_message += (
                    f"Title: {alert['headline']}\n"
                    f"Description: {alert['msgType']}\n"
                    f"Severity: {alert['severity']}\n"
                    f"Effective: {alert['effective']}\n"
                    f"Expires: {alert['expires']}\n\n"
                    f"Urgency: {alert['urgency']}\n"
                )
                self.send_notification(alert_message)
        else:
            self.send_notification("No current weather alerts.")

client = WeatherApp(api_key="9003d7771bc44eaca0583640230211", location="Valea Adanca,Romania")
client.get_current_alerts()