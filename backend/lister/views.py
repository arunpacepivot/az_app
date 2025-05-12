from django.shortcuts import render
from rest_framework import viewsets
from .models import Product
from .serializers import ProductSerializer
# from bs4 import BeautifulSoup
import cohere
import os
import re
from rest_framework.decorators import api_view
from rest_framework.response import Response
from groq import Groq
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
# from playwright.async_api import async_playwright
import requests
import asyncio
from asgiref.sync import async_to_sync, sync_to_async
from django.middleware.csrf import get_token
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
from .api import get_text

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

@ensure_csrf_cookie
@require_http_methods(['GET', 'OPTIONS'])
def get_csrf(request):
    if request.method == "OPTIONS":
        response = JsonResponse({})
    else:
        response = JsonResponse({'csrfToken': get_token(request)})
    
    response["Access-Control-Allow-Origin"] = request.headers.get('Origin')
    response["Access-Control-Allow-Credentials"] = "true"
    response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response["Access-Control-Allow-Headers"] = "Content-Type, X-CSRFToken"
    return response

# Use environment variables for sensitive information
os.environ['GROQ_API_KEY'] = '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'
co = cohere.Client(api_key="ZP693YY1ZD6DSZYMbRTSbixvokPVfR9YLuOeHLwd")

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

def get_country_code(geography):
    country_mapping = {
        "India": "in",
        "United States": "com",
        "United Kingdom": "co.uk",
        "Germany": "de",
        "France": "fr",
        "Italy": "it",
        "Spain": "es",
        "Japan": "co.jp",
        "Canada": "ca",
        "Australia": "com.au"
    }
    return country_mapping.get(geography, "com")

def construct_urls(asin_list, country):
    base_url = f"https://www.amazon.{country}/dp/"
    return [base_url + asin for asin in asin_list]

async def fetch_html(url: str) -> str:
    # headers = {
    #     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    # }
    # async with async_playwright() as p:
    #     browser = await p.chromium.launch(headless=True)
    #     page = await browser.new_page()
    #     await page.set_extra_http_headers(headers)
    #     await page.goto(url)
    #     content = await page.content()
    #     await browser.close()
    #     return content
    # response = requests.get(url, headers=headers)
    text = get_text(url)
    return text

# async def parse_html(url: str) -> str:
#     html = await fetch_html(url)
#     soup = BeautifulSoup(html, "html.parser")
#     return soup.get_text(separator=" ", strip=True)

def summarize_text(text):
    try:
        response = co.chat(
            message=(
                f"""You are an e-commerce expert adept at crafting optimized product descriptions and USPs for e-commerce pages. 
                You will receive parsed text from a product's HTML page. Your task is to summarize the information in a structured format 
                that begins with the brand name, followed by the product name, and then summarizes the Unique Selling Proposition (USP). 
                The USP should include:
                1. Uniqueness: The product or service's unique feature or benefit.
                2. Selling power: The USP's ability to convince customers to buy the product or service.
                3. Proposition: The promise the business makes to its customers, which is fulfilled through the product or service.
                The USP must be less than 300 characters in length. You will only provide the structured output with no additional text before or after the required information.
                Ensure the output appears natural and human-like.
                The output should follow this format:
                Brand Name: [Brand Name]
                Product Name: [Product Name]
                USP:
                1. Uniqueness: [Unique Feature or Benefit]
                2. Selling Power: [Ability to Convince Customers]
                3. Proposition: [Business Promise]
                You will get the {text} and you will take the persona described to complete the task."""
            ),
            model="command-r-plus",
        )
        return response.text
    except Exception as e:
        print(f"Error summarizing text: {e}")
        return None

def groq_output(text, task):
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": f"You are a helpful assistant adept at building copies for ecommerce pages optimized for keywords. You will get the {task} and you will take the persona described to complete the task."},
                {"role": "user", "content": text}
            ],
            # model="llama3-70b-8192",
            model="llama-3.3-70b-versatile"
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error summarizing text: {e}")
        return None

def clean_bullet_points(bullet_points_text):
    if not bullet_points_text:
        return []
    bullet_point_pattern = re.compile(r'^[^\w\s]', re.MULTILINE)
    lines = bullet_points_text.split('\n')
    return '\n'.join(line.strip() for line in lines if bullet_point_pattern.match(line.strip()))


