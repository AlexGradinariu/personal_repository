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


def get_loto_numbers(soup_request):
    year_dict = {'ianuarie': '', 'februarie': '', 'martie': '', 'aprilie': '', 'iulie': '', 'august': '',
                 'septembrie': '', 'octombrie': '', 'noiembrie': '', 'decembrie': ''}
    date_cells = soup_request.find_all('td', class_=['odd','even'], nowrap=True)
    # result = []
    # for item in date_cells:
    #     if 'noiembrie ' in item.text:
    #         sibling = item.find_next_sibling()
    #         while sibling and sibling.get('class') in [['odd_rounded'], ['even_rounded']]:
    #             result.append(sibling.text)
    #             sibling = sibling.find_next_sibling()

def get_loto_numbers(soup):
    year_dict = {'ianuarie': '', 'februarie': '', 'martie': '', 'aprilie': '', 'iulie': '', 'august': '',
                 'septembrie': '', 'octombrie': '', 'noiembrie': '', 'decembrie': ''}
    result = []
    date_cells = soup.find_all('td', class_=['odd','even'], nowrap=True)
    for item in date_cells:
        if 'noiembrie ' in item.text:
            sibling = item.find_next_sibling()
            while sibling and sibling.get('class') in [['odd_rounded'], ['even_rounded']]:
                result.append(sibling.text)
                sibling = sibling.find_next_sibling()

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

def split_into_group_of_no(list_of_no:list):
    batch_size = 6
    return [list_of_no[i:i+batch_size] for i in range(0, len(list_of_no), batch_size)]

def check_missing_numbers(dictionary:dict,*months):
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


if __name__ == '__main__':
    url = 'http://noroc-chior.ro/Loto/6-din-49/arhiva-rezultate.php?Y=2024'
    soup = create_request_session(url)
    lotto_number_dict = get_loto_numbers(soup)
    check_missing_numbers(lotto_number_dict,'ianuarie','februarie')
    # send_notification(get_loto_numbers(soup))
    # while True:
    #     if bool(get_day_of_week()):
    #         soup = create_request_session(url)
    #         send_notification(get_loto_numbers(soup))
    #         print('Notification sent, waiting 50 hours till next check !')
    #         time.sleep(175000)
    #     else:
    #         print('Not there yet,waiting 1 more hour !')
    #         time.sleep(3600)
#
# import numpy as np
# from sklearn.linear_model import LinearRegression
#
#
# # Step 1: Prepare the Data
# def prepare_data(year_dict):
#     # Flatten all batches from all months into a single list
#     all_numbers = []
#     for month_batches in year_dict.values():
#         for batch in month_batches:
#             all_numbers.extend(map(int, batch))  # Convert strings to integers
#
#     # Create sliding window sequences
#     X, y = [], []
#     batch_size = 6
#     for i in range(len(all_numbers) - batch_size * 2 + 1):
#         X.append(all_numbers[i:i + batch_size])  # Input batch
#         y.append(all_numbers[i + batch_size:i + batch_size * 2])  # Output batch
#
#     return np.array(X), np.array(y)
#
#
# # Step 2: Train the Model
# def train_model(X, y):
#     model = LinearRegression()
#     model.fit(X, y)
#     return model
#
#
# # Step 3: Predict the Next Batch
# def predict_next_batch(model, last_batch):
#     last_batch = np.array(last_batch).reshape(1, -1)  # Reshape to match input format
#     return model.predict(last_batch).flatten()
#
#
# # Load the data
# X, y = prepare_data(year_dict)
#
# # Train the model
# model = train_model(X, y)
#
# # Use the last batch of data to predict the next batch
# last_batch = X[-1]  # Take the last batch from the training data
# predicted_next_batch = predict_next_batch(model, last_batch)
#
# # Display Results
# print("Last Batch:", last_batch)
# print("Predicted Next Batch:", predicted_next_batch.round().astype(int))