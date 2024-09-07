import requests
from bs4 import BeautifulSoup
from datetime import datetime
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate

headers = {
    'authority': 'www.amazon.com',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'accept-language': 'en-US,en;q=0.9,bn;q=0.8',
    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="102", "Google Chrome";v="102"',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'
}

def reviewsHtml(product_url, len_page):
    soups = []
    for page_no in range(1, len_page + 1):
        params = {
            'ie': 'UTF8',
            'reviewerType': 'all_reviews',
            'filterByStar': 'critical',
            'pageNumber': page_no,
        }
        response = requests.get(product_url, headers=headers, params=params)
        soup = BeautifulSoup(response.text, "html.parser")
        soups.append(soup)
    return soups

def get_product_details(product_url):
    response = requests.get(product_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    try:
        title = soup.find('span', {'id': 'productTitle'}).get_text(strip=True)
    except Exception:
        title = 'N/A'

    try:
        description_div = soup.select_one('div#productDescription')
        if description_div:
            description_p = description_div.find('p')
            description = description_p.get_text(strip=True) if description_p else description_div.get_text(strip=True)
        else:
            description = 'N/A'
    except Exception:
        description = 'N/A'

    return title, description

def getReviews(html_data):
    data_dicts = []
    boxes = html_data.select('div[data-hook="review"]')
    for box in boxes:
        try:
            name = box.select_one('[class="a-profile-name"]').text.strip()
        except Exception:
            name = 'N/A'

        try:
            stars = box.select_one('[data-hook="review-star-rating"]').text.strip().split(' out')[0]
        except Exception:
            stars = 'N/A'

        try:
            title = box.select_one('[data-hook="review-title"]').text.strip()
        except Exception:
            title = 'N/A'

        try:
            datetime_str = box.select_one('[data-hook="review-date"]').text.strip().split(' on ')[-1]
            date = datetime.strptime(datetime_str, '%B %d, %Y').strftime("%d/%m/%Y")
        except Exception:
            date = 'N/A'

        try:
            description = box.select_one('[data-hook="review-body"]').text.strip()
            # Remove 'Read more' or similar text at the end of the description
            if 'Read more' in description:
                description = description.split('Read more')[0].strip()
        except Exception:
            description = 'N/A'

        data_dict = {
            'Name': name,
            'Stars': stars,
            'Title': title,
            'Description': description
        }
        data_dicts.append(data_dict)

    return data_dicts

def summarize_descriptions_with_llama2(descriptions):
    # Initialize the Llama2 model through LangChain and Ollama
    llm = Ollama()  # Initialize without specifying model_name

    # Prepare a prompt template
    template = """Summarize the following product reviews:
    {descriptions}"""

    prompt = PromptTemplate(
        input_variables=["descriptions"],
        template=template,
    )

    # Combine prompt and LLM
    combined_descriptions = " ".join(descriptions)
    prompt_text = prompt.format(descriptions=combined_descriptions)

    # Generate the summary using the LLM
    summary = llm.invoke(prompt_text)  # Use invoke instead of call

    return summary

def scrape_and_summarize_amazon_info():
    product_url = input("Enter the Amazon product URL: ")
    len_page = int(input("Enter the number of pages to scrape: "))

    product_title, product_description = get_product_details(product_url)

    print("\nProduct Title:")
    print(product_title)
    print("\nProduct Description:")
    print(product_description)

    html_datas = reviewsHtml(product_url, len_page)
    all_reviews = []
    descriptions = []

    for html_data in html_datas:
        reviews = getReviews(html_data)
        all_reviews.extend(reviews)
        descriptions.extend([review['Description'] for review in reviews])

    # Combine and summarize the descriptions using Llama2
    if descriptions:
        summary = summarize_descriptions_with_llama2(descriptions)
        print("\nSummary of Descriptions:")
        print(summary)

    # Print top reviews
    print("\nTop Reviews:")
    for i, review in enumerate(all_reviews[:5], 1):  # Print top 5 reviews
        print(f"\nReview {i}:")
        print(f"Name: {review['Name']}")
        print(f"Stars: {review['Stars']}")
        print(f"Title: {review['Title']}")
        print(f"Description: {review['Description']}")

scrape_and_summarize_amazon_info()
