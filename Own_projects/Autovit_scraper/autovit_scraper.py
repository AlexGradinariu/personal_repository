import requests
from bs4 import BeautifulSoup

autovit_site = 'https://www.autovit.ro/autoturisme/volkswagen/passat'
html_text = requests.get(autovit_site)
if html_text.status_code == 200:
    # Step 3: Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(html_text.content, 'html.parser')
    titles = soup.find_all('div', class_='ooa-1qo9a0p efpuxbr6')
    other = soup.find_all('section', class_='ooa-qat6iw efpuxbr1')
    counter = 0
    for title in other:
        counter += 1
        print(title.find('h1').get_text(strip=True))
        print(title.find('h3').get_text(strip=True))

def get_total_pages(soup):
    pagination = soup.find('ul', class_='pagination-list')
    if pagination:
        pages = pagination.find_all('li')
        return int(pages[-2].get_text().strip())  # Get the second last item as it contains the total pages
    return 1

total_pages = get_total_pages(soup)
print(total_pages)