import os
import json
import boto3

# Initialize DynamoDB client
dynamodb = boto3.client('dynamodb')
# Get the DynamoDB table name from environment variables
TABLE_NAME = os.environ.get('NEWS_TABLE_NAME', 'NewsArticles') 

def lambda_handler(event, context):
    """
    Lambda function to retrieve news articles from DynamoDB.
    """
    print("Received API request to fetch news.")
    try:
        # Query DynamoDB for recent articles.
        # For simplicity, we'll use scan, which reads all items and filters.
        # For production, with a large table, you would use query with a GSI
        # (Global Secondary Index) on 'pubDate' to efficiently get latest articles,
        # or implement pagination with 'ExclusiveStartKey'.
        
        response = dynamodb.scan(
            TableName=TABLE_NAME,
            Limit=50 # Retrieve up to 50 articles
            # 'ProjectionExpression': 'articleId, title, link, description, pubDate, source' # To fetch specific attributes
        )
        
        articles = []
        for item in response['Items']:
            # DynamoDB items return as a dictionary with type descriptors (e.g., {'S': 'value'}).
            # Convert them to a flatter dictionary for the API response.
            article = {k: v[list(v.keys())[0]] for k, v in item.items()}
            articles.append(article)
            
        # Optional: Sort articles by publication date (descending) in the Lambda.
        # This is good practice if your DynamoDB query cannot guarantee order.
        articles.sort(key=lambda x: x.get('pubDate', ''), reverse=True)

        print(f"Retrieved {len(articles)} articles.")

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*' # Crucial for CORS if accessed from a web browser
            },
            'body': json.dumps(articles)
        }
    except Exception as e:
        print(f"Error retrieving news: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Failed to retrieve news articles', 'details': str(e)})
        }
