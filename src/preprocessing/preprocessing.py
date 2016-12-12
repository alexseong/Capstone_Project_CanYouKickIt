import pandas as pd
import numpy as np
import datetime


'''
The functions below clean and perform feature engineering on the Webrobot
datasets which can be found at: http://webrobots.io/kickstarter-datasets/
'''


def read_file(filepath):
    '''
    INPUT: json new line delimited file
    OUTPUT: pandas dataframe
    '''
    with open(filepath, 'rb') as f:
        data = f.readlines()

    # remove the trailing "\n" from each line
    data = map(lambda x: x.rstrip(), data)

    # each element of 'data' is an individual JSON object.
    # convert it into an *array* of JSON objects, which is one large JSON object
    # translation: add square brackets to the beginning and end,
    # and have all the individual business JSON objects separated by a comma

    data_json_str = "[" + ','.join(data) + "]"

    # load it into pandas
    df = pd.read_json(data_json_str)

    return df


def remove_features(df):
    df = df.drop('table_id', axis=1)
    df = df.drop('robot_id', axis = 1)

    return df


def extract_data_features(df):
    '''
    Extract features within the nested json object ['data']
    '''
    df['status'] = df['data'].map(lambda x: x['state'])
    df['project_id'] = df['data'].map(lambda x: x['id'])
    df['creator_id'] = df['data'].map(lambda x: x['creator']['id'])
    df['creator_name'] = df['data'].map(lambda x: x['creator']['name'])
    df['goal'] = df['data'].map(lambda x: x['goal'])
    df['name'] = df['data'].map(lambda x: x['name'])
    df['slug'] = df['data'].map(lambda x: x['slug'])
    df['blurb'] = df['data'].map(lambda x: x['blurb'])
    df['pledged'] = df['data'].map(lambda x: x['pledged'])
    df['subcat_name'] = df['data'].map(lambda x: x['category']['name'])
    df['cat_slug'] = df['data'].map(lambda x: x['category']['slug'])
    df['currency'] = df['data'].map(lambda x: x['currency'])
    df['loc_type'] = df['data'].map(lambda x: x['location']['type'])
    df['short_name'] = df['data'].map(lambda x: x['location']['short_name'])
    df['state'] = df['data'].map(lambda x: x['location']['state'])
    df['country'] = df['data'].map(lambda x: x['location']['country'])
    df['spotlight'] = df['data'].map(lambda x: x['spotlight'])
    df['staff_pick'] = df['data'].map(lambda x: x['staff_pick'])
    df['created_at'] = df['data'].map(lambda x: x['created_at'])
    df['launched_at'] = df['data'].map(lambda x: x['launched_at'])
    df['deadline'] = df['data'].map(lambda x: x['deadline'])
    df['usd_pledged'] = df['data'].map(lambda x: x['usd_pledged'])
    df['backers_count'] = df['data'].map(lambda x: x['backers_count'])
    df['currency_symbol'] = df['data'].map(lambda x: x['currency_symbol'])
    df['static_usd_rate'] = df['data'].map(lambda x: x['static_usd_rate'])
    df['state_changed_at'] = df['data'].map(lambda x: x['state_changed_at'])
    df['disable_communication'] = df['data'].map(lambda x: x['disable_communication'])

    return df


def convert_datetime(feature_list, df):
    for feature in feature_list:
        df[feature] = pd.to_datetime(df[feature], unit='s')
        df[feature] = df[feature].map(lambda x: x.date())

    return df


def get_interval(feature_list, df):
    '''
    Create interval features from existing temporal features
    '''
    convert_datetime(feature_list, df)
    df['days_to_launch'] = (df['launched_at'] - df['created_at']).map(lambda x:x.days)
    df['proj_live_days'] = (df['state_changed_at'] - df['launched_at']).map(lambda x:x.days)

    return df


def get_subscriptn_rate(df):
    '''
    Create subscription rate,the ratio bewteen the amount pledged and project goal
    '''
    df['subscription_rate'] = (df['pledged'] / df['goal']).round(4)
    df['oversubscribed'] = df['subscription_rate'] >=1.

    return df


def get_dayofweek(df):
    '''
    Create feature day of week. Monday=0, Sunday=6
    '''
    df['launched_dow'] = df['launched_at'].map(lambda x:x.weekday())
    df['deadline_dow']= df['deadline'].map(lambda x:x.weekday())

    return df


def cat_name(df):
    '''
    Create feature of high level categories
    '''
    y = df['cat_slug'].str.split('/')
    df['cat_name'] = y.map(lambda x:x[0])

    return df


def dummify_catnames(col_name, df):
    df2 = pd.concat([df, pd.get_dummies(df[col_name], prefix='cat')], axis=1)
    df2 = df2.drop(col_name, axis=1)

    return df2


def get_week_number(df):
    '''
    Create new feature with launch date as a week integer. This is to
    explore if recency of successful campaigns impacts likelihood of success
    '''
    day_zero = pd.to_datetime('2013-01-01').date()
    start = pd.Series(day_zero)

    df['week_num'] = df['launched_at'] - day_zero
    df['week_num'] = df.week_num.map(lambda x:(x.days)/7)

    return df


def get_prev_wk_success(df):
    a = df.groupby('week_num')['outcome'].sum()
    b = pd.DataFrame(a)
    b['week_num'] = b.index
    b.loc[0, 'prevweek'] = b.loc[0, 'week_num']
    for i in range(1, len(b)):
        b.loc[i, 'prevweek_success'] = b.loc[i-1, 'outcome']
    df = df.join(b['prevweek_success'], on='week_num', rsuffix='_prev')
    return df


def get_outcome(df):
    df['outcome'] = df.status == 'successful'
    df = df.drop('status', axis=1)

    return df


def get_metadata_df(df):
    '''
    Returns dataframe with desired features.
    '''
    metadata_columns = ['created_at','status','project_id',
     'creator_id','goal','pledged','spotlight',
     'staff_pick', 'launched_at','deadline','usd_pledged',
     'backers_count','static_usd_rate','state_changed_at','disable_communication',
     'days_to_launch','proj_live_days','subscription_rate','oversubscribed',
     'launched_dow','deadline_dow','cat_art','cat_comics',
     'cat_crafts','cat_dance', 'cat_design','cat_fashion',
     'cat_film & video','cat_food','cat_games',
     'cat_journalism','cat_music','cat_photography','cat_publishing',
     'cat_technology','cat_theater', 'week_num']

    return df[metadata_columns]


def us_only(df):
    '''
    Returns only US-based projects
    '''
    us_df = df[df.country =='US']

    return us_df


# if __name__ == '__main__':
    df = read_file('full_data.json')
    df = remove_features(df)
    df = extract_data_features(df)

    feature_list = ['created_at', 'launched_at', 'state_changed_at', 'deadline']
    convert_datetime(feature_list, df)
    df = get_interval(df)
    df = get_subscriptn_rate(df)
    df = get_dayofweek(df)
    df = cat_name(df)
    df = dummify_catnames(col_name, df)
    df = get_week_number(df)
    df = get_prev_wk_success(df)
    df = get_outcome(df)
    df = us_only(df)
