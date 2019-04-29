import requests as r
import csv
from pprint import pprint

##get forum page
##list posts + timestamp
##get post comments
##get unique authors + timestamp



def get_forum_page(subdomain, page=None):
    if page == None:
        output = r.get('https://{}.zendesk.com/api/v2/community/posts.json'.format(subdomain))
    else:
        output = r.get(page)
    return output.json()


def store_forum_post_ids(subdomain, page):
    posts_with_comments = []
    for post in page['posts']:
        post_infos = { 'id': post['id'],
            'topic_id' : post['topic_id'],
            'title': post['title'],
            'html_url': post['html_url'],
            'created_at' : post['created_at'],
            'vote_count' : post['vote_count'],
            'follower_count' : post['follower_count'],
            'official_comments' : []}
        posts_with_comments.append(get_post_comments(subdomain, post_infos))
    
    return posts_with_comments


def get_post_comments(subdomain, post_infos):
    comments = r.get('https://{}.zendesk.com/api/v2/community/posts/{}/comments.json'.format(subdomain, post_infos['id']))
    comments = comments.json()
    comment_list = comments['comments']

    while comments['next_page'] != None:
        
        comments = r.get(comments['next_page'])
        comments = comments.json()
        comment_list.extend(comments['comments'])
    
    for comment in comment_list:
        if comment['official'] == True:
            official_comment_infos = {'comment_author' : comment['author_id'], 
                'commented_at' : comment['created_at'], 
                'official' : comment['official']
                }

            post_infos['official_comments'].append(official_comment_infos)
    
    return post_infos
        


def csv_writer(data, mode, subdomain):
    report = open("{}_community_comments_4-29.csv".format(subdomain), mode)
    headers = ['title', 'topic_id', 'vote_count','created_at', 'follower_count', 'html_url', 'id', 'commenter', 'commented_at']
    report_writer = csv.DictWriter(report, delimiter=",", fieldnames = headers)
    
    if mode == 'w':
        report_writer.writeheader()

    for row in data:
        pprint(row)
        ('------')
        if not row['official_comments']:
            del row['official_comments']
            row = {**row, 'commenter': None, 'commented_at': None}
            pprint(row)
            report_writer.writerow(row)
        else:
            for official_comment in row['official_comments']:
                comment_row = {**row, 
                    'commenter': official_comment['comment_author'], 
                    'commented_at':official_comment['commented_at']}
                del comment_row['official_comments']
                pprint(comment_row)
                report_writer.writerow(comment_row)
    
    print('page done')
    
    report.close()



if __name__ == "__main__":
    subdomain = input("What is your zendesk subdomain? ")
    page = get_forum_page(subdomain=subdomain)
    mode = 'w' ## opens a new csv file
    while page['page'] < page['page_count']:
        page_posts_with_comments = store_forum_post_ids(subdomain, page)
        csv_writer(page_posts_with_comments, mode, subdomain)
        mode = 'a' ##opens existing csv and appends
        page = get_forum_page(subdomain = subdomain, page=page['next_page'])