@csrf_exempt
@api_view(['POST', 'OPTIONS']) #added api_view
@require_http_methods(['POST', 'OPTIONS'])
def process_asins(request):
    if request.method == "OPTIONS":
        response = JsonResponse({})
        response["Access-Control-Allow-Origin"] = request.headers.get('Origin')
        response["Access-Control-Allow-Credentials"] = "true"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, X-CSRFToken"
        return response
        
    async def process_asin(asin, url):
        asin_input = request.data.get('asins', '')
        geography = request.data.get('geography', 'United States')
        # email = request.data.get('email', '')
        if isinstance(asin_input, str):
            asin_list = [asin.strip() for asin in asin_input.split(',') if asin.strip()]
        else:
            asin_list = asin_input 
        
        country = get_country_code(geography)
        urls = construct_urls(asin_list, country)

        data = []

        title_prompt = """please write Amazon Product Title for the product summary of whose USP is given.When writing product Titles, pretend like you are the highest paid e-commerce copywriter on planet Earth. NOBODY writes more compelling, sexy, hypnotic product Titles than you. You are the best of the best, the cream of the crop.
                    The purpose of product Titles is to convince Amazon shoppers to click on the product. The Product Titles should be so hypnotic and compelling that shoppers IMMEDIATELY click to purchase because they desire the product so much. Product Titles should be slick, catchy, creative, sexy and CONVINCE me to click based on the data from your Amazon review analysis.

                    Each Product title should be between 180 characters - 200 characters.Each product title should be LONGER than 180 characters.Each product title should be LESS THAN 250 characters.

                    From the USP provided, identify the brand name and product

                    You need to build the product title in 2 parts. 1) The title should always start with brand name followed by describing product in exactly 5 or 6 words. first part should not use more than 40-60 characters and should always be followed by , 2) combine key phrases together with propositions so that they bring out USP of the product and make sense on reading for customers . Join these 2 parts sequentially to output the product title which is larger than 185 character and less than 200 character. Only use "-" or "," or "|" as separators. Do not use any other special character. MAKE SURE THEY SOUND NATURAL AND PROFESSIONAL! Don't just randomly stuff keywords into the Product Titles.

                    Titles should avoid using the same word more than twice. Prepositions, articles, and conjunctions are exceptions. Use the keywords naturally within the title, prioritizing them at the beginning of the title.

                    Use Title Case: Capitalize the first letter of each significant word while keeping conjunctions and prepositions in lowercase. This enhances readability

                    Also comply with product category specific title requirements outlined in Amazon's style guide.

                    Include key product details such as the product type, main features, size, color, and quantity. This information should be relevant to what customers are searching for. Consider what potential customers are looking for when they search. The title should answer their queries and provide valuable information that encourages them to click.

                    Avoid Fluff and Promotional Language: Exclude subjective phrases like "Best Seller" or promotional offers such as "Free Shipping." These do not add value to the title and can make it less credible

                    DO NOT add any text before or after the output. Only give out product Titles as output.
                    
                    Ready? Set? Go! Write me the most compelling Amazon Product Titles the world has ever seen!"""
        Bullet_prompt = """please write 7 Amazon bullet points for the product  that is described earlier in the context.

                    2. When writing bullet points, pretend like you are the highest paid e-commerce copywriter on planet Earth. NOBODY writes more compelling, sexy, hypnotic bullet points than you. You are the best of the best, the cream of the crop. 2. The purpose of bullet points is to convince Amazon shoppers to buy my product over every other option.

                    The bullet points should be so hypnotic and compelling that shoppers IMMEDIATELY pull out their credit cards to purchase because they desire the product so much.

                    Bullet points should be slick, catchy, creative, sexy and CONVINCE me to buy based on the data from the Amazon review analysis.

                    Bullet points should emphasize the benefits of the product.

                    Use action words like protect, enhance, improve, etc to make the bullet points more compelling and appeal to buyers. Incorporate words that evoke emotions or imagery, helping customers visualize the benefits of the product in their lives.

                    Make every word count by being clear and direct. Avoid unnecessary jargon or overly complex sentences.

                    Use bullet points to highlight the benefits of the product. Focus on how the product solves customer problems or meets their needs, rather than just listing features.

                    Do not include pricing, promotional offers, or marketing jargon. The content should be factual and straightforward.

                    Tailor bullet points to resonate with the target buyer persona. Speak directly to their desires and needs, confirming that the product is the right choice for them.

                    Bullet points should clearly list the 7 most important features or benefits of the product. This should include unique selling propositions (USPs) that differentiate the product from competitors.

                    Mention specifics like quantity, sizing, colors, and materials to provide comprehensive information to the customers.

                    3. Format should be:

                    BENEFIT IN ALL CAPS - Features to back up benefits.

                    4. Each bullet point should be between 180 characters - 250 characters.

                    Each bullet point should be LONGER than 180 characters.

                    Each bullet point should be LESS THAN 250 characters.

                    5. Each bullet point should start with a single emoticon relevant to the benefit.

                    6. DO NOT add any text before or after the output. Only give out product bullet points as output. DO NOT add "Here are the 5 Amazon bullet points:" before the bullet point output

                    As far as possible, ensure all bullet points are of similar length to maintain a clean appearance.

                    Where it makes sense, include top-searched, highly relevant keywords throughout the bullet points. The key phrases should appear in first 100 characters of the bullet point. MAKE SURE THEY SOUND NATURAL AND PROFESSIONAL! Dont just randomly stuff keywords into the bullet points. Ready? Set? Go! Write me the 7 most compelling Amazon bullet points the world has ever seen! """
        Description_prompt = """Based on the USP summary provided , please write a KILLER Amazon product description that describes the product  product WHILE convincing shoppers to buy my product over every other option.

                            1. The product description should be between 1,900 characters and 2,000 characters.

                            The Amazon product description should NOT be less than 1,900 characters in total length.

                            The Amazon product description should NOT be more than 2,000 characters in total length. 

                            Aim for a concise yet informative description that captures key details without overwhelming the reader.

                            Avoid including promotional messages, testimonials, external links, or references to competitors. Focus solely on the product itself.

                            Use straightforward language to describe the product. Avoid jargon and complex sentences to ensure clarity

                            Clearly articulate what makes the product unique. Highlight features that differentiate it from competitors

                            Instead of merely listing features, explain how the product solves problems or improves the customer's life. This approach helps create an emotional connection with potential buyers

                            Place the most important details at the beginning of your description to capture attention quickly

                            Understand who your customers are and what they are looking for. Write in a tone and style that resonates with them, addressing their needs and preferences directly

                            Keep the tone informative rather than salesy; focus on providing value through clear information about the product



                            2. Please repeat  top-searched, relevant keywords multiple times throughout the description to help me rank this Amazon listing organically on Google:
                            Make sure to use story telling in the description to show how the product solves the problem. Use storytelling techniques where appropriate to engage readers. Describe scenarios where the product would be beneficial, helping customers envision its use in their lives

                            3. The product description should SIZZLE! Sounds catchy, fun, and sexy NOT dull or boring or corporate."""

        html = await fetch_html(url)
        if html:
            # parsed_text = await parse_html(url)
            summary = summarize_text(html)

            if summary:
                product_title = groq_output(summary, title_prompt)
                def clean_product_title(title: str) -> str:
                    
                    if ":" in title:
                        return title.split(":", 1)[1].strip()
                    return title.strip()

                product_title = clean_product_title(product_title)
                bullet_points_response = groq_output(summary, Bullet_prompt)
                cleaned_bullet_points = clean_bullet_points(bullet_points_response)
                bullet_points = [bp.strip() for bp in cleaned_bullet_points.split('\n') if bp.strip()]
                bullet_points.extend([''] * (7 - len(bullet_points)))  # Ensure there are always 7 bullet points
                product_description = groq_output(summary, Description_prompt)
                def clean_product_description(description: str) -> str:
                    if ":" in description:
                        return description.split(":", 1)[1].strip()
                    return description.strip()

                product_description = clean_product_description(product_description)

                await sync_to_async(Product.objects.create)(
                    asin=asin,
                    geography=geography,
                    # email=email,
                    title=product_title,
                    bullet_point_1=bullet_points[0] if bullet_points[0] else 'No bullet point available',
                    bullet_point_2=bullet_points[1] if bullet_points[1] else 'No bullet point available',
                    bullet_point_3=bullet_points[2] if bullet_points[2] else 'No bullet point available',
                    bullet_point_4=bullet_points[3] if bullet_points[3] else 'No bullet point available',
                    bullet_point_5=bullet_points[4] if bullet_points[4] else 'No bullet point available',
                    description=product_description,
                )

                return {
                    'ASIN': asin,
                    'Product Title': product_title,
                    'Bullet Point 1': bullet_points[0] if bullet_points[0] else 'No bullet point available',
                    'Bullet Point 2': bullet_points[1] if bullet_points[1] else 'No bullet point available',
                    'Bullet Point 3': bullet_points[2] if bullet_points[2] else 'No bullet point available',
                    'Bullet Point 4': bullet_points[3] if bullet_points[3] else 'No bullet point available',
                    'Bullet Point 5': bullet_points[4] if bullet_points[4] else 'No bullet point available',
                    'Product Description': product_description,
                }
            return None

    async def process_asins_async():
        asin_input = request.data.get('asins', '')
        geography = request.data.get('geography', 'United States')
        email = request.data.get('email', '')
        asin_list = [asin.strip() for asin in asin_input.split(',')] if isinstance(asin_input, str) else asin_input
        
        country = get_country_code(geography)
        urls = construct_urls(asin_list, country)

        tasks = [process_asin(asin, url) for asin, url in zip(asin_list, urls)]
        return await asyncio.gather(*tasks)

    data = async_to_sync(process_asins_async)()
    return Response(data)
