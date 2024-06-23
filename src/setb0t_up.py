#!/usr/bin/env python3

from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from telegram.constants import ParseMode
import requests


async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Hello! Send me a research topic using /search <topic>, and I will fetch CrossRef results for you.')


def search_crossref(query):
    queries = query.split()
    or_queries = [q for q in queries if q.lower() == 'or']
    and_queries = [q for q in queries if q.lower() == 'and']

    
    if or_queries:
        or_index = queries.index('or')
        query1 = ' '.join(queries[:or_index])
        query2 = ' '.join(queries[or_index + 1:])
        url1 = f"https://api.crossref.org/works?query={query1}&rows=5"
        url2 = f"https://api.crossref.org/works?query={query2}&rows=5"
        response1 = requests.get(url1).json().get('message', {}).get('items', [])
        response2 = requests.get(url2).json().get('message', {}).get('items', [])
        results = format_results(response1) + "\n\nOR\n\n" + format_results(response2)
 
    elif and_queries:
        and_index = queries.index('and')
        query1 = ' '.join(queries[:and_index])
        query2 = ' '.join(queries[and_index + 1:])
        url1 = f"https://api.crossref.org/works?query={query1}&rows=5"
        url2 = f"https://api.crossref.org/works?query={query2}&rows=5"
        response1 = requests.get(url1).json().get('message', {}).get('items', [])
        response2 = requests.get(url2).json().get('message', {}).get('items', [])
      
        results = intersect_results(response1, response2)
 
    else:
        url = f"https://api.crossref.org/works?query={query}&rows=5"
        response = requests.get(url).json().get('message', {}).get('items', [])
        results = format_results(response)

    return results


def format_results(items):
    results = "CrossRef Results:\n"
    for item in items:
        if 'title' in item and 'author' in item and 'URL' in item:
            if 'journal-article' in item['type'] or 'proceedings-article' in item['type']:
                title = item['title'][0]
                authors = ', '.join(author['given'] + ' ' + author['family'] for author in item['author'])
                url = item['URL']
                results += f"*{title}* - {authors}\n[Read more]({url})\n\n"
        if len(results) > 2000:  
            break
    return results.strip()


def intersect_results(response1, response2):
    results1 = {item['DOI'] for item in response1 if 'DOI' in item}
    results2 = {item['DOI'] for item in response2 if 'DOI' in item}
    common_dois = results1.intersection(results2)
    
    results = "CrossRef Results (AND):\n"
    for doi in common_dois:
        item1 = next((item for item in response1 if item.get('DOI') == doi), None)
        item2 = next((item for item in response2 if item.get('DOI') == doi), None)
        if item1 and item2:
            title = item1['title'][0]
            authors = ', '.join(author['given'] + ' ' + author['family'] for author in item1['author'])
            url = item1['URL']
            results += f"*{title}* - {authors}\n[Read more]({url})\n\n"
    
    return results.strip()


async def search(update: Update, context: CallbackContext) -> None:
    query = ' '.join(context.args)
    if query:
        crossref_results = search_crossref(query)
        response = crossref_results
        await update.message.reply_text(response if response else "No results found.", parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text("Please provide a search query using /search <topic>.")

def main() -> None:
    
    application = Application.builder().token("USE THE TELEGRAM API HERE").build()

   
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("search", search))

    application.run_polling()

if __name__ == '__main__':
    main()
