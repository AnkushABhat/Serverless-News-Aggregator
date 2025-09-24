import os
import json
import feedparser
import boto3
from datetime import datetime
import uuid

# Initialize DynamoDB client
dynamodb = boto3.client('dynamodb')
# Get the DynamoDB table name from environment variables
TABLE_NAME = os.environ.get('NEWS_TABLE_NAME', 'NewsArticles') 

def lambda_handler(event, context):
    """
    Lambda function to fetch news from RSS feeds and store it in DynamoDB.
    """
    news_sources = {
        "BBC News - Technology": "http://feeds.bbci.co.uk/news/technology/rss.xml",
        "CNN Top Stories": "http://rss.cnn.com/rss/cnn_topstories.rss",
        "The Verge - Tech": "https://www.theverge.com/rss/index.xml",
        # Add more RSS feeds here as needed
    }

    fetched_articles_count = 0
    
    print("Starting news fetch operation...")

    for source_name, rss_url in news_sources.items():
        try:
            feed = feedparser.parse(rss_url)
            print(f"Processing source: {source_name}. Found {len(feed.entries)} articles.")
            
            for entry in feed.entries:
                # Extract relevant data from the RSS entry
                title = entry.title if hasattr(entry, 'title') else "No Title"
                link = entry.link if hasattr(entry, 'link') else "No Link"
                description = entry.summary if hasattr(entry, 'summary') else (entry.description if hasattr(entry, 'description') else "No Description")
                
                # Parse publication date
                pub_date = None
                if hasattr(entry, 'published_parsed'):
                    # Convert time.struct_time to ISO 8601 string
                    pub_date = datetime(*entry.published_parsed[:6]).isoformat() + "Z"
                elif hasattr(entry, 'published'):
                    pub_date = entry.published # Fallback to raw string if parsing fails or not available

                # Generate a unique ID for the article
                article_id = str(uuid.uuid4()) 
                
                # Prepare item for DynamoDB
                item = {
                    'articleId': {'S': article_id}, # Partition Key
                    'title': {'S': title},
                    'link': {'S': link},
                    'source': {'S': source_name},
                    'pubDate': {'S': pub_date if pub_date else 'N/A'},
                    'description': {'S': description}
                }
                
                # Put item into DynamoDB
                # DynamoDB put_item operation is an upsert: if articleId exists, it overwrites.
                # For this simple aggregator, we rely on UUIDs for new articles.
                # A more advanced check would query if a link already exists.
                dynamodb.put_item(
                    TableName=TABLE_NAME,
                    Item=item
                )
                fetched_articles_count += 1
                
        except Exception as e:
            print(f"Error fetching from {source_name} (URL: {rss_url}): {e}")
            # Consider logging this error to CloudWatch or sending a notification

    print(f"News fetch complete. Successfully processed and stored {fetched_articles_count} articles.")
    return {
        'statusCode': 200,
        'body': json.dumps(f'Successfully fetched and stored {fetched_articles_count} articles.')
    }
