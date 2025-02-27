import requests
from bs4 import BeautifulSoup
import locale
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
    year_dict = {'ianuarie': '', 'februarie': '', 'martie': '', 'aprilie': '', 'iulie': '', 'august': '',
                 'septembrie': '', 'octombrie': '', 'noiembrie': '', 'decembrie': ''}
    date_cells = soup.find_all('td', class_=['odd','even'], nowrap=True)
    year_dict = {key: [] for key in year_dict.keys()}
    for item in date_cells:
        for key in year_dict.keys():
            if key in item.text:
                sibling = item.find_next_sibling()
                while sibling and sibling.get('class') in [['odd_rounded'], ['even_rounded']]:
                    year_dict[key].append(sibling.text)
                    sibling = sibling.find_next_sibling()
    for month in year_dict.keys():
        year_dict[month] = split_into_group_of_no(year_dict[month])
    return year_dict

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

def get_day_of_week():
    today = date.today().weekday()
    now = int(datetime.now().strftime('%H'))
    if (today == 2 or today == 5) and now >= 18:
        return True
    else:
        return False

def split_into_group_of_no(list_of_no:list):
    batch_size = 6
    return [list_of_no[i:i+batch_size] for i in range(0, len(list_of_no), batch_size)]

def check_missing_numbers(dictionary:dict,months):
    all_numbers = [x for x in range(1, 50)]
    missing_numbers = set()
    extracted_numbers = []
    for month in months:
        flattened_list = [int(num) for batch in dictionary[month] for num in batch]
        extracted_numbers.extend(flattened_list)
    for element_to_find in all_numbers:
        if element_to_find not in extracted_numbers:
            missing_numbers.add(element_to_find)
    print(f'In months {[x for x in months]},following numbers were NOT extracted: {[y for y in missing_numbers]}')
    return missing_numbers

def check_most_common_numbers(lotto_number_dict):
    all_values = []
    for value in lotto_number_dict.values():
        for sublist in value:
            if isinstance(sublist,list):
                all_values.extend(sublist)
            else:
                print("Unexpected Data Format:", sublist)
    all_values = [int(item) for item in all_values]
    counter = Counter(all_values)
    print(f"Most common used numbers: {counter.most_common(6)}")
    print(f"Least common used numbers: {counter.most_common()[:-6:-1]}")
    return counter.most_common(6),counter.most_common()[:-6:-1]

def current_month():
    locale.setlocale(locale.LC_TIME, "ro_RO.UTF-8")
    current_month = datetime.now().month
    current_year = datetime.now().year
    previous_month = current_month - 1 if current_month > 1 else 12
    current_month_name = datetime.now().strftime("%B")
    previous_month_name = datetime(current_year, previous_month, 1).strftime("%B")
    return [previous_month_name,current_month_name]

if __name__ == '__main__':
    url = 'http://noroc-chior.ro/Loto/6-din-49/arhiva-rezultate.php?Y=2025'
    soup = create_request_session(url)
    lotto_number_dict = get_loto_numbers(soup)
    months = current_month()
    missing_numbers = check_missing_numbers(lotto_number_dict,current_month())
    most_common,less_common = check_most_common_numbers(lotto_number_dict)
    message = (f"In months {list(months)}, following numbers were NOT extracted: {list(missing_numbers)}\n"
           f"Most common used numbers: {most_common}\n"
           f"Least common used numbers: {less_common}")
    send_notification(message)
    '''Cele mai extrase, nu se mai pun ,ex 23 nu se pune '''
    # while True:
    #     if bool(get_day_of_week()):
    #         soup = create_request_session(url)
    #         send_notification(get_loto_numbers(soup))
    #         print('Notification sent, waiting 50 hours till next check !')
    #         time.sleep(175000)
    #     else:
    #         print('Not there yet,waiting 1 more hour !')
    #         time.sleep(3600)