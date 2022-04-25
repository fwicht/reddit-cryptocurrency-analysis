#######
# IMPORT PACKAGES
#######

import praw
from praw.models import SubredditHelper, Submission, Comment, MoreComments, ListingGenerator, Redditor
from praw.models.comment_forest import CommentForest
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import cpu_count
import json
import os


def main():
    pool = ProcessPoolExecutor(max_workers=cpu_count())
    user_agent = os.getenv('REDDIT_USER_AGENT')
    client_id = os.getenv('REDDIT_CLIENT_ID')
    client_secret = os.getenv('REDDIT_CLIENT_SECRET')
    reddit = praw.Reddit(user_agent=user_agent,
                         client_id=client_id,
                         client_secret=client_secret)
    subreddits = ["Cryptocurrency", "Bitcoin", "Ethereum", "Askreddit", "btc",
                  "CryptoMarkets", "bitcoinbeginners", "CryptoCurrencies",
                  "altcoin", "icocrypto", "CryptoCurrencyTrading",
                  "Crypto_General", "ico", "Ripple", "litecoin", "Monero",
                  "Stellar", "binance", "Coinbase", "ledgerwallet",
                  "defi"]
    queries = ["Bitcoin", "Ethereum",
               "Cryptocurrency", "Crypto", "Crypto Wallet", "nft"]
    min_score = 10
    data_path = os.path.join("data")

    if not os.path.exists(data_path):
        os.mkdir(data_path)

    for s in subreddits:
        pool.submit(save_subreddit, reddit.subreddit(
            s), os.path.join(data_path, f"{s}.json"), queries, min_score)


def save_subreddit(subreddit: SubredditHelper,  file: str, queries: list, min_score=0):
    schema = {
        "subreddit": subreddit.display_name,
        "queries": queries,
        "type": subreddit.subreddit_type,
        "posts": []
    }
    for q in queries:

        listing: ListingGenerator = subreddit.search(
            q, sort="hot", limit=100)
        for submission in listing:
            if submission.score >= min_score:
                ss = submission_schema(
                    submission=submission, min_score=min_score)
                schema['posts'].append(ss)
    with open(file, 'w') as f:
        print(file)
        json.dump(schema, f, indent=4)


def submission_schema(submission: Submission, min_score=0):
    subreddit: str = submission.subreddit.display_name
    schema = {}
    schema['title'] = submission.title
    schema['url'] = submission.url
    schema['author'] = submission.author.name
    schema['created_utc'] = submission.created_utc
    schema['id'] = submission.id
    schema['score'] = submission.score
    schema['num_comments'] = submission.num_comments
    schema['subreddit'] = subreddit

    schema['comments'] = fetch_comments_schema(
        comments=submission.comments,
        context=[submission.title],
        depth=1,
        min_score=min_score)

    return schema


def fetch_comments_schema(comments: CommentForest, context, depth=1, min_score=0):
    fetched = []
    comment: Comment
    for comment in comments:
        if isinstance(comment, MoreComments):
            continue
        if comment.score >= min_score:
            if comment.author is not None:
                data = {
                    "author": comment.author.name,
                    "score": comment.score,
                    "created_utc": comment.created_utc,
                    "response": comment.body,
                    "depth": depth,
                    "comments": []
                }

                context.append(comment.body)
                data["comments"] = fetch_comments_schema(
                    comments=comment.replies,
                    context=context,
                    depth=depth+1,
                    min_score=min_score)
                context.pop()
                fetched.append(data)
    return fetched


def fetch_author_schema(author: Redditor):
    return {
        "author": author.name,
        "created_utc": author.created_utc,
        "id": author.id,
        "link_karma": author.link_karma,
        "comment_karma": author.comment_karma,
        "is_employee": author.is_employee,
        "has_verified_email": author.has_verified_email
    }


if __name__ == "__main__":
    main()