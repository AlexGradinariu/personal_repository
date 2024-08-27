import requests
from bs4 import BeautifulSoup
from collections import Counter
import random
from datetime import datetime
from datetime import date
import time
def create_request_session(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    html_text = requests.get(url, headers=headers)
    if html_text.status_code == 200:
        print(f"Success, responde code : {html_text.status_code}")
        # Step 3: Parse the HTML content using BeautifulSoup
        request_session = BeautifulSoup(html_text.content, 'html.parser')
        return request_session
    else:
        print(f'Error: {html_text.status_code}')
        return 0

def get_loto_numbers(soup):
    no_intregi = soup.find_all('td', class_='even_rounded')
    no_impare = soup.find_all('td', class_='odd_rounded')
    combined_list = no_intregi + no_impare
    final_values = [int(td.text) for td in combined_list]
    counted_values = Counter(final_values)
    # count_15 =counted_values[15]
    # print(count_15)
    most_common = [num for num, count in counted_values.most_common(30)]
    suggested_pick = random.sample(most_common, 6)
    return suggested_pick

def send_notification(message):
    token = "aqioije5jiex877tdp7fbbvhhd5eeh"
    user_key = "unjez5wivue53eb7ekfhyxrcxvavm6"

    url = "https://api.pushover.net/1/messages.json"
    message = f"Sugestie de bilet loto: {message}"
    data = {
        "token": token,
        "user": user_key,
        "message": message
    }
    requests.post(url, data=data)

def get_day_of_week():
    today = date.today().weekday()
    now = int(datetime.now().strftime('%H'))
    if (today == 2 or today == 5) and now >= 18:
        return True
    else:
        return False

if __name__ == '__main__':
    url = 'http://noroc-chior.ro/Loto/6-din-49/arhiva-rezultate.php?Y=2024'
    while True:
        if bool(get_day_of_week()):
            soup = create_request_session(url)
            send_notification(get_loto_numbers(soup))
            print('Notification sent, waiting 50 hours till next check !')
            time.sleep(175000)
        else:
            print('Not there yet,waiting 1 more hour !')
            time.sleep(3600)
