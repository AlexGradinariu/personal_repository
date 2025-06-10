import requests
import json
api_key = "9003d7771bc44eaca0583640230211"
current_weather = "http://api.weatherapi.com/v1/current.json"
forecast_weather = "http://api.weatherapi.com/v1/forecast.json"
alerts = "http://api.weatherapi.com/v1/alerts.json"
location = "Valea Adanca,Romania"
'''documentation:
https://www.weatherapi.com/docs/'''

request_current = requests.get(f"{current_weather}?key={api_key}&q={location}")
request_forecast = requests.get(f"{forecast_weather}?key={api_key}&q={location}&days=3")

def get_current_weather(data:json):
    current_request = data.json()
    date = (current_request['location']['localtime'])
    temperature = (current_request['current']['temp_c'])
    feels_like = (current_request['current']['feelslike_c'])
    wind_speed = (current_request['current']['wind_kph'])
    message = (
        f"Current date: {date}\n"
        f"Nor location: {location}\n"
        f"Current temperature: {temperature}C\n"
        f"Real feel: {feels_like}C\n"
        f"Wind speed: {wind_speed} km/h"
    )
    return message

def get_forecast_weather(data:json):
    forecast_request = data.json()
    forecast_days = forecast_request['forecast']['forecastday']
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

def get_current_alerts(data:json):
    alerts_request = data.json()
    if 'alert' in alerts_request and alerts_request['alerts']:
        alert_message = "Current weather alerts:\n"
        for alert in alerts_request['alerts']:
            alert_message += (
                f"Title: {alert['headline']}\n"
                f"Description: {alert['msgType']}\n"
                f"Severity: {alert['severity']}\n"
                f"Effective: {alert['effective']}\n"
                f"Expires: {alert['expires']}\n\n"
                f"Urgency: {alert['urgency']}\n"
            )
        send_notification(alert_message)
    else:
        return "No current weather alerts."

def send_notification(message):
    token = "aqioije5jiex877tdp7fbbvhhd5eeh"
    user_key = "unjez5wivue53eb7ekfhyxrcxvavm6"

    url = "https://api.pushover.net/1/messages.json"
    message = f"Loto: {message}"
    data = {
        "token": token,
        "user": user_key,
        "message": message
    }
    requests.post(url, data=data)

if __name__ == "__main__":
    # Call the function to get current weather
    get_current_weather(request_current)
    get_forecast_weather(request_forecast)
    get_current_alerts(request_current)